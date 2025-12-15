from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response, jsonify, Response
from flask_login import login_required, current_user
from app.modules.auth_manager import admin_required
from app.models import User, Estimator, Service, Appointment, ContactFormSubmission, Role, BusinessConfig, Page, PageRender, AuditLog, Location, ApiKey, Order, Post
from app.forms import ManageRolesForm, EditUserForm, EstimatorForm, EstimateRequestForm, ServiceOptionForm, CSRFTokenForm, CreateUserForm, RoleForm, BusinessConfigForm, PageForm, LocationForm, ApiKeyForm
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload
import csv
import io
from app.modules.audit import log_audit_event
from app.modules.data_manager import create_backup_zip, restore_from_zip
from app.database import db
from werkzeug.utils import secure_filename
from flask import send_file
import os
from datetime import datetime, date, time, timedelta
from app.modules.indexing import generate_sitemap, submit_sitemap_to_bing
from app import csrf
import secrets
from datetime import datetime, timedelta, timezone, time
import pytz
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.modules.compliance import collect_user_data

admin = Blueprint('admin', __name__, template_folder='templates')

@admin.context_processor
def combined_context_processor():
    erf_form = EstimateRequestForm()
    current_location = current_user.location if current_user.is_authenticated and current_user.location_id else None
    return dict(erf_form=erf_form, hide_estimate_form=True, current_location=current_location)

