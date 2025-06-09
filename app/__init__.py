from flask import Flask, current_app, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask.cli import with_appcontext, AppGroup
from app.config import Config
from app.modules.role_setup import create_roles
from app.database import db
from app.models import User, Role, BusinessConfig
from dotenv import load_dotenv
import os
import logging
import click
import pytz
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize extensions
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
bcrypt = Bcrypt()
migrate = Migrate()

# CLI group for debugging
debug_cli = AppGroup('debug')

@debug_cli.command('print-env')
def print_env():
    """Print environment variables for debugging."""
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    print(f"SECRET_KEY: {os.environ.get('SECRET_KEY')}")
    print(f"DATABASE_URL: {current_app.config['SQLALCHEMY_DATABASE_URI']}")

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
        {'setting_name': 'business_start_time', 'setting_value': '08:00'},
        {'setting_name': 'business_end_time', 'setting_value': '17:00'},
        {'setting_name': 'buffer_time_minutes', 'setting_value': '30'},
        {'setting_name': 'company_timezone', 'setting_value': 'America/Denver'}
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

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

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

    # CLI command to set admin role
    @app.cli.command('set-admin')
    @click.argument('email')
    def set_admin(email):
        """Set a user as admin by email."""
        user = User.query.filter_by(email=email).first()
        if user:
            admin_role = Role.query.filter_by(name='admin').first()
            if admin_role not in user.roles:
                user.roles.append(admin_role)
                db.session.commit()
                print(f"User {email} set as admin.")
            else:
                print("User already has admin role.")
        else:
            print("User not found.")

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    mail.init_app(app)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Inject CSRF token into templates
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf())

    # Override url_for to add version to static files
    @app.context_processor
    def override_url_for():
        return dict(url_for=dated_url_for)

    def dated_url_for(endpoint, **values):
        if endpoint == 'static':
            filename = values.get('filename')
            if filename:
                values['v'] = '1.0.0'  # Update this version manually as needed
        return url_for(endpoint, **values)

    # Register blueprints
    from app.routes.auth import auth
    from app.routes.main_routes import main
    from app.routes.user import user
    from app.routes.admin import admin as admin_blueprint
    from app.routes.blog import blog_blueprint, news_update, updates_blueprint

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(user)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    app.register_blueprint(blog_blueprint)
    app.register_blueprint(news_update)
    app.register_blueprint(updates_blueprint)

    return app

# Instantiate app for CLI and direct execution
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))