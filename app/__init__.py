from flask import Flask, current_app, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_babel import Babel
from flask.cli import with_appcontext, AppGroup
from flask_compress import Compress
from app.config import Config
from app.modules.role_setup import create_roles
from app.database import db
from app.models import User, Role, BusinessConfig
from app.modules.cache import cache, init_cache, cached_business_config, cache_warmup
from app.modules.performance import init_request_timing, setup_query_logging
from app.modules.logging_config import setup_structured_logging, init_correlation_id, init_request_logging
from dotenv import load_dotenv
import os
import logging
import click
import pytz
from datetime import datetime
from flask_ckeditor import CKEditor
from app.forms import EstimateRequestForm

# Load environment variables
load_dotenv()

# Initialize extensions
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
bcrypt = Bcrypt()
migrate = Migrate()
ckeditor = CKEditor()
babel = Babel()
compress = Compress()

# CLI group for debugging
debug_cli = AppGroup('debug')

# CLI command to create roles
@click.command('create-roles')
@with_appcontext
def create_roles_command():
    """Create default user roles."""
    create_roles()
    click.echo('Default roles have been created.')

@click.command('seed-business-config')
@with_appcontext
def seed_business_config_command():
    """Seed default business configuration."""
    default_configs = [
        {'setting_name': 'site_name', 'setting_value': 'Verso Backend'},
        {'setting_name': 'business_start_time', 'setting_value': '08:00'},
        {'setting_name': 'business_end_time', 'setting_value': '17:00'},
        {'setting_name': 'buffer_time_minutes', 'setting_value': '30'},
        {'setting_name': 'company_timezone', 'setting_value': 'America/Denver'},
        {'setting_name': 'primary_color', 'setting_value': '#007bff'},
        {'setting_name': 'secondary_color', 'setting_value': '#6c757d'},
        {'setting_name': 'font_family', 'setting_value': 'Arial, sans-serif'}
    ]
    for config in default_configs:
        if not BusinessConfig.query.filter_by(setting_name=config['setting_name']).first():
            new_config = BusinessConfig(**config)
            db.session.add(new_config)
    db.session.commit()
    click.echo('Default business configuration seeded.')

