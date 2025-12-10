"""
Phase 10: Setup Wizard
Handles initial system configuration for fresh installations.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import User, Role, BusinessConfig
from app.database import db
from app.modules.role_setup import create_roles
from app.extensions import bcrypt

setup_bp = Blueprint('setup', __name__, url_prefix='/setup', template_folder='templates')

@setup_bp.before_request
def check_setup_status():
    """Ensure setup is only accessible if no users exist."""
    # Check if we have any users (specifically admin)
    admin_role = Role.query.filter_by(name='admin').first()
    if admin_role and admin_role.users:
        flash('Setup has already been completed.', 'info')
        return redirect(url_for('auth.login'))

@setup_bp.route('/', methods=['GET', 'POST'])
def wizard():
    """Initial setup wizard."""
    # Double check in case before_request didn't catch (e.g. roles exist but no users)
    if User.query.first():
         return redirect(url_for('auth.login'))
         
    if request.method == 'POST':
        # 1. Ensure Roles Exist
        create_roles()
        
        # 2. Business Details
        business_name = request.form.get('business_name')
        business_email = request.form.get('business_email')
        
        # Update or create configs
        _set_config('business_name', business_name)
        _set_config('business_email', business_email)
        # Defaults
        _set_config('business_start_time', '09:00')
        _set_config('business_end_time', '17:00')
        
        # 3. Create Admin User
        admin_email = request.form.get('admin_email')
        admin_password = request.form.get('admin_password')
        admin_name = request.form.get('admin_name')
        
        # Check if email exists (unlikely given the User.query.first check, but safety first)
        if User.query.filter_by(email=admin_email).first():
            flash('User with this email already exists.', 'error')
            return redirect(url_for('setup.wizard'))
            
        user = User(
            username=admin_name.lower().replace(' ', ''),
            email=admin_email,
            password=admin_password
        )
        user.first_name = admin_name
        user.confirmed = True # Auto-confirm admin
        
        # Assign Admin Role
        admin_role = Role.query.filter_by(name='admin').first()
        user.roles.append(admin_role)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Setup complete! Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('setup/wizard.html')

def _set_config(name, value):
    config = BusinessConfig.query.filter_by(setting_name=name).first()
    if not config:
        config = BusinessConfig(setting_name=name, setting_value=value)
        db.session.add(config)
    else:
        config.setting_value = value