@admin.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Enhanced admin dashboard with KPI cards and metrics."""
    # Get business timezone
    config_dict = {c.setting_name: c.setting_value for c in BusinessConfig.query.all()}
    company_timezone = pytz.timezone(config_dict.get('company_timezone', 'America/Denver'))
    now_utc = datetime.now(pytz.utc)
    now_local = now_utc.astimezone(company_timezone)
    
    # Calculate date ranges
    today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_utc = today_start.astimezone(pytz.utc)
    today_end_utc = now_utc
    
    # Month start/end
    month_start = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_utc = month_start.astimezone(pytz.utc)
    
    # Previous month for comparison
    if now_local.month == 1:
        prev_month_start = now_local.replace(year=now_local.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        prev_month_start = now_local.replace(month=now_local.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start_utc = prev_month_start.astimezone(pytz.utc)
    
    # Location filter helper
    def apply_location_filter(query, model):
        if current_user.location_id:
            return query.filter(model.location_id == current_user.location_id)
        return query
    
    # === KPI 1: Revenue ===
    # Revenue today
    revenue_today_query = db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
        Order.status.in_(['paid', 'partially_paid', 'shipped', 'delivered']),
        Order.created_at >= today_start_utc
    )
    if current_user.location_id:
        revenue_today_query = revenue_today_query.filter(Order.location_id == current_user.location_id)
    revenue_today = revenue_today_query.scalar() or 0
    
    # Revenue this month  
    revenue_month_query = db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
        Order.status.in_(['paid', 'partially_paid', 'shipped', 'delivered']),
        Order.created_at >= month_start_utc
    )
    if current_user.location_id:
        revenue_month_query = revenue_month_query.filter(Order.location_id == current_user.location_id)
    revenue_month = revenue_month_query.scalar() or 0
    
    # Revenue last month (for trend)
    revenue_prev_month_query = db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
        Order.status.in_(['paid', 'partially_paid', 'shipped', 'delivered']),
        Order.created_at >= prev_month_start_utc,
        Order.created_at < month_start_utc
    )
    if current_user.location_id:
        revenue_prev_month_query = revenue_prev_month_query.filter(Order.location_id == current_user.location_id)
    revenue_prev_month = revenue_prev_month_query.scalar() or 0
    
    # === KPI 2: Leads (Contact forms + Appointments) ===
    leads_today_query = ContactFormSubmission.query.filter(ContactFormSubmission.submitted_at >= today_start_utc)
    if current_user.location_id:
        leads_today_query = leads_today_query.filter(ContactFormSubmission.location_id == current_user.location_id)
    
    appts_today_query = Appointment.query.filter(Appointment.preferred_date_time >= today_start_utc)
    if current_user.location_id:
        appts_today_query = appts_today_query.filter(Appointment.location_id == current_user.location_id)
    
    leads_today = leads_today_query.count() + appts_today_query.count()
    
    # Leads this month
    leads_month_query = ContactFormSubmission.query.filter(ContactFormSubmission.submitted_at >= month_start_utc)
    if current_user.location_id:
        leads_month_query = leads_month_query.filter(ContactFormSubmission.location_id == current_user.location_id)
    leads_month = leads_month_query.count()
    
    # Leads last month (for trend)
    leads_prev_month_query = ContactFormSubmission.query.filter(
        ContactFormSubmission.submitted_at >= prev_month_start_utc,
        ContactFormSubmission.submitted_at < month_start_utc
    )
    if current_user.location_id:
        leads_prev_month_query = leads_prev_month_query.filter(ContactFormSubmission.location_id == current_user.location_id)
    leads_prev_month = leads_prev_month_query.count()
    
    # === KPI 3: Appointments Today ===
    appointments_today_query = Appointment.query.filter(
        Appointment.preferred_date_time >= today_start_utc,
        Appointment.preferred_date_time < today_start_utc + timedelta(days=1)
    )
    if current_user.location_id:
        appointments_today_query = appointments_today_query.filter(Appointment.location_id == current_user.location_id)
    appointments_today = appointments_today_query.count()
    
    # === KPI 4: Active Users (logged in last 24h) ===
    active_users_query = User.query.filter(User.last_login >= now_utc - timedelta(hours=24))
    if current_user.location_id:
        active_users_query = active_users_query.filter(User.location_id == current_user.location_id)
    active_users = active_users_query.count()
    
    # Total users for reference
    total_users_query = User.query
    if current_user.location_id:
        total_users_query = total_users_query.filter(User.location_id == current_user.location_id)
    total_users = total_users_query.count()
    
    # Calculate trends (percentage change)
    def calc_trend(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    revenue_trend = calc_trend(revenue_month, revenue_prev_month)
    leads_trend = calc_trend(leads_month, leads_prev_month)
    
    # === Recent Data for Lists ===
    # Upcoming appointments this month
    if now_local.month == 12:
        next_month = now_local.replace(year=now_local.year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        next_month = now_local.replace(month=now_local.month+1, day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month_utc = next_month.astimezone(pytz.utc)
    # Use eager loading to prevent N+1 queries when displaying appointments
    appointments_query = Appointment.query.options(
        joinedload(Appointment.service),
        joinedload(Appointment.estimator)
    ).filter(
        Appointment.preferred_date_time >= now_utc,
        Appointment.preferred_date_time < next_month_utc
    )
    if current_user.location_id:
        appointments_query = appointments_query.filter(Appointment.location_id == current_user.location_id)
    appointments = appointments_query.order_by(Appointment.preferred_date_time.asc()).limit(10).all()
    
    for appointment in appointments:
        if appointment.preferred_date_time:
            utc_time = appointment.preferred_date_time.replace(tzinfo=pytz.utc)
            appointment.local_time = utc_time.astimezone(company_timezone)
        else:
            appointment.local_time = None
    
    # Recent contact form submissions
    submissions_query = ContactFormSubmission.query
    if current_user.location_id:
        submissions_query = submissions_query.filter(ContactFormSubmission.location_id == current_user.location_id)
    contact_form_submissions = submissions_query.order_by(ContactFormSubmission.submitted_at.desc()).limit(10).all()
    
    form = CSRFTokenForm()
    
    # Build KPIs dict for template
    kpis = {
        'revenue_today': revenue_today,
        'revenue_month': revenue_month,
        'revenue_trend': revenue_trend,
        'leads_today': leads_today,
        'leads_month': leads_month,
        'leads_trend': leads_trend,
        'appointments_today': appointments_today,
        'active_users': active_users,
        'total_users': total_users
    }
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        contact_form_submissions=contact_form_submissions,
        appointments=appointments,
        form=form,
        kpis=kpis
    )

@admin.route('/users')
@login_required
@admin_required
def list_users():
    """DEPRECATED: Redirects to unified user management dashboard."""
    return redirect(url_for('admin.user_management'))

@admin.route('/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    form = CreateUserForm()
    form.roles.choices = [(role.id, role.name) for role in Role.query.all()]
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.roles = [Role.query.get(id) for id in form.roles.data]
        try:
            db.session.add(user)
            db.session.commit()
            log_audit_event(current_user.id, 'create_user', 'User', user.id, {'username': user.username}, request.remote_addr)
            flash('User created successfully.', 'success')
            return redirect(url_for('admin.list_users'))
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already in use.', 'error')
    return render_template('admin/new_user.html', form=form)

@admin.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    form.roles.choices = [(role.id, role.name) for role in Role.query.all()]
    if request.method == 'GET':
        form.roles.data = [role.id for role in user.roles]
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        if form.password.data:
            user.set_password(form.password.data)
        user.roles = [Role.query.get(id) for id in form.roles.data]
        try:
            db.session.commit()
            log_audit_event(current_user.id, 'update_user', 'User', user.id, {'username': user.username}, request.remote_addr)
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.list_users'))
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already in use.', 'error')
    return render_template('admin/edit_user.html', form=form, user=user)

@admin.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot delete yourself.', 'error')
        return redirect(url_for('admin.list_users'))
    db.session.delete(user)
    db.session.commit()
    log_audit_event(current_user.id, 'delete_user', 'User', user_id, {'username': user.username}, request.remote_addr)
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.list_users'))

# =============================================================================
# Unified User Management Dashboard
# =============================================================================

@admin.route('/user-management')
@login_required
@admin_required
def user_management():
    """Unified user and role management dashboard with location assignment."""
    import json
    
    # Get users with roles and location eager loaded
    if current_user.location_id:
        users = User.query.options(
            selectinload(User.roles),
            selectinload(User.location)
        ).filter_by(location_id=current_user.location_id).order_by(User.username).all()
    else:
        users = User.query.options(
            selectinload(User.roles),
            selectinload(User.location)
        ).order_by(User.username).all()
    
    roles = Role.query.order_by(Role.name).all()
    locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()
    form = CSRFTokenForm()
    
    # Determine if user has owner role for conditional UI
    is_owner = current_user.has_role('owner')
    
    # Serialize users for React component - include location
    users_data = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name or '',
        'last_name': user.last_name or '',
        'phone': user.phone or '',
        'roles': [{'id': r.id, 'name': r.name} for r in user.roles],
        'role_names': ', '.join([r.name for r in user.roles]) or 'No roles',
        'location_id': user.location_id,
        'location_name': user.location.name if user.location else 'No location',
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
        'is_active': getattr(user, 'is_active', True)
    } for user in users]
    
    # Serialize roles for React component
    roles_data = [{
        'id': role.id,
        'name': role.name,
        'user_count': len(role.users),
        'users': [{'id': u.id, 'username': u.username} for u in role.users[:5]]  # First 5 users
    } for role in roles]
    
    # Serialize locations for dropdown
    locations_data = [{
        'id': loc.id,
        'name': loc.name,
        'address': loc.full_address,
        'user_count': loc.user_count,
        'is_primary': loc.is_primary
    } for loc in locations]
    
    return render_template('admin/user_management.html', 
                          users_json=json.dumps(users_data),
                          roles_json=json.dumps(roles_data),
                          locations_json=json.dumps(locations_data),
                          is_owner=is_owner,
                          form=form)

@admin.route('/api/user/<int:user_id>')
@login_required
@admin_required
def api_user_detail(user_id):
    """Get detailed user information for profile slideout."""
    user = User.query.options(selectinload(User.roles)).get_or_404(user_id)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name or '',
        'last_name': user.last_name or '',
        'phone': user.phone or '',
        'roles': [{'id': r.id, 'name': r.name} for r in user.roles],
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'is_active': getattr(user, 'is_active', True)
    })

@admin.route('/api/user/<int:user_id>/roles', methods=['PUT'])
@login_required
@admin_required
def api_update_user_roles(user_id):
    """Update user roles via AJAX."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data or 'role_ids' not in data:
        return jsonify({'success': False, 'error': 'Missing role_ids'}), 400
    
    role_ids = data.get('role_ids', [])
    
    # Validate and assign roles
    new_roles = []
    for rid in role_ids:
        role = Role.query.get(rid)
        if role:
            new_roles.append(role)
    
    user.roles = new_roles
    
    try:
        db.session.commit()
        log_audit_event(current_user.id, 'update_user_roles', 'User', user.id, 
                       {'roles': [r.name for r in new_roles]}, request.remote_addr)
        return jsonify({
            'success': True, 
            'roles': [{'id': r.id, 'name': r.name} for r in user.roles]
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating user roles: {e}')
        return jsonify({'success': False, 'error': 'Database error'}), 500


@admin.route('/api/user/<int:user_id>/location', methods=['PUT'])
@login_required
@admin_required
def api_update_user_location(user_id):
    """Update user location assignment via AJAX. Owner role recommended for bulk changes."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if data is None:
        return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
    
    location_id = data.get('location_id')
    
    # Handle null/None location (unassign)
    if location_id is None or location_id == '' or location_id == 0:
        user.location_id = None
        new_location_name = 'No location'
    else:
        # Validate location exists and is active
        location = Location.query.get(location_id)
        if not location:
            return jsonify({'success': False, 'error': 'Location not found'}), 404
        if not location.is_active:
            return jsonify({'success': False, 'error': 'Location is not active'}), 400
        
        user.location_id = location_id
        new_location_name = location.name
    
    try:
        db.session.commit()
        log_audit_event(current_user.id, 'update_user_location', 'User', user.id, 
                       {'location_id': location_id, 'location_name': new_location_name}, request.remote_addr)
        return jsonify({
            'success': True,
            'location_id': user.location_id,
            'location_name': new_location_name
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating user location: {e}')
        return jsonify({'success': False, 'error': 'Database error'}), 500

@admin.route('/api/role', methods=['POST'])
@login_required
@admin_required
def api_create_role():
    """Create a new role via AJAX."""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'success': False, 'error': 'Missing role name'}), 400
    
    role_name = data.get('name', '').strip()
    if not role_name:
        return jsonify({'success': False, 'error': 'Role name cannot be empty'}), 400
    
    # Check for existing role
    if Role.query.filter_by(name=role_name).first():
        return jsonify({'success': False, 'error': 'Role already exists'}), 400
    
    role = Role(name=role_name)
    try:
        db.session.add(role)
        db.session.commit()
        return jsonify({
            'success': True,
            'role': {'id': role.id, 'name': role.name, 'user_count': 0}
        })
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Role already exists'}), 400

@admin.route('/api/role/<int:role_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_role(role_id):
    """Delete a role via AJAX."""
    role = Role.query.get_or_404(role_id)
    
    if role.users:
        return jsonify({
            'success': False, 
            'error': f'Cannot delete role - {len(role.users)} user(s) assigned'
        }), 400
    
    try:
        db.session.delete(role)
        db.session.commit()
        return jsonify({'success': True})
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting role: {e}')
        return jsonify({'success': False, 'error': 'Database error'}), 500

@admin.route('/roles')
@login_required
@admin_required
def list_roles():
    """DEPRECATED: Redirects to unified user management dashboard (Roles tab)."""
    return redirect(url_for('admin.user_management'))

@admin.route('/role/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_role():
    form = RoleForm()
    if form.validate_on_submit():
        role = Role(name=form.name.data)
        try:
            db.session.add(role)
            db.session.commit()
            flash('Role created successfully.', 'success')
            return redirect(url_for('admin.list_roles'))
        except IntegrityError:
            db.session.rollback()
            flash('Role name already exists.', 'error')
    return render_template('admin/new_role.html', form=form)

@admin.route('/role/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    form = RoleForm(obj=role)
    if form.validate_on_submit():
        role.name = form.name.data
        try:
            db.session.commit()
            flash('Role updated successfully.', 'success')
            return redirect(url_for('admin.list_roles'))
        except IntegrityError:
            db.session.rollback()
            flash('Role name already exists.', 'error')
    return render_template('admin/edit_role.html', form=form, role=role)

@admin.route('/role/<int:role_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    if role.users:
        flash('Cannot delete role because it is assigned to users.', 'error')
        return redirect(url_for('admin.list_roles'))
    db.session.delete(role)
    db.session.commit()
    flash('Role deleted successfully.', 'success')
    return redirect(url_for('admin.list_roles'))

# NOTE: Old /admin/estimator and /admin/service routes have been removed.
# Use the unified booking dashboard at /admin/booking instead.
# Staff and services are now managed through the React-based BookingAdmin component.

@admin.route('/generate-sitemap', methods=['GET'])
@login_required
@admin_required
def generate_sitemap_route():
    try:
        generate_sitemap(current_app)
        flash('Sitemap generated and saved successfully.', 'success')
        flash('Sitemap submitted to Bing successfully.', 'success')
    except Exception as e:
        flash(f'Error generating or submitting sitemap: {e}', 'error')
    return redirect(url_for('admin.admin_dashboard'))

@admin.route('/api/admin_appointments')
@csrf.exempt
@login_required
@admin_required
def admin_appointments():
    now = datetime.utcnow()
    appointments = Appointment.query.filter(
        Appointment.preferred_date_time >= now
    ).order_by(Appointment.preferred_date_time).all()
    appointments_data = [{
        'first_name': appointment.first_name,
        'last_name': appointment.last_name,
        'phone': appointment.phone,
        'email': appointment.email,
        'preferred_date_time': appointment.preferred_date_time.replace(tzinfo=pytz.utc).isoformat(),
        'service': appointment.service.name if appointment.service else 'N/A',
        'estimator': appointment.estimator.name if appointment.estimator else 'N/A',
        'start': appointment.preferred_date_time.replace(tzinfo=pytz.utc).isoformat(),
        'end': (appointment.preferred_date_time + timedelta(hours=1)).replace(tzinfo=pytz.utc).isoformat()
    } for appointment in appointments]
    return jsonify(appointments_data), 200

@admin.route('/delete_contact_submission/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_contact_submission(id):
    submission = ContactFormSubmission.query.get_or_404(id)
    db.session.delete(submission)
    db.session.commit()
    flash('Contact form submission deleted successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin.route('/delete_appointment/<int:appointment_id>', methods=['POST'])
@login_required
@admin_required
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    db.session.delete(appointment)
    db.session.commit()
    flash('Appointment deleted successfully.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin.route('/business_config', methods=['GET', 'POST'])
@login_required
@admin_required
def business_config():
    form = BusinessConfigForm()
    if form.validate_on_submit():
        try:
            # Update or create settings
            settings = {
                'business_start_time': form.business_start_time.data,
                'business_end_time': form.business_end_time.data,
                'buffer_time_minutes': str(form.buffer_time_minutes.data),
                'company_timezone': form.company_timezone.data,
                'primary_color': form.primary_color.data,
                'secondary_color': form.secondary_color.data,
                'font_family': form.font_family.data
            }
            for name, value in settings.items():
                config = BusinessConfig.query.filter_by(setting_name=name).first()
                if config:
                    config.setting_value = value
                else:
                    config = BusinessConfig(setting_name=name, setting_value=value)
                    db.session.add(config)
            db.session.commit()
            log_audit_event(current_user.id, 'update_business_config', 'BusinessConfig', None, settings, request.remote_addr)
            current_app.logger.info('Business configuration updated successfully.')
            flash('Business settings updated successfully.', 'success')
            return redirect(url_for('admin.business_config'))
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating business configuration: {e}')
            flash('Error updating settings. Please try again.', 'error')

    # Load existing settings
    configs = BusinessConfig.query.all()
    config_dict = {config.setting_name: config.setting_value for config in configs}
    if config_dict:
        form.business_start_time.data = config_dict.get('business_start_time', '08:00')
        form.business_end_time.data = config_dict.get('business_end_time', '17:00')
        form.buffer_time_minutes.data = int(config_dict.get('buffer_time_minutes', 30))
        form.company_timezone.data = config_dict.get('company_timezone', 'America/Denver')
        form.primary_color.data = config_dict.get('primary_color', '#007bff')
        form.secondary_color.data = config_dict.get('secondary_color', '#6c757d')
        form.font_family.data = config_dict.get('font_family', 'Arial, sans-serif')

    return render_template('admin/business_config.html', form=form, hide_estimate_form=True)

@admin.route('/settings/features', methods=['GET', 'POST'])
@login_required
@admin_required
def feature_settings():
    """Toggle e-commerce and booking features on/off."""
    form = CSRFTokenForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Get feature toggles from form
            ecommerce_enabled = 'true' if request.form.get('ecommerce_enabled') else 'false'
            booking_enabled = 'true' if request.form.get('booking_enabled') else 'false'
            
            settings = {
                'ecommerce_enabled': ecommerce_enabled,
                'booking_enabled': booking_enabled
            }
            
            for name, value in settings.items():
                config = BusinessConfig.query.filter_by(setting_name=name).first()
                if config:
                    config.setting_value = value
                else:
                    config = BusinessConfig(setting_name=name, setting_value=value)
                    db.session.add(config)
            
            db.session.commit()
            log_audit_event(current_user.id, 'update_feature_settings', 'BusinessConfig', None, settings, request.remote_addr)
            flash('Feature settings updated successfully.', 'success')
            return redirect(url_for('admin.feature_settings'))
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating feature settings: {e}')
            flash('Error updating settings. Please try again.', 'error')
    
    # Load current settings
    configs = {c.setting_name: c.setting_value for c in BusinessConfig.query.all()}
    
    # Default to enabled for existing deployments
    features = {
        'ecommerce_enabled': configs.get('ecommerce_enabled', 'true') == 'true',
        'booking_enabled': configs.get('booking_enabled', 'true') == 'true'
    }
    
    return render_template('admin/feature_settings.html', form=form, features=features)

@admin.route('/pages')
@login_required
@admin_required
def list_pages():
    import json
    pages = Page.query.order_by(Page.title).all()
    form = CSRFTokenForm()
    
    # Serialize for AdminDataTable
    pages_json = json.dumps([{
        'id': page.id,
        'title': f'<a href="{url_for("admin.edit_page", page_id=page.id)}">{page.title}</a>',
        'slug': f'/{page.slug}',
        'status': f'<span class="badge bg-success">Published</span>' if page.is_published else '<span class="badge bg-warning">Draft</span>',
        'actions': f'<a href="{url_for("pages.show_page", slug=page.slug)}" class="btn btn-sm btn-outline-info" target="_blank"><i class="fas fa-eye"></i></a> <form method="POST" action="{url_for("admin.delete_page", page_id=page.id)}" class="d-inline" onsubmit="return confirm(\'Delete {page.title}?\');"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}"><button type="submit" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button></form>'
    } for page in pages])
    
    return render_template('admin/list_pages.html', pages=pages, pages_json=pages_json, form=form)

@admin.route('/page/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_page():
    from app.models import PageRevision
    form = PageForm()
    if form.validate_on_submit():
        # Check slug uniqueness
        if Page.query.filter_by(slug=form.slug.data).first():
            flash('Slug already exists.', 'error')
        else:
            page = Page(
                title=form.title.data,
                slug=form.slug.data,
                html_content=form.content.data,
                meta_description=form.meta_description.data,
                status=form.status.data,
                canonical_url=form.canonical_url.data or None,
                schema_type=form.schema_type.data,
                author_id=current_user.id,
                is_published=(form.status.data == 'published' or form.is_published.data)
            )
            db.session.add(page)
            db.session.flush()  # Get page.id before creating revision
            
            # Create initial revision
            revision = PageRevision(
                page_id=page.id,
                title=page.title,
                html_content=page.html_content,
                meta_description=page.meta_description,
                status=page.status,
                user_id=current_user.id,
                revision_note=form.revision_note.data or 'Initial creation'
            )
            db.session.add(revision)
            db.session.commit()
            
            log_audit_event(current_user.id, 'create_page', 'Page', page.id, {'title': page.title}, request.remote_addr)
            flash('Page created successfully.', 'success')
            return redirect(url_for('admin.list_pages'))
    return render_template('admin/edit_page.html', form=form, title='New Page')

@admin.route('/page/<int:page_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_page(page_id):
    from app.models import PageRevision
    page = Page.query.get_or_404(page_id)
    form = PageForm(obj=page)
    
    # Pre-populate content field on GET
    if request.method == 'GET':
        form.content.data = page.html_content
    
    if request.method == 'POST' and form.validate():
        # Check slug uniqueness if changed
        existing_page = Page.query.filter_by(slug=form.slug.data).first()
        if existing_page and existing_page.id != page.id:
            flash('Slug already exists.', 'error')
        else:
            # Create revision before updating (capture old state)
            revision = PageRevision(
                page_id=page.id,
                title=page.title,
                html_content=page.html_content,
                meta_description=page.meta_description,
                status=page.status,
                user_id=current_user.id,
                revision_note=form.revision_note.data or 'Content updated'
            )
            db.session.add(revision)
            
            # Update page with new values
            page.title = form.title.data
            page.slug = form.slug.data
            page.html_content = form.content.data
            page.meta_description = form.meta_description.data
            page.status = form.status.data
            page.canonical_url = form.canonical_url.data or None
            page.schema_type = form.schema_type.data
            page.is_published = (form.status.data == 'published' or form.is_published.data)
            
            db.session.commit()
            
            log_audit_event(current_user.id, 'update_page', 'Page', page.id, {'title': page.title}, request.remote_addr)
            flash('Page updated successfully.', 'success')
            return redirect(url_for('admin.list_pages'))
            
    return render_template('admin/edit_page.html', form=form, title='Edit Page', page=page)


@admin.route('/page/<int:page_id>/revisions')
@login_required
@admin_required
def page_revisions(page_id):
    """View revision history for a page."""
    from app.models import PageRevision
    page = Page.query.get_or_404(page_id)
    revisions = PageRevision.query.filter_by(page_id=page_id).order_by(PageRevision.created_at.desc()).all()
    form = CSRFTokenForm()
    return render_template('admin/revision_history.html', page=page, revisions=revisions, form=form)


@admin.route('/page/revision/<int:revision_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_revision(revision_id):
    """Restore a page to a previous revision."""
    from app.models import PageRevision
    revision = PageRevision.query.get_or_404(revision_id)
    page = revision.page
    
    # Create a revision of current state before restoring
    current_revision = PageRevision(
        page_id=page.id,
        title=page.title,
        html_content=page.html_content,
        meta_description=page.meta_description,
        status=page.status,
        user_id=current_user.id,
        revision_note=f'Auto-saved before restore from revision #{revision.id}'
    )
    db.session.add(current_revision)
    
    # Restore the page from the selected revision
    page.title = revision.title
    page.html_content = revision.html_content
    page.meta_description = revision.meta_description
    if revision.status:
        page.status = revision.status
    
    db.session.commit()
    
    log_audit_event(current_user.id, 'restore_page_revision', 'Page', page.id, {'revision_id': revision_id}, request.remote_addr)
    flash(f'Page restored to revision from {revision.created_at.strftime("%Y-%m-%d %H:%M")}.', 'success')
    return redirect(url_for('admin.edit_page', page_id=page.id))


@admin.route('/page/<int:page_id>/custom-fields', methods=['GET', 'POST'])
@login_required
@admin_required
def page_custom_fields(page_id):
    """Manage custom fields for a page."""
    from app.models import PageCustomField
    from app.forms import PageCustomFieldForm
    
    page = Page.query.get_or_404(page_id)
    form = PageCustomFieldForm()
    
    if form.validate_on_submit():
        # Check for duplicate field name
        existing = PageCustomField.query.filter_by(page_id=page_id, field_name=form.field_name.data).first()
        if existing:
            flash('A field with this name already exists.', 'error')
        else:
            field = PageCustomField(
                page_id=page_id,
                field_name=form.field_name.data,
                field_type=form.field_type.data,
                field_value=form.field_value.data,
                display_order=form.display_order.data
            )
            db.session.add(field)
            db.session.commit()
            flash('Custom field added.', 'success')
            return redirect(url_for('admin.page_custom_fields', page_id=page_id))
    
    fields = PageCustomField.query.filter_by(page_id=page_id).order_by(PageCustomField.display_order).all()
    csrf_form = CSRFTokenForm()
    return render_template('admin/page_custom_fields.html', page=page, fields=fields, form=form, csrf_form=csrf_form)


@admin.route('/page/custom-field/<int:field_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_custom_field(field_id):
    """Delete a custom field."""
    from app.models import PageCustomField
    field = PageCustomField.query.get_or_404(field_id)
    page_id = field.page_id
    db.session.delete(field)
    db.session.commit()
    flash('Custom field deleted.', 'success')
    return redirect(url_for('admin.page_custom_fields', page_id=page_id))


@admin.route('/page/<int:page_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_page(page_id):
    page = Page.query.get_or_404(page_id)
    log_audit_event(current_user.id, 'delete_page', 'Page', page_id, {'title': page.title}, request.remote_addr)
    db.session.delete(page)
    db.session.commit()
    flash('Page deleted successfully.', 'success')
    return redirect(url_for('admin.list_pages'))

@admin.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    import json
    page_num = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page_num, per_page=50)
    
    # Serialize for AdminDataTable
    logs_json = json.dumps([{
        'id': log.id,
        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'user': f'<a href="{url_for("admin.edit_user", user_id=log.user.id)}">{log.user.username}</a>' if log.user else f'User ID: {log.user_id} (Deleted)',
        'action': f'<span class="badge bg-secondary">{log.action}</span>',
        'target_type': log.target_type or '-',
        'target_id': str(log.target_id) if log.target_id else '-',
        'ip_address': log.ip_address or '-',
        'details': f'<button type="button" class="btn btn-sm btn-info" title="{log.details}">View</button>' if log.details else '-'
    } for log in logs.items])
    
    return render_template('admin/audit_logs.html', logs=logs, logs_json=logs_json)

@admin.route('/api/recent-activity')
@login_required
@admin_required
def recent_activity_api():
    """JSON API for recent activity feed."""
    limit = request.args.get('limit', 10, type=int)
    limit = min(limit, 50)  # Cap at 50 for performance
    
    logs = AuditLog.query.options(
        joinedload(AuditLog.user)
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    activities = [{
        'id': log.id,
        'action': log.action,
        'entity_type': log.target_type or '',
        'entity_id': log.target_id,
        'details': log.details if isinstance(log.details, dict) else {},
        'created_at': log.timestamp.isoformat(),
        'user_name': log.user.username if log.user else None
    } for log in logs]
    
    return jsonify(activities)

@admin.route('/data-management')
@login_required
@admin_required
def data_management():
    form = CSRFTokenForm()
    return render_template('admin/data_management.html', form=form)


@admin.route('/api/data-stats')
@login_required
@admin_required
def data_stats():
    """JSON API for database statistics."""
    import os
    from app.models import User, Appointment, Order, Product
    
    # Get record counts
    total_users = User.query.count()
    total_appointments = Appointment.query.count()
    total_orders = Order.query.count() if hasattr(Order, 'query') else 0
    total_products = Product.query.count() if hasattr(Product, 'query') else 0
    
    # Get database file size (for SQLite)
    db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    db_size = 'N/A'
    if 'sqlite' in db_path:
        db_file = db_path.replace('sqlite:///', '')
        if os.path.exists(db_file):
            size_bytes = os.path.getsize(db_file)
            if size_bytes < 1024:
                db_size = f'{size_bytes} B'
            elif size_bytes < 1024 * 1024:
                db_size = f'{size_bytes / 1024:.1f} KB'
            else:
                db_size = f'{size_bytes / 1024 / 1024:.1f} MB'
    
    # Get last backup from audit log
    last_backup_log = AuditLog.query.filter_by(action='download_backup').order_by(AuditLog.timestamp.desc()).first()
    last_backup = last_backup_log.timestamp.strftime('%Y-%m-%d %H:%M') if last_backup_log else None
    
    # Get recent data management activities
    activities = AuditLog.query.filter(
        AuditLog.action.in_(['download_backup', 'restore_data', 'export_user_data'])
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    activities_list = [{
        'id': a.id,
        'action': a.action.replace('_', ' ').title(),
        'timestamp': a.timestamp.strftime('%Y-%m-%d %H:%M'),
        'details': str(a.details) if a.details else ''
    } for a in activities]
    
    return jsonify({
        'stats': {
            'totalUsers': total_users,
            'totalAppointments': total_appointments,
            'totalOrders': total_orders,
            'totalProducts': total_products,
            'lastBackup': last_backup,
            'databaseSize': db_size
        },
        'activities': activities_list
    })


@admin.route('/backup/download')
@login_required
@admin_required
def download_backup():
    zip_buffer = create_backup_zip()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_audit_event(current_user.id, 'download_backup', None, None, None, request.remote_addr)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'verso_backup_{timestamp}.zip'
    )

@admin.route('/data/import', methods=['POST'])
@login_required
@admin_required
def import_data():
    form = CSRFTokenForm()
    if form.validate_on_submit():
        if 'backup_file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('admin.data_management'))
            
        file = request.files['backup_file']
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('admin.data_management'))
            
        if file:
            try:
                success, msg = restore_from_zip(file)
                if success:
                    log_audit_event(current_user.id, 'restore_data', 'System', None, {'filename': file.filename}, request.remote_addr)
                    flash('Data restored successfully.', 'success')
                else:
                    flash(f'Restore failed: {msg}', 'error')
            except Exception as e:
                flash(f'Error processing file: {e}', 'error')
                
    return redirect(url_for('admin.data_management'))

@admin.route('/data/compliance/export', methods=['POST'])
@login_required
@admin_required
def export_user_data():
    email = request.form.get('email')
    if not email:
        flash('Email is required.', 'error')
        return redirect(url_for('admin.data_management'))
    
    data = collect_user_data(email=email)
    
    response = make_response(jsonify(data))
    response.headers['Content-Disposition'] = f'attachment; filename=gdpr_export_{email}.json'
    return response

# --- Location Management ---

@admin.route('/locations')
@login_required
@admin_required
def list_locations():
    """Location management dashboard - enterprise UI with full location details."""
    import json
    locations = Location.query.order_by(Location.is_primary.desc(), Location.name).all()
    users = User.query.order_by(User.username).all()
    form = CSRFTokenForm()
    
    # Determine if user has owner role for conditional UI
    is_owner = current_user.has_role('owner')
    
    # Serialize for LocationManagement React component - include all new fields
    locations_json = json.dumps([{
        'id': loc.id,
        'name': loc.name,
        'address': loc.address or '',
        'city': loc.city or '',
        'state': loc.state or '',
        'zipCode': loc.zip_code or '',
        'phone': loc.phone or '',
        'email': loc.email or '',
        'timezone': loc.timezone or '',
        'isActive': loc.is_active if loc.is_active is not None else True,
        'isPrimary': loc.is_primary if loc.is_primary is not None else False,
        'managerId': loc.manager_id,
        'managerName': f"{loc.manager.first_name or ''} {loc.manager.last_name or ''}".strip() if loc.manager else None,
        'userCount': loc.user_count,
        'fullAddress': loc.full_address,
        'createdAt': loc.created_at.isoformat() if loc.created_at else None,
        'updatedAt': loc.updated_at.isoformat() if loc.updated_at else None
    } for loc in locations])
    
    # Serialize users for manager dropdown
    users_json = json.dumps([{
        'id': u.id,
        'name': f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username,
        'username': u.username
    } for u in users])
    
    return render_template('admin/list_locations.html', 
                          locations=locations, 
                          locations_json=locations_json, 
                          users_json=users_json,
                          is_owner=is_owner,
                          form=form)


@admin.route('/api/locations', methods=['GET'])
@login_required
@admin_required
def api_list_locations():
    """JSON API for listing locations with all fields."""
    locations = Location.query.order_by(Location.is_primary.desc(), Location.name).all()
    return jsonify({
        'locations': [{
            'id': loc.id,
            'name': loc.name,
            'address': loc.address or '',
            'city': loc.city or '',
            'state': loc.state or '',
            'zipCode': loc.zip_code or '',
            'phone': loc.phone or '',
            'email': loc.email or '',
            'timezone': loc.timezone or '',
            'isActive': loc.is_active if loc.is_active is not None else True,
            'isPrimary': loc.is_primary if loc.is_primary is not None else False,
            'managerId': loc.manager_id,
            'managerName': f"{loc.manager.first_name or ''} {loc.manager.last_name or ''}".strip() if loc.manager else None,
            'userCount': loc.user_count,
            'fullAddress': loc.full_address,
            'createdAt': loc.created_at.isoformat() if loc.created_at else None
        } for loc in locations]
    })


@admin.route('/api/locations', methods=['POST'])
@login_required
@admin_required
def api_create_location():
    """JSON API for creating a location with all fields."""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Location name is required'}), 400
    
    # Check for duplicate name
    existing = Location.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Location name already exists'}), 400
    
    # If marking as primary, unset other primaries
    if data.get('isPrimary'):
        Location.query.filter_by(is_primary=True).update({'is_primary': False})
    
    location = Location(
        name=data['name'],
        address=data.get('address'),
        city=data.get('city'),
        state=data.get('state'),
        zip_code=data.get('zipCode'),
        phone=data.get('phone'),
        email=data.get('email'),
        timezone=data.get('timezone'),
        is_active=data.get('isActive', True),
        is_primary=data.get('isPrimary', False),
        manager_id=data.get('managerId') or None
    )
    
    try:
        db.session.add(location)
        db.session.commit()
        log_audit_event(current_user.id, 'create_location', 'Location', location.id, {'name': location.name}, request.remote_addr)
        
        return jsonify({
            'location': {
                'id': location.id,
                'name': location.name,
                'address': location.address or '',
                'city': location.city or '',
                'state': location.state or '',
                'zipCode': location.zip_code or '',
                'phone': location.phone or '',
                'email': location.email or '',
                'timezone': location.timezone or '',
                'isActive': location.is_active,
                'isPrimary': location.is_primary,
                'managerId': location.manager_id,
                'managerName': f"{location.manager.first_name or ''} {location.manager.last_name or ''}".strip() if location.manager else None,
                'userCount': 0,
                'fullAddress': location.full_address,
                'createdAt': location.created_at.isoformat() if location.created_at else None
            },
            'message': 'Location created successfully'
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Location name already exists'}), 400


@admin.route('/api/locations/<int:location_id>', methods=['PUT'])
@login_required
@admin_required
def api_update_location(location_id):
    """JSON API for updating a location with all fields."""
    location = Location.query.get_or_404(location_id)
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Location name is required'}), 400
    
    # Check for duplicate name (excluding current location)
    existing = Location.query.filter(Location.name == data['name'], Location.id != location_id).first()
    if existing:
        return jsonify({'error': 'Location name already exists'}), 400
    
    # If marking as primary, unset other primaries
    if data.get('isPrimary') and not location.is_primary:
        Location.query.filter(Location.id != location_id, Location.is_primary == True).update({'is_primary': False})
    
    location.name = data['name']
    location.address = data.get('address')
    location.city = data.get('city')
    location.state = data.get('state')
    location.zip_code = data.get('zipCode')
    location.phone = data.get('phone')
    location.email = data.get('email')
    location.timezone = data.get('timezone')
    location.is_active = data.get('isActive', True)
    location.is_primary = data.get('isPrimary', False)
    location.manager_id = data.get('managerId') or None
    
    try:
        db.session.commit()
        log_audit_event(current_user.id, 'update_location', 'Location', location.id, {'name': location.name}, request.remote_addr)
        
        return jsonify({
            'location': {
                'id': location.id,
                'name': location.name,
                'address': location.address or '',
                'city': location.city or '',
                'state': location.state or '',
                'zipCode': location.zip_code or '',
                'phone': location.phone or '',
                'email': location.email or '',
                'timezone': location.timezone or '',
                'isActive': location.is_active,
                'isPrimary': location.is_primary,
                'managerId': location.manager_id,
                'managerName': f"{location.manager.first_name or ''} {location.manager.last_name or ''}".strip() if location.manager else None,
                'userCount': location.user_count,
                'fullAddress': location.full_address,
                'createdAt': location.created_at.isoformat() if location.created_at else None
            },
            'message': 'Location updated successfully'
        })
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Location name already exists'}), 400


@admin.route('/api/locations/<int:location_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_location(location_id):
    """JSON API for deleting a location."""
    location = Location.query.get_or_404(location_id)
    
    # Check if location has users assigned
    if hasattr(location, 'users') and len(location.users) > 0:
        return jsonify({'error': 'Cannot delete location with assigned users. Please reassign users first.'}), 400
    
    name = location.name
    try:
        db.session.delete(location)
        db.session.commit()
        log_audit_event(current_user.id, 'delete_location', 'Location', location_id, {'name': name}, request.remote_addr)
        
        return jsonify({'message': 'Location deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin.route('/location/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_location():
    form = LocationForm()
    if form.validate_on_submit():
        location = Location(name=form.name.data, address=form.address.data)
        try:
            db.session.add(location)
            db.session.commit()
            log_audit_event(current_user.id, 'create_location', 'Location', location.id, {'name': location.name}, request.remote_addr)
            flash('Location created successfully.', 'success')
            return redirect(url_for('admin.list_locations'))
        except IntegrityError:
            db.session.rollback()
            flash('Location name already exists.', 'error')
    return render_template('admin/new_location.html', form=form)

@admin.route('/location/<int:location_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)
    form = LocationForm(obj=location)
    if form.validate_on_submit():
        location.name = form.name.data
        location.address = form.address.data
        try:
            db.session.commit()
            log_audit_event(current_user.id, 'update_location', 'Location', location.id, {'name': location.name}, request.remote_addr)
            flash('Location updated successfully.', 'success')
            return redirect(url_for('admin.list_locations'))
        except IntegrityError:
            db.session.rollback()
            flash('Location name already exists.', 'error')
    return render_template('admin/new_location.html', form=form)

# --- API Key Management ---

@admin.route('/api_keys')
@login_required
@admin_required
def list_api_keys():
    import json
    keys = ApiKey.query.order_by(ApiKey.created_at.desc()).all()
    form = CSRFTokenForm()
    
    # Serialize for AdminDataTable
    keys_json = json.dumps([{
        'id': key.id,
        'name': key.name,
        'prefix': f'<code>{key.prefix}...</code>',
        'scopes': ' '.join([f'<span class="badge bg-info">{s}</span>' for s in (key.scopes or [])]),
        'created': key.created_at.strftime('%Y-%m-%d'),
        'last_used': key.last_used_at.strftime('%Y-%m-%d %H:%M') if key.last_used_at else 'Never',
        'status': '<span class="badge bg-success">Active</span>' if key.is_active else '<span class="badge bg-danger">Revoked</span>',
        'actions': f'<form action="{url_for("admin.revoke_api_key", key_id=key.id)}" method="POST" class="d-inline" onsubmit="return confirm(\'Revoke this key?\');"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}"><button type="submit" class="btn btn-danger btn-sm">Revoke</button></form>' if key.is_active else ''
    } for key in keys])
    
    return render_template('admin/list_api_keys.html', keys=keys, keys_json=keys_json, form=form)

@admin.route('/api_keys/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_api_key():
    form = ApiKeyForm()
    if form.validate_on_submit():
        raw_key = f"sk_live_{secrets.token_hex(24)}"
        key = ApiKey(
            name=form.name.data,
            scopes=form.scopes.data,
            user_id=current_user.id
        )
        key.set_key(raw_key)
        try:
            db.session.add(key)
            db.session.commit()
            log_audit_event(current_user.id, 'create_api_key', 'ApiKey', key.id, {'name': key.name}, request.remote_addr)
            flash(f'API Key created. Copy this now, it will not be shown again: {raw_key}', 'success')
            return redirect(url_for('admin.list_api_keys'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating key: {e}', 'error')
            
    return render_template('admin/new_api_key.html', form=form)

@admin.route('/api_keys/revoke/<int:key_id>', methods=['POST'])
@login_required
@admin_required
def revoke_api_key(key_id):
    key = ApiKey.query.get_or_404(key_id)
    key.is_active = False
    db.session.commit()
    log_audit_event(current_user.id, 'revoke_api_key', 'ApiKey', key.id, {'name': key.name}, request.remote_addr)
    flash('API Key revoked.', 'success')
    return redirect(url_for('admin.list_api_keys'))


# --- Phase 2: Reschedule Request Management ---

@admin.route('/reschedule-requests')
@login_required
@admin_required
def list_reschedule_requests():
    """List all pending and recent reschedule requests."""
    import json
    from app.models import RescheduleRequest
    
    pending = RescheduleRequest.query.filter_by(status='pending').order_by(RescheduleRequest.created_at.desc()).all()
    recent = RescheduleRequest.query.filter(
        RescheduleRequest.status.in_(['approved', 'rejected'])
    ).order_by(RescheduleRequest.updated_at.desc()).limit(20).all()
    
    form = CSRFTokenForm()
    
    # Serialize pending requests for AdminDataTable
    pending_json = json.dumps([{
        'id': rr.id,
        'appointment': f'<strong>{rr.appointment.first_name} {rr.appointment.last_name}</strong><br><small class="text-muted">{rr.appointment.service.name if rr.appointment.service else "N/A"}</small>',
        'staff': rr.user.username if rr.user else '-',
        'current_time': rr.appointment.preferred_date_time.strftime('%Y-%m-%d %H:%M') if rr.appointment.preferred_date_time else '-',
        'proposed_time': f'<strong class="text-primary">{rr.proposed_datetime.strftime("%Y-%m-%d %H:%M")}</strong>' if rr.proposed_datetime else '-',
        'reason': rr.reason or '-',
        'submitted': rr.created_at.strftime('%Y-%m-%d %H:%M') if rr.created_at else '-',
        'actions': f'''<form method="POST" action="{url_for('admin.approve_reschedule', request_id=rr.id)}" class="d-inline">
            <input type="hidden" name="csrf_token" value="{form.csrf_token._value()}">
            <button type="submit" class="btn btn-sm btn-success" onclick="return confirm('Approve this reschedule?')"><i class="fas fa-check"></i></button>
        </form>
        <button type="button" class="btn btn-sm btn-danger" data-bs-toggle="modal" data-bs-target="#rejectModal{rr.id}"><i class="fas fa-times"></i></button>'''
    } for rr in pending])
    
    # Serialize recent history for AdminDataTable
    recent_json = json.dumps([{
        'id': rr.id,
        'appointment': f'{rr.appointment.first_name} {rr.appointment.last_name}' if rr.appointment else '-',
        'proposed_time': rr.proposed_datetime.strftime('%Y-%m-%d %H:%M') if rr.proposed_datetime else '-',
        'status': f'<span class="badge bg-success">Approved</span>' if rr.status == 'approved' else '<span class="badge bg-danger">Rejected</span>',
        'admin_notes': rr.admin_notes or '-',
        'processed': rr.updated_at.strftime('%Y-%m-%d %H:%M') if rr.updated_at else '-'
    } for rr in recent])
    
    return render_template('admin/reschedule_requests.html', 
                          pending=pending, recent=recent, form=form,
                          pending_json=pending_json, recent_json=recent_json)


@admin.route('/reschedule/<int:request_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_reschedule(request_id):
    """Approve a reschedule request and update the appointment."""
    from app.models import RescheduleRequest
    
    reschedule = RescheduleRequest.query.get_or_404(request_id)
    
    if reschedule.status != 'pending':
        flash('This request has already been processed.', 'warning')
        return redirect(url_for('admin.list_reschedule_requests'))
    
    # Update the appointment with new time
    appointment = reschedule.appointment
    old_time = appointment.preferred_date_time
    appointment.preferred_date_time = reschedule.proposed_datetime
    
    reschedule.status = 'approved'
    reschedule.admin_notes = request.form.get('admin_notes', '')
    
    db.session.commit()
    
    log_audit_event(
        current_user.id, 
        'approve_reschedule', 
        'RescheduleRequest', 
        request_id, 
        {'old_time': old_time.isoformat(), 'new_time': reschedule.proposed_datetime.isoformat()}, 
        request.remote_addr
    )
    
    # TODO: Send notification email to customer about the reschedule
    
    flash(f'Reschedule approved. Appointment moved to {reschedule.proposed_datetime.strftime("%Y-%m-%d %H:%M")}.', 'success')
    return redirect(url_for('admin.list_reschedule_requests'))


@admin.route('/reschedule/<int:request_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_reschedule(request_id):
    """Reject a reschedule request."""
    from app.models import RescheduleRequest
    
    reschedule = RescheduleRequest.query.get_or_404(request_id)
    
    if reschedule.status != 'pending':
        flash('This request has already been processed.', 'warning')
        return redirect(url_for('admin.list_reschedule_requests'))
    
    reschedule.status = 'rejected'
    reschedule.admin_notes = request.form.get('admin_notes', '')
    
    db.session.commit()
    
    log_audit_event(
        current_user.id, 
        'reject_reschedule', 
        'RescheduleRequest', 
        request_id, 
        {'reason': reschedule.admin_notes}, 
        request.remote_addr
    )
    
    flash('Reschedule request rejected.', 'info')
    return redirect(url_for('admin.list_reschedule_requests'))


# --- Phase 2: Recurring Appointments ---

@admin.route('/appointment/<int:appointment_id>/create-recurring', methods=['POST'])
@login_required
@admin_required
def create_recurring_appointments(appointment_id):
    """Create recurring appointments from a base appointment."""
    from app.modules.availability_service import generate_recurring_appointments
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    recurrence_type = request.form.get('recurrence_type', 'weekly')
    count = int(request.form.get('count', 4))
    
    if count < 1 or count > 52:
        flash('Count must be between 1 and 52.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    try:
        new_appointments = generate_recurring_appointments(appointment, recurrence_type, count)
        
        # Mark base appointment as recurring parent
        appointment.is_recurring = True
        
        for appt in new_appointments:
            db.session.add(appt)
        
        db.session.commit()
        
        log_audit_event(
            current_user.id,
            'create_recurring_appointments',
            'Appointment',
            appointment_id,
            {'type': recurrence_type, 'count': count},
            request.remote_addr
        )
        
        flash(f'Created {count} recurring appointments ({recurrence_type}).', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    
    return redirect(url_for('admin.admin_dashboard'))


# ============================================================================
# Phase 5: Employee Portal & HR Administration
# ============================================================================

@admin.route('/hr/leave-requests')
@login_required
@admin_required
def hr_leave_requests():
    """View all leave requests with approval actions."""
    from app.models import LeaveRequest
    from app.forms import LeaveApprovalForm
    
    pending = LeaveRequest.query.filter_by(status='pending').order_by(LeaveRequest.created_at.desc()).all()
    recent = LeaveRequest.query.filter(
        LeaveRequest.status.in_(['approved', 'rejected'])
    ).order_by(LeaveRequest.approved_at.desc()).limit(20).all()
    
    form = LeaveApprovalForm()
    csrf_form = CSRFTokenForm()
    
    return render_template('admin/hr/leave_requests.html', pending=pending, recent=recent, form=form, csrf_form=csrf_form)


@admin.route('/hr/leave/<int:request_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_leave(request_id):
    """Approve a leave request and deduct from balance."""
    from app.models import LeaveRequest, LeaveBalance
    
    leave = LeaveRequest.query.get_or_404(request_id)
    
    if leave.status != 'pending':
        flash('This request has already been processed.', 'warning')
        return redirect(url_for('admin.hr_leave_requests'))
    
    leave.status = 'approved'
    leave.approved_by_id = current_user.id
    leave.approved_at = datetime.utcnow()
    leave.admin_notes = request.form.get('admin_notes', '')
    
    # Deduct from leave balance
    days_requested = leave.days_requested()
    current_year = leave.start_date.year
    
    balance = LeaveBalance.query.filter_by(
        user_id=leave.user_id,
        leave_type=leave.leave_type,
        year=current_year
    ).first()
    
    if balance:
        balance.used_days += days_requested
    
    db.session.commit()
    
    log_audit_event(
        current_user.id,
        'approve_leave',
        'LeaveRequest',
        request_id,
        {'days': days_requested, 'type': leave.leave_type},
        request.remote_addr
    )
    
    # Queue email notification to employee
    from app.models import Task
    notification_task = Task(
        name='leave_decision_notification',
        payload={
            'leave_request_id': request_id,
            'decision': 'approved',
            'admin_notes': leave.admin_notes
        }
    )
    db.session.add(notification_task)
    db.session.commit()

    flash(f'Leave request approved. {days_requested} day(s) deducted from balance.', 'success')
    return redirect(url_for('admin.hr_leave_requests'))


@admin.route('/hr/leave/<int:request_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_leave(request_id):
    """Reject a leave request."""
    from app.models import LeaveRequest
    
    leave = LeaveRequest.query.get_or_404(request_id)
    
    if leave.status != 'pending':
        flash('This request has already been processed.', 'warning')
        return redirect(url_for('admin.hr_leave_requests'))
    
    leave.status = 'rejected'
    leave.approved_by_id = current_user.id
    leave.approved_at = datetime.utcnow()
    leave.admin_notes = request.form.get('admin_notes', '')
    
    db.session.commit()
    
    log_audit_event(
        current_user.id,
        'reject_leave',
        'LeaveRequest',
        request_id,
        {'reason': leave.admin_notes},
        request.remote_addr
    )
    
    # Queue email notification to employee
    from app.models import Task
    notification_task = Task(
        name='leave_decision_notification',
        payload={
            'leave_request_id': request_id,
            'decision': 'rejected',
            'admin_notes': leave.admin_notes
        }
    )
    db.session.add(notification_task)
    db.session.commit()

    flash('Leave request rejected.', 'info')
    return redirect(url_for('admin.hr_leave_requests'))


@admin.route('/hr/leave-balances')
@login_required
@admin_required
def hr_leave_balances():
    """View and manage all employee leave balances."""
    from app.models import LeaveBalance
    from app.forms import LeaveBalanceAdjustForm
    
    current_year = datetime.utcnow().year
    
    balances = LeaveBalance.query.filter_by(year=current_year).order_by(LeaveBalance.user_id).all()
    
    # Group by user
    users_balances = {}
    for balance in balances:
        if balance.user_id not in users_balances:
            users_balances[balance.user_id] = {'user': balance.user, 'balances': []}
        users_balances[balance.user_id]['balances'].append(balance)
    
    form = LeaveBalanceAdjustForm()
    form.year.data = current_year
    
    return render_template('admin/hr/leave_balances.html', users_balances=users_balances, form=form, year=current_year)


@admin.route('/hr/leave-balances/adjust', methods=['POST'])
@login_required
@admin_required
def adjust_leave_balance():
    """Create or adjust leave balance for an employee."""
    from app.models import LeaveBalance
    from app.forms import LeaveBalanceAdjustForm
    
    form = LeaveBalanceAdjustForm()
    
    if form.validate_on_submit():
        balance = LeaveBalance.query.filter_by(
            user_id=form.user_id.data,
            leave_type=form.leave_type.data,
            year=form.year.data
        ).first()
        
        if balance:
            balance.balance_days = form.balance_days.data
            balance.carryover_days = form.carryover_days.data
        else:
            balance = LeaveBalance(
                user_id=form.user_id.data,
                leave_type=form.leave_type.data,
                year=form.year.data,
                balance_days=form.balance_days.data,
                carryover_days=form.carryover_days.data
            )
            db.session.add(balance)
        
        db.session.commit()
        
        log_audit_event(
            current_user.id,
            'adjust_leave_balance',
            'LeaveBalance',
            balance.id,
            {'user_id': form.user_id.data, 'type': form.leave_type.data, 'days': form.balance_days.data},
            request.remote_addr
        )
        
        flash('Leave balance updated successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('admin.hr_leave_balances'))


@admin.route('/hr/timesheets')
@login_required
@admin_required
def hr_timesheets():
    """View all employee timesheets."""
    from app.models import TimeEntry
    
    month = request.args.get('month', datetime.utcnow().month, type=int)
    year = request.args.get('year', datetime.utcnow().year, type=int)
    
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    entries = TimeEntry.query.filter(
        TimeEntry.date >= start_date,
        TimeEntry.date < end_date
    ).order_by(TimeEntry.user_id, TimeEntry.date.desc()).all()
    
    # Group by user
    users_entries = {}
    for entry in entries:
        if entry.user_id not in users_entries:
            users_entries[entry.user_id] = {'user': entry.user, 'entries': [], 'total_minutes': 0}
        users_entries[entry.user_id]['entries'].append(entry)
        users_entries[entry.user_id]['total_minutes'] += entry.duration_minutes or 0
    
    return render_template('admin/hr/timesheets.html', users_entries=users_entries, month=month, year=year)


@admin.route('/api/timecards')
@login_required
@admin_required
def api_timecards():
    """JSON API: Get all employee time cards with filtering."""
    from app.models import TimeEntry, User
    
    # Get filter parameters
    month = request.args.get('month', datetime.utcnow().month, type=int)
    year = request.args.get('year', datetime.utcnow().year, type=int)
    employee_id = request.args.get('employee_id', type=int)
    
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    # Build query
    query = TimeEntry.query.filter(
        TimeEntry.date >= start_date,
        TimeEntry.date < end_date
    )
    
    if employee_id:
        query = query.filter(TimeEntry.user_id == employee_id)
    
    entries = query.order_by(TimeEntry.user_id, TimeEntry.date.desc()).all()
    
    # Group by employee
    employees_data = {}
    for entry in entries:
        uid = entry.user_id
        if uid not in employees_data:
            user = entry.user
            employees_data[uid] = {
                'employee_id': uid,
                'employee_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
                'employee_email': user.email,
                'department': user.department or 'Unassigned',
                'entries': [],
                'total_minutes': 0,
                'days_worked': 0
            }
        
        employees_data[uid]['entries'].append({
            'id': entry.id,
            'date': entry.date.isoformat() if entry.date else None,
            'clock_in': entry.clock_in.strftime('%H:%M') if entry.clock_in else None,
            'clock_out': entry.clock_out.strftime('%H:%M') if entry.clock_out else None,
            'duration_minutes': entry.duration_minutes,
            'notes': entry.notes,
            'is_active': entry.clock_out is None
        })
        
        if entry.duration_minutes:
            employees_data[uid]['total_minutes'] += entry.duration_minutes
            employees_data[uid]['days_worked'] += 1
    
    # Calculate totals
    employees_list = list(employees_data.values())
    for emp in employees_list:
        emp['total_hours'] = round(emp['total_minutes'] / 60, 2)
        emp['avg_hours_per_day'] = round(emp['total_hours'] / emp['days_worked'], 2) if emp['days_worked'] else 0
    
    # Get list of all employees for filter dropdown
    all_employees = User.query.filter(
        User.roles.any(name='Employee')
    ).order_by(User.last_name, User.first_name).all()
    
    return jsonify({
        'month': month,
        'year': year,
        'month_name': ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December'][month - 1],
        'employees': employees_list,
        'available_employees': [
            {
                'id': emp.id,
                'name': f"{emp.first_name or ''} {emp.last_name or ''}".strip() or emp.username
            }
            for emp in all_employees
        ],
        'summary': {
            'total_employees': len(employees_list),
            'total_hours': sum(e['total_hours'] for e in employees_list),
            'total_entries': sum(len(e['entries']) for e in employees_list)
        }
    })


@admin.route('/api/timecards/export')
@login_required
@admin_required
def export_timecards():
    """Export time cards to CSV."""
    from app.models import TimeEntry
    import io
    import csv
    
    # Get filter parameters
    month = request.args.get('month', datetime.utcnow().month, type=int)
    year = request.args.get('year', datetime.utcnow().year, type=int)
    employee_id = request.args.get('employee_id', type=int)
    
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    # Build query
    query = TimeEntry.query.filter(
        TimeEntry.date >= start_date,
        TimeEntry.date < end_date
    )
    
    if employee_id:
        query = query.filter(TimeEntry.user_id == employee_id)
    
    entries = query.order_by(TimeEntry.user_id, TimeEntry.date.desc()).all()
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Employee', 'Email', 'Department', 'Date', 'Clock In', 'Clock Out', 'Hours', 'Notes'])
    
    for entry in entries:
        user = entry.user
        hours = round(entry.duration_minutes / 60, 2) if entry.duration_minutes else ''
        writer.writerow([
            f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
            user.email,
            user.department or '',
            entry.date.strftime('%Y-%m-%d') if entry.date else '',
            entry.clock_in.strftime('%H:%M') if entry.clock_in else '',
            entry.clock_out.strftime('%H:%M') if entry.clock_out else 'Active',
            hours,
            entry.notes or ''
        ])
    
    output.seek(0)
    month_names = ['january', 'february', 'march', 'april', 'may', 'june', 
                   'july', 'august', 'september', 'october', 'november', 'december']
    filename = f"timecards_{month_names[month-1]}_{year}.csv"
    
    log_audit_event(
        current_user.id, 
        'export_timecards', 
        'TimeEntry', 
        None, 
        {'month': month, 'year': year, 'count': len(entries)}, 
        request.remote_addr
    )
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@admin.route('/hr/org-chart')
@login_required
@admin_required
def hr_org_chart():
    """Admin view of organization chart with editing capabilities."""
    from app.models import User
    
    users = User.query.all()
    
    def build_tree(user):
        return {
            'id': user.id,
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
            'title': user.job_title or 'Employee',
            'department': user.department,
            'email': user.email,
            'children': [build_tree(report) for report in user.direct_reports]
        }
    
    roots = [u for u in users if not u.reports_to_id]
    org_data = [build_tree(root) for root in roots]
    
    return render_template('admin/hr/org_chart.html', org_data=org_data, users=users)


@admin.route('/hr/user/<int:user_id>/reporting', methods=['POST'])
@login_required
@admin_required
def update_reporting(user_id):
    """Update who a user reports to."""
    from app.models import User
    
    user = User.query.get_or_404(user_id)
    reports_to_id = request.form.get('reports_to_id', type=int)
    
    if reports_to_id == 0:
        user.reports_to_id = None
    else:
        # Prevent circular references
        if reports_to_id == user_id:
            flash('User cannot report to themselves.', 'error')
            return redirect(url_for('admin.hr_org_chart'))
        user.reports_to_id = reports_to_id
    
    user.job_title = request.form.get('job_title', user.job_title)
    user.department = request.form.get('department', user.department)
    
    db.session.commit()
    flash('Reporting structure updated.', 'success')
    return redirect(url_for('admin.hr_org_chart'))


# ============================================================================
# Employee Schedule Management
# ============================================================================

@admin.route('/schedule')
@login_required
@admin_required
def schedule_management():
    """Employee schedule management interface."""
    return render_template('admin/schedule.html')


# ============================================================================
# Phase 7: Admin Experience & Dashboard Enhancements
# ============================================================================

@admin.route('/dashboard/metrics')
@login_required
@admin_required
def dashboard_metrics():
    """API endpoint for dashboard KPI data with chart datasets."""
    # Get business timezone
    config_dict = {c.setting_name: c.setting_value for c in BusinessConfig.query.all()}
    company_timezone = pytz.timezone(config_dict.get('company_timezone', 'America/Denver'))
    now_utc = datetime.now(pytz.utc)
    now_local = now_utc.astimezone(company_timezone)
    
    # Get date range from query params (default: 30 days)
    days = request.args.get('days', 30, type=int)
    if days not in [7, 30, 90]:
        days = 30
    
    # Generate date labels and data for charts
    revenue_data = []
    leads_data = []
    labels = []
    
    for i in range(days - 1, -1, -1):
        day = now_local.date() - timedelta(days=i)
        day_start = company_timezone.localize(datetime.combine(day, time(0, 0, 0)))
        day_end = company_timezone.localize(datetime.combine(day + timedelta(days=1), time(0, 0, 0)))
        day_start_utc = day_start.astimezone(pytz.utc)
        day_end_utc = day_end.astimezone(pytz.utc)
        
        labels.append(day.strftime('%b %d'))
        
        # Revenue for this day
        rev_query = db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
            Order.status.in_(['paid', 'partially_paid', 'shipped', 'delivered']),
            Order.created_at >= day_start_utc,
            Order.created_at < day_end_utc
        )
        if current_user.location_id:
            rev_query = rev_query.filter(Order.location_id == current_user.location_id)
        revenue_data.append(float(rev_query.scalar() or 0) / 100)  # Convert cents to dollars
        
        # Leads for this day
        leads_query = ContactFormSubmission.query.filter(
            ContactFormSubmission.submitted_at >= day_start_utc,
            ContactFormSubmission.submitted_at < day_end_utc
        )
        if current_user.location_id:
            leads_query = leads_query.filter(ContactFormSubmission.location_id == current_user.location_id)
        leads_data.append(leads_query.count())
    
    # Lead funnel data (pipeline stages)
    funnel_stages = [
        {'name': 'New', 'status': 'New', 'color': '#6c757d'},
        {'name': 'Contacted', 'status': 'Contacted', 'color': '#17a2b8'},
        {'name': 'Qualified', 'status': 'Qualified', 'color': '#ffc107'},
        {'name': 'Proposal', 'status': 'Proposal', 'color': '#fd7e14'},
        {'name': 'Won', 'status': 'Won', 'color': '#28a745'},
        {'name': 'Lost', 'status': 'Lost', 'color': '#dc3545'}
    ]
    
    funnel_data = []
    for stage in funnel_stages:
        query = ContactFormSubmission.query.filter_by(status=stage['status'])
        if current_user.location_id:
            query = query.filter(ContactFormSubmission.location_id == current_user.location_id)
        funnel_data.append({
            'name': stage['name'],
            'count': query.count(),
            'color': stage['color']
        })
    
    return jsonify({
        'labels': labels,
        'revenue': revenue_data,
        'leads': leads_data,
        'funnel': funnel_data,
        'days': days
    })


@admin.route('/search')
@login_required
@admin_required
def admin_search():
    """Global search across users, orders, leads, and posts."""
    q = request.args.get('q', '').strip()
    
    if not q or len(q) < 2:
        return render_template('admin/search.html', query=q, results=None)
    
    search_term = f'%{q}%'
    results = {
        'users': [],
        'leads': [],
        'orders': [],
        'posts': []
    }
    
    # Search users
    users_query = User.query.filter(
        db.or_(
            User.username.ilike(search_term),
            User.email.ilike(search_term),
            User.first_name.ilike(search_term),
            User.last_name.ilike(search_term)
        )
    )
    if current_user.location_id:
        users_query = users_query.filter(User.location_id == current_user.location_id)
    results['users'] = users_query.limit(10).all()
    
    # Search leads (ContactFormSubmission)
    leads_query = ContactFormSubmission.query.filter(
        db.or_(
            ContactFormSubmission.email.ilike(search_term),
            ContactFormSubmission.first_name.ilike(search_term),
            ContactFormSubmission.last_name.ilike(search_term),
            ContactFormSubmission.phone.ilike(search_term)
        )
    )
    if current_user.location_id:
        leads_query = leads_query.filter(ContactFormSubmission.location_id == current_user.location_id)
    results['leads'] = leads_query.limit(10).all()
    
    # Search orders
    orders_query = Order.query.filter(
        db.or_(
            Order.id.ilike(search_term) if q.isdigit() else False,
            Order.shipping_address.ilike(search_term)
        )
    )
    if current_user.location_id:
        orders_query = orders_query.filter(Order.location_id == current_user.location_id)
    results['orders'] = orders_query.limit(10).all()
    
    # Search posts
    posts_query = Post.query.filter(
        db.or_(
            Post.title.ilike(search_term),
            Post.slug.ilike(search_term)
        )
    )
    results['posts'] = posts_query.limit(10).all()
    
    total_count = sum(len(v) for v in results.values())
    
    return render_template('admin/search.html', query=q, results=results, total_count=total_count)


@admin.route('/users/bulk', methods=['POST'])
@login_required
@admin_required
def bulk_user_action():
    """Bulk actions for users: delete, deactivate, assign role."""
    user_ids = request.form.getlist('user_ids[]', type=int)
    action = request.form.get('action', '')
    
    if not user_ids:
        flash('No users selected.', 'warning')
        return redirect(url_for('admin.list_users'))
    
    if action == 'delete':
        count = 0
        for uid in user_ids:
            if uid != current_user.id:  # Can't delete yourself
                user = User.query.get(uid)
                if user:
                    db.session.delete(user)
                    count += 1
        db.session.commit()
        log_audit_event(current_user.id, 'bulk_delete_users', 'User', None, {'count': count}, request.remote_addr)
        flash(f'Deleted {count} users.', 'success')
        
    elif action == 'deactivate':
        count = User.query.filter(User.id.in_(user_ids)).update({'is_active': False}, synchronize_session=False)
        db.session.commit()
        log_audit_event(current_user.id, 'bulk_deactivate_users', 'User', None, {'count': count}, request.remote_addr)
        flash(f'Deactivated {count} users.', 'success')
        
    elif action == 'activate':
        count = User.query.filter(User.id.in_(user_ids)).update({'is_active': True}, synchronize_session=False)
        db.session.commit()
        log_audit_event(current_user.id, 'bulk_activate_users', 'User', None, {'count': count}, request.remote_addr)
        flash(f'Activated {count} users.', 'success')
        
    elif action.startswith('add_role_'):
        role_id = int(action.replace('add_role_', ''))
        role = Role.query.get(role_id)
        if role:
            count = 0
            for uid in user_ids:
                user = User.query.get(uid)
                if user and role not in user.roles:
                    user.roles.append(role)
                    count += 1
            db.session.commit()
            log_audit_event(current_user.id, 'bulk_add_role', 'User', None, {'role': role.name, 'count': count}, request.remote_addr)
            flash(f'Added role "{role.name}" to {count} users.', 'success')
    else:
        flash('Unknown action.', 'error')
    
    return redirect(url_for('admin.list_users'))


@admin.route('/users/export/csv')
@login_required
@admin_required
def export_users_csv():
    """Export users list as CSV."""
    users_query = User.query
    if current_user.location_id:
        users_query = users_query.filter(User.location_id == current_user.location_id)
    users = users_query.order_by(User.username).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Phone', 'Roles', 'Created At', 'Last Login'])
    
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.first_name or '',
            user.last_name or '',
            user.phone or '',
            ', '.join([r.name for r in user.roles]),
            user.date.strftime('%Y-%m-%d %H:%M:%S') if user.date else '',
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else ''
        ])
    
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_audit_event(current_user.id, 'export_users_csv', 'User', None, {'count': len(users)}, request.remote_addr)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=users_export_{timestamp}.csv'}
    )


@admin.route('/orders/export/csv')
@login_required
@admin_required
def export_orders_csv():
    """Export orders list as CSV."""
    orders_query = Order.query
    if current_user.location_id:
        orders_query = orders_query.filter(Order.location_id == current_user.location_id)
    orders = orders_query.order_by(Order.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order ID', 'Status', 'Total (USD)', 'Items', 'Customer ID', 'Created At', 'Tracking'])
    
    for order in orders:
        writer.writerow([
            order.id,
            order.status,
            f'{order.total_amount / 100:.2f}',
            len(order.items),
            order.user_id or 'Guest',
            order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '',
            order.tracking_number or ''
        ])
    
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_audit_event(current_user.id, 'export_orders_csv', 'Order', None, {'count': len(orders)}, request.remote_addr)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=orders_export_{timestamp}.csv'}
    )


@admin.route('/leads/export/csv')
@login_required
@admin_required
def export_leads_csv():
    """Export leads (contact form submissions) as CSV."""
    leads_query = ContactFormSubmission.query
    if current_user.location_id:
        leads_query = leads_query.filter(ContactFormSubmission.location_id == current_user.location_id)
    leads = leads_query.order_by(ContactFormSubmission.submitted_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Message', 'Status', 'Source', 'Submitted At'])
    
    for lead in leads:
        writer.writerow([
            lead.id,
            lead.first_name or '',
            lead.last_name or '',
            lead.email or '',
            lead.phone or '',
            (lead.message or '')[:200],  # Truncate long messages
            lead.status or 'New',
            lead.source or '',
            lead.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if lead.submitted_at else ''
        ])
    
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_audit_event(current_user.id, 'export_leads_csv', 'ContactFormSubmission', None, {'count': len(leads)}, request.remote_addr)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=leads_export_{timestamp}.csv'}
    )


# ============================================================================
# Phase 9: Webhook Management
# ============================================================================

@admin.route('/webhooks')
@login_required
@admin_required
def webhooks():
    """List all outbound webhooks."""
    import json
    from app.models import Webhook
    from app.forms import CSRFTokenForm
    webhooks = Webhook.query.order_by(Webhook.created_at.desc()).all()
    form = CSRFTokenForm()
    
    # Serialize for AdminDataTable
    webhooks_json = json.dumps([{
        'id': wh.id,
        'name': f'<strong>{wh.name}</strong>',
        'url': f'<code class="small">{wh.url[:50]}{"..." if len(wh.url) > 50 else ""}</code>',
        'events': ' '.join([f'<span class="badge bg-secondary">{e}</span>' for e in (wh.events or [])]),
        'status': '<span class="badge bg-success">Active</span>' if wh.is_active else '<span class="badge bg-danger">Inactive</span>',
        'last_triggered': (wh.last_triggered_at.strftime('%Y-%m-%d %H:%M') + (f' <span class="badge bg-{"success" if 200 <= (wh.last_status_code or 0) < 300 else "warning"}">{wh.last_status_code}</span>' if wh.last_status_code else '')) if wh.last_triggered_at else '<span class="text-muted">Never</span>',
        'failures': f'<span class="badge bg-warning">{wh.failure_count}</span>' if wh.failure_count > 0 else '<span class="text-muted">0</span>',
        'actions': f'''<a href="{url_for('admin.webhook_edit', id=wh.id)}" class="btn btn-sm btn-outline-primary"><i class="fas fa-edit"></i></a>
            <form action="{url_for('admin.webhook_toggle', id=wh.id)}" method="POST" class="d-inline"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}"><button type="submit" class="btn btn-sm btn-outline-{'warning' if wh.is_active else 'success'}" title="{'Deactivate' if wh.is_active else 'Activate'}"><i class="fas fa-{'pause' if wh.is_active else 'play'}"></i></button></form>
            <form action="{url_for('admin.webhook_test', id=wh.id)}" method="POST" class="d-inline"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}"><button type="submit" class="btn btn-sm btn-outline-info" title="Test"><i class="fas fa-paper-plane"></i></button></form>
            <form action="{url_for('admin.webhook_delete', id=wh.id)}" method="POST" class="d-inline" onsubmit="return confirm('Delete?');"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}"><button type="submit" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button></form>'''
    } for wh in webhooks])
    
    return render_template('admin/api/webhooks.html', webhooks=webhooks, webhooks_json=webhooks_json)


@admin.route('/webhooks/new')
@login_required
@admin_required
def webhook_new():
    """New webhook form."""
    return render_template('admin/api/webhook_form.html', webhook=None)


@admin.route('/webhooks/<int:id>/edit')
@login_required
@admin_required
def webhook_edit(id):
    """Edit webhook form."""
    from app.models import Webhook
    webhook = Webhook.query.get_or_404(id)
    return render_template('admin/api/webhook_form.html', webhook=webhook)


@admin.route('/webhooks/save', methods=['POST'])
@admin.route('/webhooks/<int:id>/save', methods=['POST'])
@login_required
@admin_required
def webhook_save(id=None):
    """Create or update a webhook."""
    from app.models import Webhook
    
    if id:
        webhook = Webhook.query.get_or_404(id)
    else:
        webhook = Webhook()
    
    webhook.name = request.form.get('name')
    webhook.url = request.form.get('url')
    webhook.events = request.form.getlist('events')
    webhook.is_active = request.form.get('is_active') == 'on'
    
    if not id:
        # New webhook - set secret
        secret = request.form.get('secret')
        if not secret:
            import secrets as sec
            secret = sec.token_hex(32)
        webhook.secret = secret
        webhook.created_by_id = current_user.id
        db.session.add(webhook)
    
    try:
        db.session.commit()
        log_audit_event(current_user.id, 'save_webhook', 'Webhook', webhook.id, 
                       {'name': webhook.name, 'events': webhook.events}, request.remote_addr)
        flash('Webhook saved successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving webhook: {e}', 'error')
    
    return redirect(url_for('admin.webhooks'))


@admin.route('/webhooks/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def webhook_toggle(id):
    """Toggle webhook active status."""
    from app.models import Webhook
    webhook = Webhook.query.get_or_404(id)
    webhook.is_active = not webhook.is_active
    webhook.failure_count = 0  # Reset failures on reactivation
    db.session.commit()
    
    status = 'activated' if webhook.is_active else 'deactivated'
    log_audit_event(current_user.id, f'webhook_{status}', 'Webhook', id, 
                   {'name': webhook.name}, request.remote_addr)
    flash(f'Webhook {status}.', 'success')
    return redirect(url_for('admin.webhooks'))


@admin.route('/webhooks/<int:id>/test', methods=['POST'])
@login_required
@admin_required
def webhook_test(id):
    """Send a test webhook."""
    from app.models import Webhook, Task
    webhook = Webhook.query.get_or_404(id)
    
    # Create a task to send test webhook
    test_task = Task(
        name='send_webhook',
        payload={
            'webhook_id': webhook.id,
            'event': 'test.ping',
            'data': {
                'message': 'This is a test webhook from Verso',
                'webhook_name': webhook.name,
                'timestamp': datetime.utcnow().isoformat()
            },
            'url': webhook.url,
            'secret': webhook.secret
        },
        priority=8  # High priority for test
    )
    db.session.add(test_task)
    db.session.commit()
    
    flash('Test webhook queued. Check your endpoint shortly.', 'info')
    return redirect(url_for('admin.webhooks'))


@admin.route('/webhooks/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def webhook_delete(id):
    """Delete a webhook."""
    from app.models import Webhook
    webhook = Webhook.query.get_or_404(id)
    name = webhook.name
    
    db.session.delete(webhook)
    db.session.commit()
    
    log_audit_event(current_user.id, 'delete_webhook', 'Webhook', id, 
                   {'name': name}, request.remote_addr)
    flash('Webhook deleted.', 'success')
    return redirect(url_for('admin.webhooks'))


# ============================================================================
# Phase 11: Admin Command Center Dashboards
# ============================================================================

@admin.route('/dashboard/owner')
@login_required
@admin_required
def owner_dashboard():
    """Executive owner dashboard with high-level revenue and performance metrics."""
    config_dict = {c.setting_name: c.setting_value for c in BusinessConfig.query.all()}
    company_timezone = pytz.timezone(config_dict.get('company_timezone', 'America/Denver'))
    now_utc = datetime.now(pytz.utc)
    now_local = now_utc.astimezone(company_timezone)
    
    # Date ranges
    month_start = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_utc = month_start.astimezone(pytz.utc)
    year_start = now_local.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start_utc = year_start.astimezone(pytz.utc)
    
    # Location filter
    location_filter = {}
    if current_user.location_id and not current_user.has_role('super_admin'):
        location_filter['location_id'] = current_user.location_id
    
    # Revenue metrics
    revenue_mtd = db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
        Order.status.in_(['paid', 'shipped', 'delivered']),
        Order.created_at >= month_start_utc
    ).scalar() or 0
    
    revenue_ytd = db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
        Order.status.in_(['paid', 'shipped', 'delivered']),
        Order.created_at >= year_start_utc
    ).scalar() or 0
    
    # Order counts
    orders_mtd = Order.query.filter(
        Order.status.in_(['paid', 'shipped', 'delivered']),
        Order.created_at >= month_start_utc
    ).count()
    
    orders_ytd = Order.query.filter(
        Order.status.in_(['paid', 'shipped', 'delivered']),
        Order.created_at >= year_start_utc
    ).count()
    
    # Lead metrics
    leads_mtd = ContactFormSubmission.query.filter(
        ContactFormSubmission.submitted_at >= month_start_utc
    ).count()
    
    leads_ytd = ContactFormSubmission.query.filter(
        ContactFormSubmission.submitted_at >= year_start_utc
    ).count()
    
    # Conversion rate (leads to paid orders)
    total_leads = ContactFormSubmission.query.count()
    paid_orders = Order.query.filter(Order.status.in_(['paid', 'shipped', 'delivered'])).count()
    conversion_rate = (paid_orders / total_leads * 100) if total_leads > 0 else 0
    
    # Top products (by revenue)
    from app.models import OrderItem, Product
    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('qty'),
        func.sum(OrderItem.price_at_purchase * OrderItem.quantity).label('revenue')
    ).join(OrderItem.product).join(OrderItem.order).filter(
        Order.status.in_(['paid', 'shipped', 'delivered']),
        Order.created_at >= month_start_utc
    ).group_by(Product.id).order_by(func.sum(OrderItem.price_at_purchase * OrderItem.quantity).desc()).limit(5).all()
    
    # Average order value
    avg_order_value = revenue_mtd / orders_mtd if orders_mtd > 0 else 0
    
    kpis = {
        'revenue_mtd': revenue_mtd,
        'revenue_ytd': revenue_ytd,
        'orders_mtd': orders_mtd,
        'orders_ytd': orders_ytd,
        'leads_mtd': leads_mtd,
        'leads_ytd': leads_ytd,
        'conversion_rate': round(conversion_rate, 1),
        'avg_order_value': avg_order_value,
        'top_products': top_products
    }
    
    return render_template('admin/dashboards/owner.html', kpis=kpis)


@admin.route('/dashboard/operations')
@login_required
@admin_required
def operations_dashboard():
    """Operations dashboard with daily logistics, tasks, and staff management."""
    config_dict = {c.setting_name: c.setting_value for c in BusinessConfig.query.all()}
    company_timezone = pytz.timezone(config_dict.get('company_timezone', 'America/Denver'))
    now_utc = datetime.now(pytz.utc)
    now_local = now_utc.astimezone(company_timezone)
    
    today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_utc = today_start.astimezone(pytz.utc)
    tomorrow_start = today_start + timedelta(days=1)
    tomorrow_start_utc = tomorrow_start.astimezone(pytz.utc)
    
    # Today's appointments
    todays_appointments = Appointment.query.filter(
        Appointment.preferred_date_time >= today_start_utc,
        Appointment.preferred_date_time < tomorrow_start_utc
    ).order_by(Appointment.preferred_date_time.asc()).all()
    
    # Add local time
    for appt in todays_appointments:
        if appt.preferred_date_time:
            utc_time = appt.preferred_date_time.replace(tzinfo=pytz.utc)
            appt.local_time = utc_time.astimezone(company_timezone)
    
    # Pending tasks from background worker
    from app.models import Task
    pending_tasks = Task.query.filter_by(status='pending').order_by(Task.created_at.desc()).limit(20).all()
    failed_tasks = Task.query.filter_by(status='failed').order_by(Task.created_at.desc()).limit(10).all()
    
    # Leave requests pending approval
    from app.models import LeaveRequest
    pending_leave = LeaveRequest.query.filter_by(status='pending').order_by(LeaveRequest.created_at.desc()).all()
    
    # Reschedule requests
    from app.models import RescheduleRequest
    pending_reschedules = RescheduleRequest.query.filter_by(status='pending').order_by(RescheduleRequest.created_at.desc()).all()
    
    # Orders needing fulfillment
    unfulfilled_orders = Order.query.filter(
        Order.status == 'paid',
        Order.fulfillment_status == 'unfulfilled'
    ).order_by(Order.created_at.asc()).limit(20).all()
    
    # Staff on leave today
    staff_on_leave = []
    approved_leave = LeaveRequest.query.filter(
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= today_start.date(),
        LeaveRequest.end_date >= today_start.date()
    ).all()
    for leave in approved_leave:
        if leave.user:
            staff_on_leave.append(leave.user)
    
    data = {
        'todays_appointments': todays_appointments,
        'pending_tasks': pending_tasks,
        'failed_tasks': failed_tasks,
        'pending_leave': pending_leave,
        'pending_reschedules': pending_reschedules,
        'unfulfilled_orders': unfulfilled_orders,
        'staff_on_leave': staff_on_leave,
        'today': today_start.strftime('%A, %B %d, %Y')
    }
    
    return render_template('admin/dashboards/operations.html', data=data)


@admin.route('/dashboard/sales')
@login_required
@admin_required
def sales_dashboard():
    """Sales and marketing dashboard with pipeline, conversion, and lead metrics."""
    config_dict = {c.setting_name: c.setting_value for c in BusinessConfig.query.all()}
    company_timezone = pytz.timezone(config_dict.get('company_timezone', 'America/Denver'))
    now_utc = datetime.now(pytz.utc)
    now_local = now_utc.astimezone(company_timezone)
    
    month_start = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_utc = month_start.astimezone(pytz.utc)
    
    # Lead funnel
    new_leads = ContactFormSubmission.query.filter(
        ContactFormSubmission.status == 'new'
    ).count()
    contacted_leads = ContactFormSubmission.query.filter(
        ContactFormSubmission.status == 'contacted'
    ).count()
    qualified_leads = ContactFormSubmission.query.filter(
        ContactFormSubmission.status == 'qualified'
    ).count()
    won_leads = ContactFormSubmission.query.filter(
        ContactFormSubmission.status == 'won'
    ).count()
    lost_leads = ContactFormSubmission.query.filter(
        ContactFormSubmission.status == 'lost'
    ).count()
    
    # Build funnel data
    funnel = [
        {'name': 'New', 'count': new_leads, 'color': '#17a2b8'},
        {'name': 'Contacted', 'count': contacted_leads, 'color': '#6f42c1'},
        {'name': 'Qualified', 'count': qualified_leads, 'color': '#fd7e14'},
        {'name': 'Won', 'count': won_leads, 'color': '#28a745'},
        {'name': 'Lost', 'count': lost_leads, 'color': '#dc3545'}
    ]
    
    # Hot leads (recent with high engagement)
    from app.models import FollowUpReminder
    hot_leads = ContactFormSubmission.query.filter(
        ContactFormSubmission.status.in_(['new', 'contacted', 'qualified']),
        ContactFormSubmission.submitted_at >= month_start_utc
    ).order_by(ContactFormSubmission.submitted_at.desc()).limit(10).all()
    
    # Follow-up reminders due today or overdue
    today = now_local.date()
    due_reminders = FollowUpReminder.query.filter(
        FollowUpReminder.status == 'pending',
        FollowUpReminder.due_date <= datetime.combine(today, datetime.max.time())
    ).order_by(FollowUpReminder.due_date.asc()).all()
    
    # This month's conversions
    conversions_mtd = ContactFormSubmission.query.filter(
        ContactFormSubmission.status == 'won',
        ContactFormSubmission.submitted_at >= month_start_utc
    ).count()
    
    # Response time average (placeholder - would need more tracking)
    
    data = {
        'funnel': funnel,
        'hot_leads': hot_leads,
        'due_reminders': due_reminders,
        'conversions_mtd': conversions_mtd,
        'total_pipeline': new_leads + contacted_leads + qualified_leads
    }
    
    return render_template('admin/dashboards/sales.html', data=data)