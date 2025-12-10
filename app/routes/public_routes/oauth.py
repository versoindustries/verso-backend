"""
Phase 22: OAuth Authentication Routes
Google OAuth integration using Authlib
"""
from flask import Blueprint, redirect, url_for, flash, session, current_app, request
from flask_login import login_user, current_user
from authlib.integrations.flask_client import OAuth
from app import db
from app.models import User, Role, UserActivity, UserPreference

oauth_bp = Blueprint('oauth', __name__, url_prefix='/auth')

# OAuth client will be initialized in init_oauth()
oauth = OAuth()


def init_oauth(app):
    """Initialize OAuth with the Flask app."""
    oauth.init_app(app)
    
    # Register Google OAuth
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        access_token_url='https://oauth2.googleapis.com/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        api_base_url='https://www.googleapis.com/oauth2/v3/',
        client_kwargs={
            'scope': 'openid email profile'
        },
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
    )


@oauth_bp.route('/google')
def google_login():
    """Initiate Google OAuth login."""
    if current_user.is_authenticated:
        return redirect(url_for('main_routes.index'))
    
    # Check if OAuth is configured
    if not current_app.config.get('GOOGLE_CLIENT_ID'):
        flash('Google login is not configured. Please use email/password.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Store the next URL in session for redirect after login
    next_url = request.args.get('next')
    if next_url:
        session['oauth_next'] = next_url
    
    redirect_uri = url_for('oauth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@oauth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        current_app.logger.error(f'Google OAuth error: {e}')
        flash('Failed to authenticate with Google. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get user info from Google
    user_info = oauth.google.get('userinfo').json()
    google_id = user_info.get('sub')
    email = user_info.get('email')
    first_name = user_info.get('given_name', '')
    last_name = user_info.get('family_name', '')
    avatar_url = user_info.get('picture', '')
    
    if not email:
        flash('Could not retrieve email from Google. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Check if user exists with this Google ID
    user = User.query.filter_by(oauth_provider='google', oauth_id=google_id).first()
    
    if not user:
        # Check if user exists with this email (link accounts)
        user = User.query.filter_by(email=email.lower()).first()
        
        if user:
            # Link existing account to Google
            user.oauth_provider = 'google'
            user.oauth_id = google_id
            user.email_verified = True
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            db.session.commit()
            flash('Your Google account has been linked to your existing account.', 'success')
        else:
            # Create new user from Google OAuth
            import secrets
            user = User(
                username=email.split('@')[0] + '_' + secrets.token_hex(4),
                email=email.lower(),
                password=secrets.token_urlsafe(32)  # Random password, won't be used
            )
            user.first_name = first_name
            user.last_name = last_name
            user.oauth_provider = 'google'
            user.oauth_id = google_id
            user.email_verified = True
            user.avatar_url = avatar_url
            user.tos_accepted = True  # OAuth implies acceptance
            
            # Assign default role
            default_role = Role.query.filter_by(name='user').first()
            if not default_role:
                default_role = Role.query.filter_by(name='residential').first()
            if default_role:
                user.roles.append(default_role)
            
            db.session.add(user)
            db.session.commit()
            
            # Create default preferences
            prefs = UserPreference(user_id=user.id)
            db.session.add(prefs)
            
            # Log activity
            user.log_activity(
                activity_type='account_created',
                title='Account created via Google',
                description='Signed up using Google OAuth',
                icon='fa-google'
            )
            db.session.commit()
            
            flash('Account created successfully! Please complete your profile.', 'success')
    
    # Log in the user
    login_user(user)
    from datetime import datetime
    user.last_activity_at = datetime.utcnow()
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Redirect to onboarding if not completed
    if not user.onboarding_completed:
        return redirect(url_for('onboarding.welcome'))
    
    # Redirect to next URL or dashboard
    next_url = session.pop('oauth_next', None)
    return redirect(next_url or url_for('user.dashboard'))