# Application factory
def create_app(config_class=Config):
    app = Flask(__name__)

    # Phase 24: Configure structured logging
    # Uses JSON format in production, readable format in debug
    setup_structured_logging(app)

    # Load configuration
    app.config.from_object(config_class)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///default.db').replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SCHEDULER_API_ENABLED'] = True

    # Mail configuration from environment variables
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # SQLAlchemy connection pooling options
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Register CLI commands
    app.cli.add_command(create_roles_command)
    app.cli.add_command(debug_cli)
    app.cli.add_command(seed_business_config_command)

    from app.cli_worker import run_worker_command
    app.cli.add_command(run_worker_command)

    # CLI command to set admin role
    @app.cli.command('set-admin')
    @click.argument('email')
    def set_admin(email):
        """Set a user as admin by email."""
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User not found: {email}")
            return
        
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            print("Admin role not found. Please run 'flask create-roles' first.")
            return
        
        if admin_role in user.roles:
            print(f"User {email} already has admin role.")
        else:
            user.roles.append(admin_role)
            db.session.commit()
            print(f"User {email} set as admin.")

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    mail.init_app(app)
    ckeditor = CKEditor(app)
    
    # Initialize Babel
    babel.init_app(app, locale_selector=get_locale)
    
    # Phase 23: Initialize caching and compression
    init_cache(app)
    compress.init_app(app)
    
    # Initialize performance monitoring
    init_request_timing(app)
    setup_query_logging(app)
    
    # Phase 24: Initialize observability
    init_correlation_id(app)
    init_request_logging(app)


    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Handle unauthorized requests - return JSON for AJAX, redirect for browser
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import jsonify
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
           request.headers.get('Accept', '').startswith('application/json'):
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'redirect': url_for('auth.login', next=request.url)
            }), 401
        # For regular requests, use the default behavior (redirect to login)
        from flask import redirect, flash
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login', next=request.url))


    # Load version from file
    def get_version():
        try:
            with open('VERSION', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return '1.0.0'

    # Inject version into templates
    @app.context_processor
    def inject_version():
        return dict(current_version=get_version())

    # Override url_for to add version to static files
    @app.context_processor
    def override_url_for():
        return dict(url_for=dated_url_for)

    def dated_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename')
            if filename:
                values['v'] = get_version()
        return url_for(endpoint, **values)

    # Inject business config into templates (cached for performance)
    @app.context_processor
    def inject_business_config():
        config_dict = cached_business_config()
        # Feature flags (default to True for existing deployments)
        feature_flags = {
            'ecommerce_enabled': config_dict.get('ecommerce_enabled', 'true') == 'true',
            'booking_enabled': config_dict.get('booking_enabled', 'true') == 'true'
        }
        return dict(business_config=config_dict, erf_form=EstimateRequestForm(), feature_flags=feature_flags)

    # Register Vite tags
    from app.utils.vite import vite_tags
    @app.context_processor
    def inject_vite_tags():
        return dict(vite_tags=vite_tags)

    # Register blueprints
    # Public routes (customer-facing)
    from app.routes.public_routes.auth import auth
    from app.routes.public_routes.main_routes import main
    from app.routes.public_routes.blog import blog_blueprint, news_update, updates_blueprint
    from app.routes.public_routes.newsletter import newsletter_bp
    from app.routes.public_routes.shop import shop_bp
    from app.routes.public_routes.pages import pages_bp
    from app.routes.public_routes.cart import cart_bp
    from app.routes.public_routes.media import media_bp
    
    # API routes
    from app.routes.api_routes.api import api
    from app.routes.api_routes.api_docs import api_docs
    from app.routes.api_routes.webhooks import webhooks_bp
    
    # Employee routes
    from app.routes.employee_routes.user import user
    from app.routes.employee_routes.employee import employee_bp
    
    # Admin routes
    from app.routes.admin_routes.admin import admin as admin_blueprint
    from app.routes.admin_routes.crm import crm_bp
    from app.routes.admin_routes.messaging import messaging_bp
    from app.routes.admin_routes.theme import theme_bp
    from app.routes.admin_routes.calendar import calendar_bp
    from app.routes.admin_routes.analytics import analytics_bp
    from app.routes.admin_routes.orders_admin import orders_admin_bp
    from app.routes.admin_routes.subscriptions import subscriptions_bp
    from app.routes.admin_routes.shop_admin import shop_admin_bp
    from app.routes.admin_routes.tasks_admin import tasks_admin_bp
    from app.routes.admin_routes.availability import availability_bp
    from app.routes.admin_routes.category_admin import category_admin_bp
    from app.routes.admin_routes.automation import automation_bp
    from app.routes.admin_routes.notifications import notifications_bp
    from app.routes.admin_routes.setup import setup_bp

    # Register main blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(user)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    csrf.exempt(api)  # Exempt API blueprint from CSRF
    app.register_blueprint(api)
    app.register_blueprint(blog_blueprint)
    app.register_blueprint(crm_bp)
    csrf.exempt(messaging_bp)  # Messaging uses AJAX with X-CSRFToken header
    app.register_blueprint(messaging_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(newsletter_bp)
    app.register_blueprint(theme_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(orders_admin_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(shop_admin_bp)
    app.register_blueprint(api_docs)
    app.register_blueprint(tasks_admin_bp)
    app.register_blueprint(availability_bp)
    app.register_blueprint(category_admin_bp)
    app.register_blueprint(automation_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(setup_bp)

    # Phase 17: Calendar & Scheduling Powerhouse
    from app.routes.admin_routes.scheduling import scheduling_bp
    app.register_blueprint(scheduling_bp)
    
    # Employee Schedule Management API
    from app.routes.admin_routes.schedule_routes import schedule_bp
    csrf.exempt(schedule_bp)  # API uses JSON requests
    app.register_blueprint(schedule_bp)

    # Phase 13: E-Commerce Routes
    from app.routes.admin_routes.ecommerce_admin import ecommerce_admin_bp
    from app.routes.public_routes.ecommerce import ecommerce_bp
    app.register_blueprint(ecommerce_admin_bp)
    app.register_blueprint(ecommerce_bp)

    # Phase E: Feature Completion - Media, SMS, Reports
    from app.routes.admin_routes.media_admin import media_admin_bp
    from app.routes.admin_routes.sms_admin import sms_admin_bp
    from app.routes.admin_routes.reports_admin import reports_admin_bp
    app.register_blueprint(media_admin_bp)
    app.register_blueprint(sms_admin_bp)
    app.register_blueprint(reports_admin_bp)

    # Phase 14: Reports Blueprint
    from app.routes.admin_routes.reports import reports_bp
    app.register_blueprint(reports_bp)

    # Phase 15: Communication Hub Expansion
    from app.routes.admin_routes.email_admin import email_admin_bp
    from app.routes.admin_routes.email_tracking import email_tracking_bp
    from app.routes.admin_routes.push import push_bp
    app.register_blueprint(email_admin_bp)
    csrf.exempt(email_tracking_bp)  # Tracking endpoints don't need CSRF
    app.register_blueprint(email_tracking_bp)
    csrf.exempt(push_bp)  # API endpoints
    app.register_blueprint(push_bp)

    # Phase 16: Forms & Data Collection Platform
    from app.routes.admin_routes.forms_admin import forms_admin_bp
    from app.routes.public_routes.forms import forms_bp
    app.register_blueprint(forms_admin_bp)
    app.register_blueprint(forms_bp)

    # Phase 22: Registration & User Experience Hardening
    from app.routes.public_routes.oauth import oauth_bp, init_oauth
    from app.routes.employee_routes.onboarding import onboarding_bp
    
    # Configure OAuth settings from environment
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
    app.config['RECAPTCHA_SITE_KEY'] = os.getenv('RECAPTCHA_SITE_KEY')
    app.config['RECAPTCHA_SECRET_KEY'] = os.getenv('RECAPTCHA_SECRET_KEY')
    
    # Initialize OAuth
    init_oauth(app)
    
    app.register_blueprint(oauth_bp)
    app.register_blueprint(onboarding_bp)

    # Phase 23: Support Ticketing System
    from app.routes.admin_routes.support import support_bp
    app.register_blueprint(support_bp)

    # Phase 24: Observability & Monitoring
    from app.routes.admin_routes.observability import observability_bp, init_metrics_collection
    csrf.exempt(observability_bp)  # Health/metrics endpoints don't need CSRF
    app.register_blueprint(observability_bp)
    init_metrics_collection(app)
    
    # Phase 24.5: Advanced Observability (Log Aggregation, Tracing, RUM, Sentry)
    try:
        from app.modules.advanced_observability import init_advanced_observability
        init_advanced_observability(app)
    except ImportError as e:
        app.logger.debug(f'Advanced observability not fully configured: {e}')

    # Phase 25: Advanced Infrastructure (Backup, Session, Deployment)
    from app.routes.admin_routes.backup import backup_bp
    app.register_blueprint(backup_bp)
    
    # Initialize backup service and session manager
    try:
        from app.modules.backup_service import backup_service
        from app.modules.session_manager import session_manager
        from app.modules.deployment import feature_flags, deployment_manager, health_checker
        
        backup_service.init_app(app)
        session_manager.init_app(app)
        feature_flags.init_app(app)
        deployment_manager.init_app(app)
        health_checker.init_app(app)
        
        # Register default health checks
        health_checker.register_check('database', health_checker.check_database)
        health_checker.register_check('redis', health_checker.check_redis)
        health_checker.register_check('disk_space', health_checker.check_disk_space)
    except Exception as e:
        app.logger.debug(f'Phase 25 infrastructure partially configured: {e}')

    # Phase 27: AI & Business Intelligence
    from app.routes.admin_routes.ai import ai_bp
    app.register_blueprint(ai_bp)
    
    try:
        from app.modules.ai_intelligence import business_intelligence
        business_intelligence.init_app(app)
    except Exception as e:
        app.logger.debug(f'Phase 27 AI not fully configured: {e}')

    # Phase 28: Security & OWASP Compliance
    try:
        from app.modules.security import rate_limiter, login_tracker, password_validator
        from app.modules.security_headers import security_headers, cookie_security
        from app.modules.mfa import mfa_service
        
        rate_limiter.init_app(app)
        login_tracker.init_app(app)
        password_validator.init_app(app)
        security_headers.init_app(app)
        cookie_security.init_app(app)
        mfa_service.init_app(app)
    except Exception as e:
        app.logger.debug(f'Phase 28 security partially configured: {e}')

    # Phase 29: Privacy & Compliance
    from app.routes.public_routes.privacy import privacy_bp, compliance_bp
    app.register_blueprint(privacy_bp)
    app.register_blueprint(compliance_bp)
    
    try:
        from app.modules.privacy import cookie_consent, data_exporter
        from app.modules.retention import retention_manager
        
        cookie_consent.init_app(app)
        data_exporter.init_app(app)
        retention_manager.init_app(app)
    except Exception as e:
        app.logger.debug(f'Phase 29 compliance partially configured: {e}')

    # Inject unread notification count into all templates
    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        unread_count = 0
        if current_user.is_authenticated:
            from app.models import Notification
            unread_count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()
        return dict(unread_notifications_count=unread_count)

    @app.after_request
    def log_page_view(response):
        # Ignore static assets and favicon
        if request.path.startswith('/static') or request.path == '/favicon.ico':
            return response
        
        # Ignore API calls
        if request.path.startswith('/api/'):
            return response
            
        # Respect Do Not Track header
        if request.headers.get('DNT') == '1':
            return response

        try:
            from app.models import PageView, VisitorSession
            from app.modules.reporting import parse_user_agent
            from flask_login import current_user
            import hashlib
            import uuid
            
            ip_hash = hashlib.sha256(request.remote_addr.encode('utf-8')).hexdigest()
            referrer = request.referrer
            user_agent_str = request.user_agent.string
            
            # Parse UTM parameters
            utm_source = request.args.get('utm_source')
            utm_medium = request.args.get('utm_medium')
            utm_campaign = request.args.get('utm_campaign')
            utm_term = request.args.get('utm_term')
            utm_content = request.args.get('utm_content')
            
            # Parse device info
            device_info = parse_user_agent(user_agent_str)
            
            # Get or create session token (stored in cookie)
            session_token = request.cookies.get('_vs_session')
            is_new_session = False
            
            if not session_token:
                session_token = str(uuid.uuid4())
                is_new_session = True
            
            # Get user ID if authenticated
            user_id = current_user.id if current_user.is_authenticated else None
            
            # Create page view record
            view = PageView(
                session_id=session_token,
                user_id=user_id,
                url=request.path,
                referrer=referrer,
                user_agent=user_agent_str[:500] if user_agent_str else None,
                ip_hash=ip_hash,
                utm_source=utm_source,
                utm_medium=utm_medium,
                utm_campaign=utm_campaign,
                utm_term=utm_term,
                utm_content=utm_content,
                device_type=device_info['device_type'],
                browser=device_info['browser'],
                os=device_info['os']
            )
            db.session.add(view)
            
            # Update or create session
            if is_new_session:
                session = VisitorSession(
                    session_token=session_token,
                    user_id=user_id,
                    ip_hash=ip_hash,
                    entry_page=request.path,
                    exit_page=request.path,
                    referrer=referrer,
                    utm_source=utm_source,
                    utm_medium=utm_medium,
                    utm_campaign=utm_campaign,
                    device_type=device_info['device_type'],
                    browser=device_info['browser'],
                    os=device_info['os']
                )
                db.session.add(session)
            else:
                # Update existing session
                session = VisitorSession.query.filter_by(session_token=session_token).first()
                if session:
                    session.update_activity(request.path)
                    if user_id and not session.user_id:
                        session.user_id = user_id
            
            db.session.commit()
            
            # Set session cookie if new
            if is_new_session:
                response.set_cookie(
                    '_vs_session', 
                    session_token, 
                    max_age=60*60*24*30,  # 30 days
                    httponly=True,
                    samesite='Lax'
                )
                
        except Exception as e:
            app.logger.error(f"Failed to log page view: {e}")
            db.session.rollback()
            
        return response


    # Initialize Flask-DebugToolbar in debug mode
    if app.debug or app.config.get('DEBUG_TB_ENABLED'):
        from flask_debugtoolbar import DebugToolbarExtension
        toolbar = DebugToolbarExtension(app)
    
    # Cache warmup on first request
    @app.before_request
    def warmup_caches():
        if not getattr(app, '_cache_warmed', False):
            cache_warmup()
            app._cache_warmed = True

    from app.routes.api_routes.booking_api import booking_api_bp, booking_pages_public_bp
    from app.routes.admin_routes.booking_admin import booking_admin_bp, booking_pages_bp
    from app.routes.admin_routes.stripe_settings import stripe_settings_bp
    from app.modules.security import rate_limiter
    app.register_blueprint(booking_api_bp)
    app.register_blueprint(booking_pages_public_bp)
    app.register_blueprint(booking_admin_bp)
    app.register_blueprint(booking_pages_bp)
    app.register_blueprint(stripe_settings_bp)
    # Exempt booking API from rate limiting for public booking flow
    if hasattr(rate_limiter, 'limiter') and rate_limiter.limiter:
        rate_limiter.limiter.exempt(booking_api_bp)
        # Exempt schedule API - routes have @rate_limiter.exempt but that runs before init_app
        from app.routes.admin_routes.schedule_routes import schedule_bp
        rate_limiter.limiter.exempt(schedule_bp)

    return app

def get_locale():
    # if a user is logged in, use the locale from the user settings
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  The best match wins.
    # We will refine this later with session/url support.
    
    # Check for 'lang' query param to switch language
    lang = request.args.get('lang')
    if lang and lang in current_app.config['LANGUAGES']:
        return lang
    
    # Check session
    if 'lang' in session:
        return session['lang']
        
    return request.accept_languages.best_match(current_app.config['LANGUAGES'].keys())


# Instantiate app for CLI and direct execution
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))