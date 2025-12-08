from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, current_user
from flask_mail import Message
from flask import current_app as app
from app import db, mail, bcrypt
from app.models import User, Role, UserPreference, UserActivity
from app.forms import RegistrationForm, LoginForm, EstimateRequestForm, ResendVerificationForm
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.context_processor
def combined_context_processor():
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form)


# ============================================================================
# Phase 22: Enhanced Registration with Email Verification & Onboarding
# ============================================================================

@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main_routes.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        if not form.accept_tos.data:
            flash('You must agree to the Terms and Conditions to register.', 'warning')
            return render_template('register.html', title='Register', form=form)

        # Check for existing user
        if user_exists(form.email.data.lower(), form.username.data):
            return render_template('register.html', title='Register', form=form)

        # Create new user
        new_user = create_new_user(form)
        db.session.add(new_user)
        db.session.commit()
        
        # Create default preferences
        prefs = UserPreference(user_id=new_user.id)
        db.session.add(prefs)
        
        # Log activity
        new_user.log_activity(
            activity_type='account_created',
            title='Account created',
            description='Registered via email/password',
            icon='fa-user-plus'
        )
        db.session.commit()
        
        # Send verification email (optional, can be enabled via config)
        if app.config.get('REQUIRE_EMAIL_VERIFICATION'):
            send_verification_email(new_user)
            flash('Account created! Please check your email to verify your account.', 'info')
        else:
            new_user.email_verified = True
            db.session.commit()
        
        login_user(new_user)
        
        # Redirect to onboarding wizard
        return redirect(url_for('onboarding.welcome'))

    return render_template('register.html', title='Register', form=form)


def user_exists(email, username):
    """Check if a user with the given email or username already exists."""
    email = email.lower()
    if User.query.filter_by(email=email).first():
        flash('An account with this email already exists.', 'warning')
        return True
    if User.query.filter_by(username=username).first():
        flash('This username is already taken. Please choose a different one.', 'warning')
        return True
    return False


def create_new_user(form):
    """Create a new user instance from the registration form."""
    new_user = User(
        username=form.username.data, 
        email=form.email.data.lower(), 
        password=form.password.data
    )
    new_user.first_name = form.first_name.data
    new_user.last_name = form.last_name.data
    new_user.tos_accepted = True
    role = Role.query.get(form.role.data)
    if role:
        new_user.roles.append(role)
    return new_user


def send_verification_email(user):
    """Send email verification link."""
    token = user.generate_email_verification_token()
    db.session.commit()
    
    msg = Message(
        "Verify your email address",
        sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
        recipients=[user.email]
    )
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    msg.html = f"""
    <h2>Welcome to {app.config.get('SITE_NAME', 'Our Platform')}!</h2>
    <p>Please verify your email address by clicking the button below:</p>
    <p><a href="{verify_url}" style="background: #007bff; color: white; padding: 12px 24px; 
       text-decoration: none; border-radius: 6px; display: inline-block;">Verify Email</a></p>
    <p>Or copy this link: {verify_url}</p>
    <p>This link will expire in 24 hours.</p>
    """
    try:
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Failed to send verification email: {e}")


# Phase 22: Email Verification Routes
@auth.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address via token."""
    user = User.verify_email_token(token)
    if not user:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('auth.login'))
    
    if user.email_verified:
        flash('Email already verified.', 'info')
    else:
        user.email_verified = True
        user.email_verification_token = None
        user.calculate_profile_completion_score()
        
        # Log activity
        user.log_activity(
            activity_type='email_verified',
            title='Email verified',
            description='Email address confirmed',
            icon='fa-check-circle'
        )
        db.session.commit()
        flash('Email verified successfully!', 'success')
    
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))


@auth.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Resend email verification link."""
    form = ResendVerificationForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and not user.email_verified:
            # Rate limit: only allow resend once per 5 minutes
            if user.email_verification_sent_at:
                time_diff = datetime.utcnow() - user.email_verification_sent_at
                if time_diff.total_seconds() < 300:  # 5 minutes
                    remaining = int(300 - time_diff.total_seconds())
                    flash(f'Please wait {remaining} seconds before requesting another email.', 'warning')
                    return render_template('resend_verification.html', form=form)
            
            send_verification_email(user)
            flash('Verification email sent! Please check your inbox.', 'success')
        else:
            # Don't reveal if email exists
            flash('If an account exists with this email, a verification link has been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('resend_verification.html', form=form)


# Phase 22: AJAX Duplicate Detection Endpoints
@auth.route('/check-email', methods=['POST'])
def check_email():
    """AJAX endpoint for real-time email duplicate check."""
    email = request.json.get('email', '').lower().strip()
    if not email:
        return jsonify({'available': False, 'message': 'Email is required'})
    
    exists = User.query.filter_by(email=email).first() is not None
    return jsonify({
        'available': not exists,
        'message': 'Email is already registered' if exists else 'Email is available'
    })


@auth.route('/check-username', methods=['POST'])
def check_username():
    """AJAX endpoint for real-time username duplicate check."""
    username = request.json.get('username', '').strip()
    if not username or len(username) < 3:
        return jsonify({'available': False, 'message': 'Username must be at least 3 characters'})
    
    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({
        'available': not exists,
        'message': 'Username is already taken' if exists else 'Username is available'
    })


# Standard Login/Logout Routes
@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_routes.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            user.last_activity_at = datetime.utcnow()
            
            # Log activity
            user.log_activity(
                activity_type='login',
                title='Logged in',
                icon='fa-sign-in-alt'
            )
            db.session.commit()
            
            app.logger.info(f'User logged in: {user.username}')
            
            if not user.tos_accepted:
                return redirect(url_for('main_routes.accept_terms'))
            
            # Redirect to onboarding if not completed
            if not user.onboarding_completed:
                return redirect(url_for('onboarding.welcome'))
            
            flash('You have been logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('user.dashboard'))
        else:
            if user:
                app.logger.warning(f'Failed login attempt for {email}: Incorrect password')
            else:
                app.logger.warning(f'Failed login attempt for {email}: User not found')
            flash('Login Unsuccessful. Please check email and password', 'danger')

    if form.errors:
        app.logger.warning(f'Login form validation errors: {form.errors}')

    return render_template('login.html', title='Login', form=form)


@auth.route("/logout")
def logout():
    if current_user.is_authenticated:
        current_user.log_activity(
            activity_type='logout',
            title='Logged out',
            icon='fa-sign-out-alt'
        )
        db.session.commit()
    
    session.clear()
    logout_user()
    return redirect(url_for('auth.login'))


# Password Reset Routes
@auth.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.form.get('email', '').lower()
    user = User.query.filter_by(email=email).first()
    if user:
        token = user.generate_reset_token()
        msg = Message(
            "Password reset request",
            sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
            recipients=[user.email]
        )
        reset_url = url_for('auth.reset_password_form', token=token, _external=True)
        msg.body = f"""To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email and no changes will be made.
"""
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send password reset email: {e}")
    
    # Always show same message for security
    flash('If an account exists with that email, a password reset link has been sent.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_form(token):
    """Password reset form with token."""
    from app.forms import ResetPasswordForm
    
    user = User.confirm_reset_token(token)
    if not user:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.login'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', form=form, token=token)


@auth.route('/reset_password', methods=['POST'])
def reset_password():
    """Legacy password reset POST handler."""
    token = request.form.get('token')
    password = request.form.get('password')
    user = User.confirm_reset_token(token)
    if user:
        user.set_password(password)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.login'))

