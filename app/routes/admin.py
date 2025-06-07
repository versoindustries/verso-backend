# app/routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response, jsonify
from flask_login import login_required, current_user
from app.modules.auth_manager import admin_required  # Assuming you have an admin_required decorator
from app.models import User, Estimator, Service, Appointment, ContactFormSubmission, Role
from app.forms import ManageRolesForm, EditUserForm, EstimatorForm, EstimateRequestForm, ServiceOptionForm, CSRFTokenForm
from app.database import db
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date, time, timedelta
from app.modules.indexing import generate_sitemap, submit_sitemap_to_bing
from app import csrf
from datetime import datetime, timedelta, timezone, time
import pytz

admin = Blueprint('admin', __name__, template_folder='templates')

@admin.context_processor
def combined_context_processor():
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form, hide_estimate_form=True)

@admin.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Fetch necessary data for the dashboard
    total_users = User.query.count()
    contact_form_submissions = ContactFormSubmission.query.order_by(ContactFormSubmission.submitted_at.desc()).all()

    # Fetch appointments within current month
    company_timezone = pytz.timezone('America/Denver')
    now_local = datetime.now(company_timezone)

    # Get the first day of the current month
    first_day = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get the first day of the next month
    if now_local.month == 12:
        next_month = now_local.replace(year=now_local.year+1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        next_month = now_local.replace(month=now_local.month+1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # Convert to UTC
    first_day_utc = first_day.astimezone(pytz.utc)
    next_month_utc = next_month.astimezone(pytz.utc)

    # Query appointments in this date range
    appointments = Appointment.query.filter(
        Appointment.preferred_date_time >= first_day_utc,
        Appointment.preferred_date_time < next_month_utc
    ).order_by(Appointment.preferred_date_time.asc()).all()

    # Convert appointment times to company's timezone (America/Denver)
    for appointment in appointments:
        if appointment.preferred_date_time:
            # Assuming preferred_date_time is stored in UTC
            utc_time = appointment.preferred_date_time.replace(tzinfo=pytz.utc)
            appointment.local_time = utc_time.astimezone(company_timezone)
        else:
            appointment.local_time = None

    form = CSRFTokenForm()  # Create an instance of the CSRFTokenForm

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        contact_form_submissions=contact_form_submissions,
        appointments=appointments,
        form=form
    )

@admin.route('/manage-roles/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_roles(user_id):
    user = User.query.get_or_404(user_id)
    form = ManageRolesForm(obj=user)

    if form.validate_on_submit():
        user.roles = form.roles.data
        db.session.commit()
        flash('User roles updated successfully.', 'success')
        return redirect(url_for('admin.user_management'))

    return render_template('manage_roles.html', form=form, user=user)

@admin.route('/estimator', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_estimator():
    form = EstimatorForm()
    if form.validate_on_submit():
        estimator = Estimator(name=form.name.data)
        db.session.add(estimator)
        db.session.commit()
        return redirect(url_for('admin.admin_dashboard'))  # Redirect to admin dashboard

    # Query all estimators
    estimators = Estimator.query.all()
    
    return render_template('admin/estimator_form.html', hide_estimate_form=True, form=form, estimators=estimators)

@admin.route('/estimator/delete/<int:estimator_id>', methods=['POST'])
@login_required
@admin_required
def delete_estimator(estimator_id):
    """Delete an estimator record by ID."""
    current_app.logger.debug(f'Attempting to delete estimator with ID: {estimator_id}')
    
    estimator = Estimator.query.get_or_404(estimator_id)
    
    try:
        # Check if the estimator is associated with any appointments
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

        # Add the new Service instance to the session
        db.session.add(service)
        
        try:
            # Commit the session to save changes to the database
            db.session.commit()
            current_app.logger.debug('New Service added to the database successfully.')
            
            # Flash a success message
            flash('Service added successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding Service to the database: {e}')
            flash('Error adding Service. Please try again.', 'error')

        # Redirect to the 'admin.services' route
        return redirect(url_for('admin.services'))
    else:
        if form.errors:
            current_app.logger.debug(f'Form validation errors: {form.errors}')

    # Query all Service instances, ordered by display_order
    services = Service.query.order_by(Service.display_order).all()
    current_app.logger.debug(f'Loaded {len(services)} Services for display.')

    # Render the 'admin/service.html' template
    return render_template('admin/service.html', hide_estimate_form=True, form=form, services=services)

@admin.route('/service/delete/<int:service_id>', methods=['POST'])
@login_required
@admin_required
def delete_service(service_id):
    """Delete a service record by ID."""
    current_app.logger.debug(f'Attempting to delete service with ID: {service_id}')
    
    service = Service.query.get_or_404(service_id)
    
    try:
        # Check if the service is associated with any appointments
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
        # Call the generate_sitemap function to create the sitemap
        generate_sitemap(current_app)
        flash('Sitemap generated and saved successfully.', 'success')
        
        # Optionally, submit the sitemap to Bing or any other search engine
        # submit_sitemap_to_bing('http://www.yourdomain.com/static/sitemap.xml')
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
        'end': (appointment.preferred_date_time + timedelta(hours=1)).replace(tzinfo=pytz.utc).isoformat()  # Assuming each appointment lasts 1 hour
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

@admin.route('/user-management', methods=['GET', 'POST'])
@login_required
@admin_required
def user_management():
    """Manage users with filtering, sorting, and bulk actions."""
    current_app.logger.debug('Accessing user management route')
    
    form = CSRFTokenForm()
    
    # Handle filtering and sorting
    search_query = request.args.get('search', '', type=str).strip()
    sort_by = request.args.get('sort', 'username', type=str)
    sort_order = request.args.get('order', 'asc', type=str)
    
    # Build query
    query = User.query
    
    if search_query:
        query = query.filter(
            (User.username.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%')) |
            (User.first_name.ilike(f'%{search_query}%')) |
            (User.last_name.ilike(f'%{search_query}%'))
        )
    
    # Apply sorting
    if sort_by == 'email':
        query = query.order_by(User.email.asc() if sort_order == 'asc' else User.email.desc())
    elif sort_by == 'name':
        query = query.order_by(User.last_name.asc() if sort_order == 'asc' else User.last_name.desc())
    else:
        query = query.order_by(User.username.asc() if sort_order == 'asc' else User.username.desc())
    
    # Handle bulk actions (POST request)
    if request.method == 'POST' and form.validate_on_submit():
        action = request.form.get('action')
        user_ids = request.form.getlist('selected_users')
        
        try:
            if action == 'assign_role' and user_ids:
                role_id = request.form.get('role_id')
                role = Role.query.get_or_404(role_id)
                for user_id in user_ids:
                    user = User.query.get_or_404(user_id)
                    if not user.has_role(role.name):
                        user.add_role(role)
                db.session.commit()
                flash(f'Role "{role.name}" assigned to selected users.', 'success')
                current_app.logger.info(f'Bulk role assignment: Role {role.name} to users {user_ids}')
            
            elif action == 'remove_role' and user_ids:
                role_id = request.form.get('role_id')
                role = Role.query.get_or_404(role_id)
                for user_id in user_ids:
                    user = User.query.get_or_404(user_id)
                    if user.has_role(role.name):
                        user.remove_role(role)
                db.session.commit()
                flash(f'Role "{role.name}" removed from selected users.', 'success')
                current_app.logger.info(f'Bulk role removal: Role {role.name} from users {user_ids}')
            
            elif action == 'delete' and user_ids:
                for user_id in user_ids:
                    user = User.query.get_or_404(user_id)
                    if user.id != current_user.id:  # Prevent self-deletion
                        db.session.delete(user)
                db.session.commit()
                flash('Selected users deleted successfully.', 'success')
                current_app.logger.info(f'Bulk user deletion: Users {user_ids}')
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Error performing bulk action. Please try again.', 'error')
            current_app.logger.error(f'Bulk action error: {e}')
    
    users = query.all()
    roles = Role.query.all()
    
    return render_template(
        'admin/user_management.html',
        users=users,
        roles=roles,
        form=form,
        search_query=search_query,
        sort_by=sort_by,
        sort_order=sort_order
    )