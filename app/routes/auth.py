from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user
from flask_mail import Message
from flask import current_app as app
# Assuming the below modules are part of your application
from app import db, mail, bcrypt  # Adjust 'yourapp' to your actual app's name
from app.models import User, Role  # Adjust 'yourapp.models' to your actual models' location
from app.forms import RegistrationForm, LoginForm, EstimateRequestForm  # Adjust 'yourapp.forms' to your actual forms' location

auth = Blueprint('auth', __name__)

@auth.context_processor
def combined_context_processor():
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form)

@auth.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if not form.accept_tos.data:
            flash('You must agree to the Terms and Conditions to register.', 'warning')
            return render_template('register.html', title='Register', form=form)

        # Refactor user existence checks into a function
        if user_exists(form.email.data, form.username.data):
            return render_template('register.html', title='Register', form=form)

        # Create and add the new user
        new_user = create_new_user(form)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        # Handle post-registration redirection
        return handle_post_registration_redirect()

    return render_template('register.html', title='Register', form=form)

def user_exists(email, username):
    """Check if a user with the given email or username already exists."""
    if User.query.filter_by(email=email).first():
        flash('An account with this email already exists.', 'warning')
        return True
    if User.query.filter_by(username=username).first():
        flash('This username is already taken. Please choose a different one.', 'warning')
        return True
    return False

def create_new_user(form):
    """Create a new user instance from the registration form."""
    new_user = User(username=form.username.data, email=form.email.data, password=form.password.data)
    new_user.first_name = form.first_name.data
    new_user.last_name = form.last_name.data
    role = Role.query.get(form.role.data)
    if role:
        new_user.roles.append(role)
    return new_user

def handle_post_registration_redirect():
    """Handle redirection after successful registration."""
    if 'booking_address' in session:
        flash('Account created! Please continue with your booking.', 'success')
        return redirect(url_for('user.manage_booking'))
    else:
        flash('Your account has been created! You are now logged in.', 'success')
        return redirect(url_for('main_routes.index'))

@auth.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Normalize email to lowercase
        email = form.email.data.lower()
        user = User.query.filter_by(email=email).first()

        if user:
            if bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                app.logger.info(f'User logged in: {user.username}')  # Logging successful login
                
                if not user.tos_accepted:
                    # Redirect to accept terms if not already accepted
                    return redirect(url_for('main_routes.accept_terms'))
                
                flash('You have been logged in!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main_routes.index'))
            else:
                # Log failed password check
                app.logger.warning(f'Failed login attempt for {email}: Incorrect password')
        else:
            # Log failed login attempt due to user not found
            app.logger.warning(f'Failed login attempt for {email}: User not found')

        flash('Login Unsuccessful. Please check email and password', 'danger')

    # Log form validation errors
    if form.errors:
        app.logger.warning(f'Login form validation errors: {form.errors}')

    return render_template('login.html', title='Login', form=form)

@auth.route("/logout")
def logout():
    # Clear the entire session when the user logs out
    session.clear()
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        token = user.generate_reset_token()
        msg = Message("Password reset request",
                      sender="noreply@demo.com",
                      recipients=[user.email])
        msg.body = f"""To reset your password, visit the following link:
{url_for('main.reset_password', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
"""
        mail.send(msg)
        return "Password reset email sent!"
    else:
        return "Invalid email"

@auth.route('/reset_password', methods=['POST'])
def reset_password():
    token = request.form.get('token')
    password = request.form.get('password')
    user = User.verify_reset_token(token)
    if user:
        # Hash the new password with bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user.set_password(hashed_password)  # Assuming set_password is properly adjusted to use bcrypt
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('main.register'))
