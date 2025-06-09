from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response, jsonify
from flask_login import login_required, current_user
from app.modules.auth_manager import admin_required
from app.models import User, Estimator, Service, Appointment, ContactFormSubmission, Role, BusinessConfig
from app.forms import ManageRolesForm, EditUserForm, EstimatorForm, EstimateRequestForm, ServiceOptionForm, CSRFTokenForm, CreateUserForm, RoleForm, BusinessConfigForm
from app.database import db
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date, time, timedelta
from app.modules.indexing import generate_sitemap, submit_sitemap_to_bing
from app import csrf
from datetime import datetime, timedelta, timezone, time
import pytz
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

admin = Blueprint('admin', __name__, template_folder='templates')

@admin.context_processor
def combined_context_processor():
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form, hide_estimate_form=True)

@admin.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    contact_form_submissions = ContactFormSubmission.query.order_by(ContactFormSubmission.submitted_at.desc()).all()
    company_timezone = pytz.timezone('America/Denver')
    now_local = datetime.now(company_timezone)
    first_day = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now_local.month == 12:
        next_month = now_local.replace(year=now_local.year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        next_month = now_local.replace(month=now_local.month+1, day=1, hour=0, minute=0, second=0, microsecond=0)
    first_day_utc = first_day.astimezone(pytz.utc)
    next_month_utc = next_month.astimezone(pytz.utc)
    appointments = Appointment.query.filter(
        Appointment.preferred_date_time >= first_day_utc,
        Appointment.preferred_date_time < next_month_utc
    ).order_by(Appointment.preferred_date_time.asc()).all()
    for appointment in appointments:
        if appointment.preferred_date_time:
            utc_time = appointment.preferred_date_time.replace(tzinfo=pytz.utc)
            appointment.local_time = utc_time.astimezone(company_timezone)
        else:
            appointment.local_time = None
    form = CSRFTokenForm()
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        contact_form_submissions=contact_form_submissions,
        appointments=appointments,
        form=form
    )

@admin.route('/users')
@login_required
@admin_required
def list_users():
    users = User.query.order_by(User.username).all()
    form = CSRFTokenForm()  # Initialize the CSRF form
    return render_template('admin/list_users.html', users=users, form=form)

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
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.list_users'))

@admin.route('/roles')
@login_required
@admin_required
def list_roles():
    roles = Role.query.all()
    form = CSRFTokenForm()  # Initialize the CSRF form
    return render_template('admin/list_roles.html', roles=roles, form=form)

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

@admin.route('/estimator', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_estimator():
    form = EstimatorForm()
    if form.validate_on_submit():
        estimator = Estimator(name=form.name.data)
        db.session.add(estimator)
        db.session.commit()
        return redirect(url_for('admin.admin_dashboard'))
    estimators = Estimator.query.all()
    return render_template('admin/estimator_form.html', hide_estimate_form=True, form=form, estimators=estimators)

@admin.route('/estimator/delete/<int:estimator_id>', methods=['POST'])
@login_required
@admin_required
def delete_estimator(estimator_id):
    current_app.logger.debug(f'Attempting to delete estimator with ID: {estimator_id}')
    estimator = Estimator.query.get_or_404(estimator_id)
    try:
        if estimator.appointments:
            flash('Cannot delete estimator because they are assigned to appointments.', 'error')
            return redirect(url_for('admin.admin_estimator'))
        db.session.delete(estimator)
        db.session.commit()
        current_app.logger.info(f'Estimator ID {estimator_id} deleted successfully.')
        flash('Estimator deleted successfully.', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting estimator ID {estimator_id}: {e}')
        flash('Error deleting estimator. Please try again.', 'error')
    return redirect(url_for('admin.admin_estimator'))

@admin.route('/service', methods=['GET', 'POST'])
@login_required
@admin_required
def services():
    form = ServiceOptionForm()
    if form.validate_on_submit():
        current_app.logger.debug('Form validated successfully.')
        service = Service(
            name=form.name.data, 
            description=form.description.data, 
            display_order=form.display_order.data
        )
        current_app.logger.debug(f'Creating new Service: {service.name}')
        db.session.add(service)
        try:
            db.session.commit()
            current_app.logger.debug('New Service added to the database successfully.')
            flash('Service added successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding Service to the database: {e}')
            flash('Error adding Service. Please try again.', 'error')
        return redirect(url_for('admin.services'))
    else:
        if form.errors:
            current_app.logger.debug(f'Form validation errors: {form.errors}')
    services = Service.query.order_by(Service.display_order).all()
    current_app.logger.debug(f'Loaded {len(services)} Services for display.')
    return render_template('admin/service.html', hide_estimate_form=True, form=form, services=services)

@admin.route('/service/delete/<int:service_id>', methods=['POST'])
@login_required
@admin_required
def delete_service(service_id):
    current_app.logger.debug(f'Attempting to delete service with ID: {service_id}')
    service = Service.query.get_or_404(service_id)
    try:
        if service.appointments:
            flash('Cannot delete service because it is associated with appointments.', 'error')
            return redirect(url_for('admin.services'))
        db.session.delete(service)
        db.session.commit()
        current_app.logger.info(f'Service ID {service_id} deleted successfully.')
        flash('Service deleted successfully.', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting service ID {service_id}: {e}')
        flash('Error deleting service. Please try again.', 'error')
    return redirect(url_for('admin.services'))

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
                'company_timezone': form.company_timezone.data
            }
            for name, value in settings.items():
                config = BusinessConfig.query.filter_by(setting_name=name).first()
                if config:
                    config.setting_value = value
                else:
                    config = BusinessConfig(setting_name=name, setting_value=value)
                    db.session.add(config)
            db.session.commit()
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

    return render_template('admin/business_config.html', form=form, hide_estimate_form=True)