"""
Booking Admin API Routes

API endpoints for the unified booking admin dashboard.
Supports CRUD operations for services, staff (from employees), and other booking entities.
"""

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from app.modules.auth_manager import admin_required
from app.database import db
from app.models import (
    Service, Estimator, User, Role, AppointmentType, Resource, Availability, BusinessConfig,
    Appointment, RescheduleRequest
)
from datetime import time, datetime, timedelta
import pytz

# Blueprint for API routes (prefix: /api/admin/booking)
booking_admin_bp = Blueprint('booking_admin', __name__, url_prefix='/api/admin/booking')

# Blueprint for page routes (prefix: /admin)
booking_pages_bp = Blueprint('booking_pages', __name__, url_prefix='/admin')


# =============================================================================
# Page Routes (Unified Booking Dashboard)
# =============================================================================

@booking_pages_bp.route('/booking')
@login_required
@admin_required
def booking_dashboard():
    """Unified booking administration dashboard."""
    active_tab = request.args.get('tab', 'services')
    return render_template('admin/booking.html', active_tab=active_tab)


# =============================================================================
# Services CRUD
# =============================================================================

@booking_admin_bp.route('/services')
@login_required
@admin_required
def list_services():
    """Get all services for admin management."""
    services = Service.query.order_by(Service.display_order, Service.name).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'description': s.description or '',
        'duration_minutes': s.duration_minutes or 60,
        'price': float(s.price) if s.price else None,
        'requires_payment': s.requires_payment if hasattr(s, 'requires_payment') else False,
        'icon': s.icon or 'fa-clipboard-list',
        'display_order': s.display_order or 0
    } for s in services])


@booking_admin_bp.route('/services', methods=['POST'])
@login_required
@admin_required
def create_service():
    """Create a new service."""
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    service = Service(
        name=data['name'].strip(),
        description=data.get('description', '').strip(),
        duration_minutes=data.get('duration_minutes', 60),
        price=data.get('price'),
        icon=data.get('icon', 'fa-clipboard-list'),
        display_order=data.get('display_order', 0)
    )
    
    # Set requires_payment if the field exists
    if hasattr(service, 'requires_payment'):
        service.requires_payment = data.get('requires_payment', False)
    
    db.session.add(service)
    db.session.commit()
    
    return jsonify({'id': service.id, 'message': 'Service created'}), 201


@booking_admin_bp.route('/services/<int:service_id>', methods=['PUT'])
@login_required
@admin_required
def update_service(service_id):
    """Update an existing service."""
    service = Service.query.get_or_404(service_id)
    data = request.json
    
    if data.get('name'):
        service.name = data['name'].strip()
    if 'description' in data:
        service.description = data.get('description', '').strip()
    if 'duration_minutes' in data:
        service.duration_minutes = data.get('duration_minutes', 60)
    if 'price' in data:
        service.price = data.get('price')
    if 'icon' in data:
        service.icon = data.get('icon')
    if 'display_order' in data:
        service.display_order = data.get('display_order', 0)
    if hasattr(service, 'requires_payment') and 'requires_payment' in data:
        service.requires_payment = data.get('requires_payment', False)
    
    db.session.commit()
    return jsonify({'message': 'Service updated'})


@booking_admin_bp.route('/services/<int:service_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_service(service_id):
    """Delete a service."""
    service = Service.query.get_or_404(service_id)
    
    # Check if service has appointments
    if service.appointments:
        return jsonify({'error': 'Cannot delete service with existing appointments'}), 400
    
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': 'Service deleted'})


# =============================================================================
# Staff (Estimators from Employees) CRUD
# =============================================================================

@booking_admin_bp.route('/staff')
@login_required
@admin_required
def list_staff():
    """Get all staff/estimators with their linked user info."""
    estimators = Estimator.query.all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'user_id': e.user_id,
        'user_email': e.user.email if e.user else None,
        'user_name': f"{e.user.first_name or ''} {e.user.last_name or ''}".strip() or e.user.username if e.user else None,
        'is_active': e.is_active
    } for e in estimators])


@booking_admin_bp.route('/employees')
@login_required
@admin_required
def list_employees():
    """Get all users with employee role for staff selection."""
    from sqlalchemy import func
    
    # Case-insensitive search for Employee role
    employee_role = Role.query.filter(func.lower(Role.name) == 'employee').first()
    if not employee_role:
        return jsonify([])
    
    employees = User.query.filter(
        User.roles.any(id=employee_role.id),
        User.is_active == True
    ).all()
    
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'first_name': u.first_name,
        'last_name': u.last_name
    } for u in employees])


@booking_admin_bp.route('/staff', methods=['POST'])
@login_required
@admin_required
def create_staff():
    """Create a new staff member from an employee user."""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already an estimator
    existing = Estimator.query.filter_by(user_id=user_id).first()
    if existing:
        return jsonify({'error': 'User is already a staff member'}), 400
    
    # Create estimator linked to user
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username
    estimator = Estimator(
        name=name,
        user_id=user_id,
        is_active=True
    )
    
    db.session.add(estimator)
    db.session.flush()  # Get the estimator ID
    
    # Auto-seed default availability (Mon-Fri 9am-5pm)
    # Get business hours from config or use defaults
    config = {c.setting_name: c.setting_value for c in BusinessConfig.query.all()}
    start_hour = int(config.get('business_start_time', '09:00').split(':')[0])
    end_hour = int(config.get('business_end_time', '17:00').split(':')[0])
    
    for day in range(5):  # Monday=0 through Friday=4
        availability = Availability(
            estimator_id=estimator.id,
            day_of_week=day,
            start_time=time(start_hour, 0),
            end_time=time(end_hour, 0)
        )
        db.session.add(availability)
    
    db.session.commit()
    
    return jsonify({
        'id': estimator.id, 
        'message': 'Staff member added with default availability (Mon-Fri)'
    }), 201


@booking_admin_bp.route('/staff/<int:staff_id>', methods=['PATCH'])
@login_required
@admin_required
def update_staff(staff_id):
    """Update staff member (toggle active status)."""
    estimator = Estimator.query.get_or_404(staff_id)
    data = request.json
    
    if 'is_active' in data:
        estimator.is_active = data['is_active']
    if 'name' in data:
        estimator.name = data['name']
    
    db.session.commit()
    return jsonify({'message': 'Staff updated'})


@booking_admin_bp.route('/staff/<int:staff_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_staff(staff_id):
    """Remove a staff member from booking availability."""
    estimator = Estimator.query.get_or_404(staff_id)
    
    # Check if estimator has appointments
    if estimator.appointments:
        return jsonify({'error': 'Cannot remove staff with existing appointments. Deactivate instead.'}), 400
    
    db.session.delete(estimator)
    db.session.commit()
    return jsonify({'message': 'Staff removed'})


# =============================================================================
# Staff Availability CRUD
# =============================================================================

@booking_admin_bp.route('/availability/<int:staff_id>')
@login_required
@admin_required
def get_staff_availability(staff_id):
    """Get availability schedule for a staff member."""
    estimator = Estimator.query.get_or_404(staff_id)
    availabilities = Availability.query.filter_by(estimator_id=staff_id).order_by(Availability.day_of_week).all()
    
    return jsonify({
        'staff_id': staff_id,
        'staff_name': estimator.name,
        'availability': [{
            'id': a.id,
            'day_of_week': a.day_of_week,
            'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][a.day_of_week],
            'start_time': a.start_time.strftime('%H:%M') if a.start_time else None,
            'end_time': a.end_time.strftime('%H:%M') if a.end_time else None
        } for a in availabilities]
    })


@booking_admin_bp.route('/availability/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def set_staff_availability(staff_id):
    """Set availability schedule for a staff member."""
    estimator = Estimator.query.get_or_404(staff_id)
    data = request.json
    
    if not data or 'availability' not in data:
        return jsonify({'error': 'availability array is required'}), 400
    
    # Clear existing availability
    Availability.query.filter_by(estimator_id=staff_id).delete()
    
    # Create new availability entries
    for avail in data['availability']:
        day_of_week = avail.get('day_of_week')
        start_str = avail.get('start_time')
        end_str = avail.get('end_time')
        
        if day_of_week is None or not start_str or not end_str:
            continue
        
        try:
            start_parts = start_str.split(':')
            end_parts = end_str.split(':')
            start_time = time(int(start_parts[0]), int(start_parts[1]))
            end_time = time(int(end_parts[0]), int(end_parts[1]))
        except (ValueError, IndexError):
            continue
        
        availability = Availability(
            estimator_id=staff_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(availability)
    
    db.session.commit()
    return jsonify({'message': 'Availability updated', 'staff_id': staff_id})


@booking_admin_bp.route('/availability/<int:staff_id>/seed', methods=['POST'])
@login_required
@admin_required
def seed_staff_availability(staff_id):
    """Seed default Mon-Fri availability for a staff member."""
    estimator = Estimator.query.get_or_404(staff_id)
    
    # Check if already has availability
    existing = Availability.query.filter_by(estimator_id=staff_id).first()
    if existing:
        return jsonify({'error': 'Staff already has availability. Clear first if you want to reseed.'}), 400
    
    # Get business hours from config
    config = {c.setting_name: c.setting_value for c in BusinessConfig.query.all()}
    start_hour = int(config.get('business_start_time', '09:00').split(':')[0])
    end_hour = int(config.get('business_end_time', '17:00').split(':')[0])
    
    for day in range(5):  # Monday through Friday
        availability = Availability(
            estimator_id=staff_id,
            day_of_week=day,
            start_time=time(start_hour, 0),
            end_time=time(end_hour, 0)
        )
        db.session.add(availability)
    
    db.session.commit()
    return jsonify({'message': f'Default availability seeded for {estimator.name}'})


# =============================================================================
# Business Settings
# =============================================================================

@booking_admin_bp.route('/settings')
@login_required
@admin_required
def get_booking_settings():
    """Get business hours and booking configuration."""
    config = {c.setting_name: c.setting_value for c in BusinessConfig.query.all()}
    
    return jsonify({
        'business_start_time': config.get('business_start_time', '09:00'),
        'business_end_time': config.get('business_end_time', '17:00'),
        'buffer_time_minutes': int(config.get('buffer_time_minutes', 30)),
        'company_timezone': config.get('company_timezone', 'America/Denver'),
        'booking_enabled': config.get('booking_enabled', 'true') == 'true'
    })


@booking_admin_bp.route('/settings', methods=['PUT'])
@login_required
@admin_required  
def update_booking_settings():
    """Update business hours and booking configuration."""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Settings that can be updated
    allowed_settings = ['business_start_time', 'business_end_time', 'buffer_time_minutes', 'company_timezone', 'booking_enabled']
    
    for setting_name in allowed_settings:
        if setting_name in data:
            value = str(data[setting_name])
            config = BusinessConfig.query.filter_by(setting_name=setting_name).first()
            if config:
                config.setting_value = value
            else:
                config = BusinessConfig(setting_name=setting_name, setting_value=value)
                db.session.add(config)
    
    db.session.commit()
    return jsonify({'message': 'Settings updated'})


# =============================================================================
# Appointment Types (Read-only from here, full CRUD in scheduling routes)
# =============================================================================

@booking_admin_bp.route('/appointment-types')
@login_required
@admin_required
def list_appointment_types():
    """Get all appointment types."""
    types = AppointmentType.query.order_by(AppointmentType.name).all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'slug': t.slug,
        'duration_minutes': t.duration_minutes,
        'price': float(t.price) if t.price else None,
        'is_active': t.is_active,
        'max_attendees': t.max_attendees or 1
    } for t in types])


# =============================================================================
# Resources (Read-only from here, full CRUD in scheduling routes)
# =============================================================================

@booking_admin_bp.route('/resources')
@login_required
@admin_required
def list_resources():
    """Get all resources with inventory info."""
    resources = Resource.query.order_by(Resource.name).all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'resource_type': r.resource_type,
        'capacity': r.capacity,
        'is_active': r.is_active,
        'is_rental': r.is_rental if hasattr(r, 'is_rental') else False,
        'inventory_quantity': r.inventory_quantity if hasattr(r, 'inventory_quantity') else 1,
        'rental_unit': r.rental_unit if hasattr(r, 'rental_unit') else None,
        'hourly_rate': float(r.hourly_rate) if r.hourly_rate else None
    } for r in resources])


@booking_admin_bp.route('/resources/<int:resource_id>', methods=['PUT'])
@login_required
@admin_required
def update_resource(resource_id):
    """Update resource with inventory fields."""
    resource = Resource.query.get_or_404(resource_id)
    data = request.json
    
    if 'name' in data:
        resource.name = data['name'].strip()
    if 'is_active' in data:
        resource.is_active = data['is_active']
    if hasattr(resource, 'is_rental') and 'is_rental' in data:
        resource.is_rental = data['is_rental']
    if hasattr(resource, 'inventory_quantity') and 'inventory_quantity' in data:
        resource.inventory_quantity = data['inventory_quantity']
    if hasattr(resource, 'rental_unit') and 'rental_unit' in data:
        resource.rental_unit = data.get('rental_unit')
    if 'hourly_rate' in data:
        resource.hourly_rate = data.get('hourly_rate')
    
    db.session.commit()
    return jsonify({'message': 'Resource updated'})


@booking_admin_bp.route('/resources/<int:resource_id>/availability')
@login_required
@admin_required
def check_resource_availability(resource_id):
    """Check resource availability for a time range."""
    resource = Resource.query.get_or_404(resource_id)
    
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    if not start_str or not end_str:
        return jsonify({'error': 'start and end parameters required'}), 400
    
    from datetime import datetime
    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
    except ValueError:
        return jsonify({'error': 'Invalid datetime format'}), 400
    
    available = resource.get_available_quantity(start, end) if hasattr(resource, 'get_available_quantity') else 1
    
    return jsonify({
        'resource_id': resource_id,
        'available_quantity': available,
        'is_rental': resource.is_rental if hasattr(resource, 'is_rental') else False,
        'total_inventory': resource.inventory_quantity if hasattr(resource, 'inventory_quantity') else 1
    })


# =============================================================================
# Booking Form Templates & Intake Forms
# =============================================================================

# Pre-built field templates for booking intake forms
BOOKING_FIELD_TEMPLATES = {
    'contact_info': {
        'name': 'Contact Information',
        'fields': [
            {'name': 'first_name', 'type': 'text', 'label': 'First Name', 'required': True},
            {'name': 'last_name', 'type': 'text', 'label': 'Last Name', 'required': True},
            {'name': 'email', 'type': 'email', 'label': 'Email Address', 'required': True},
            {'name': 'phone', 'type': 'tel', 'label': 'Phone Number', 'required': False}
        ]
    },
    'address': {
        'name': 'Address',
        'fields': [
            {'name': 'street_address', 'type': 'text', 'label': 'Street Address', 'required': True},
            {'name': 'city', 'type': 'text', 'label': 'City', 'required': True},
            {'name': 'state', 'type': 'text', 'label': 'State/Province', 'required': True},
            {'name': 'zip_code', 'type': 'text', 'label': 'ZIP/Postal Code', 'required': True},
            {'name': 'country', 'type': 'select', 'label': 'Country', 'required': True, 
             'options': ['United States', 'Canada', 'Other']}
        ]
    },
    'emergency_contact': {
        'name': 'Emergency Contact',
        'fields': [
            {'name': 'emergency_name', 'type': 'text', 'label': 'Emergency Contact Name', 'required': True},
            {'name': 'emergency_phone', 'type': 'tel', 'label': 'Emergency Phone', 'required': True},
            {'name': 'emergency_relationship', 'type': 'text', 'label': 'Relationship', 'required': False}
        ]
    },
    'insurance': {
        'name': 'Insurance Information',
        'fields': [
            {'name': 'insurance_provider', 'type': 'text', 'label': 'Insurance Provider', 'required': False},
            {'name': 'policy_number', 'type': 'text', 'label': 'Policy Number', 'required': False},
            {'name': 'group_number', 'type': 'text', 'label': 'Group Number', 'required': False}
        ]
    },
    'notes': {
        'name': 'Additional Notes',
        'fields': [
            {'name': 'notes', 'type': 'textarea', 'label': 'Additional Notes or Special Requests', 'required': False}
        ]
    },
    'consent': {
        'name': 'Consent & Agreements',
        'fields': [
            {'name': 'terms_accepted', 'type': 'checkbox', 'label': 'I agree to the Terms of Service', 'required': True},
            {'name': 'cancellation_policy', 'type': 'checkbox', 'label': 'I understand the cancellation policy', 'required': True}
        ]
    }
}


@booking_admin_bp.route('/form-templates')
@login_required
@admin_required
def list_form_templates():
    """Get pre-built field templates for booking intake forms."""
    return jsonify(BOOKING_FIELD_TEMPLATES)


@booking_admin_bp.route('/intake-forms')
@login_required
@admin_required
def list_intake_forms():
    """Get all booking intake forms."""
    from app.models import FormDefinition
    
    forms = FormDefinition.query.filter(
        FormDefinition.form_type == 'booking_intake'
    ).order_by(FormDefinition.name).all()
    
    return jsonify([{
        'id': f.id,
        'name': f.name,
        'slug': f.slug,
        'description': f.description,
        'fields_count': len(f.fields_schema or []),
        'is_active': f.is_active
    } for f in forms])


@booking_admin_bp.route('/intake-forms', methods=['POST'])
@login_required
@admin_required
def create_intake_form():
    """Create a new booking intake form from templates."""
    from app.models import FormDefinition
    import re
    
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    # Generate slug from name
    slug = re.sub(r'[^a-z0-9]+', '-', data['name'].lower()).strip('-')
    base_slug = slug
    counter = 1
    while FormDefinition.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Build fields from selected templates
    fields = []
    for template_key in data.get('templates', []):
        template = BOOKING_FIELD_TEMPLATES.get(template_key)
        if template:
            fields.extend(template['fields'])
    
    # Add any custom fields
    fields.extend(data.get('custom_fields', []))
    
    form = FormDefinition(
        name=data['name'].strip(),
        slug=slug,
        description=data.get('description', ''),
        form_type='booking_intake',
        fields_schema=fields,
        settings=data.get('settings', {}),
        conditional_logic=data.get('conditional_logic', []),
        is_active=True,
        created_by_id=current_user.id
    )
    
    db.session.add(form)
    db.session.commit()
    
    return jsonify({'id': form.id, 'slug': form.slug, 'message': 'Intake form created'}), 201


# =============================================================================
# Appointments Management (Unified Dashboard APIs)
# =============================================================================

@booking_admin_bp.route('/appointments')
@login_required
@admin_required
def list_appointments():
    """
    List appointments with filters.
    
    Query params:
    - start: ISO date string (filter appointments from this date)
    - end: ISO date string (filter appointments until this date)
    - status: Filter by status (e.g., 'New', 'Confirmed', 'Cancelled')
    - staff_id: Filter by estimator ID
    - location_id: Filter by location ID
    - limit: Max results (default 100)
    """
    query = Appointment.query
    
    # Date range filter
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    if start_str:
        try:
            start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            query = query.filter(Appointment.preferred_date_time >= start)
        except ValueError:
            pass
    if end_str:
        try:
            end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            query = query.filter(Appointment.preferred_date_time <= end)
        except ValueError:
            pass
    
    # Status filter
    status = request.args.get('status')
    if status:
        query = query.filter(Appointment.status == status)
    
    # Staff filter
    staff_id = request.args.get('staff_id', type=int)
    if staff_id:
        query = query.filter(Appointment.estimator_id == staff_id)
    
    # Location filter
    location_id = request.args.get('location_id', type=int)
    if location_id:
        query = query.filter(Appointment.location_id == location_id)
    elif current_user.location_id:
        query = query.filter(Appointment.location_id == current_user.location_id)
    
    # Limit
    limit = request.args.get('limit', 100, type=int)
    
    # Order by date descending (most recent first)
    appointments = query.order_by(Appointment.preferred_date_time.desc()).limit(limit).all()
    
    return jsonify([{
        'id': a.id,
        'first_name': a.first_name,
        'last_name': a.last_name,
        'email': a.email,
        'phone': a.phone,
        'status': a.status,
        'preferred_date_time': a.preferred_date_time.isoformat() + 'Z' if a.preferred_date_time else None,
        'service': {
            'id': a.service.id,
            'name': a.service.name,
            'duration_minutes': a.service.duration_minutes
        } if a.service else None,
        'estimator': {
            'id': a.estimator.id,
            'name': a.estimator.name
        } if a.estimator else None,
        'location': {
            'id': a.location.id,
            'name': a.location.name
        } if a.location else None,
        'payment_status': a.payment_status,
        'created_at': a.created_at.isoformat() + 'Z' if a.created_at else None
    } for a in appointments])


@booking_admin_bp.route('/appointments/<int:appointment_id>')
@login_required
@admin_required
def get_appointment_detail(appointment_id):
    """Get full appointment details."""
    appt = Appointment.query.get_or_404(appointment_id)
    
    # Get reschedule requests for this appointment
    reschedule_requests = [{
        'id': r.id,
        'proposed_datetime': r.proposed_datetime.isoformat() + 'Z' if r.proposed_datetime else None,
        'reason': r.reason,
        'status': r.status,
        'created_at': r.created_at.isoformat() + 'Z' if r.created_at else None,
        'admin_notes': r.admin_notes
    } for r in appt.reschedule_requests]
    
    return jsonify({
        'id': appt.id,
        'first_name': appt.first_name,
        'last_name': appt.last_name,
        'email': appt.email,
        'phone': appt.phone,
        'status': appt.status,
        'notes': appt.notes,
        'staff_notes': appt.staff_notes,
        'preferred_date_time': appt.preferred_date_time.isoformat() + 'Z' if appt.preferred_date_time else None,
        'service': {
            'id': appt.service.id,
            'name': appt.service.name,
            'description': appt.service.description,
            'duration_minutes': appt.service.duration_minutes,
            'price': float(appt.service.price) if appt.service.price else None
        } if appt.service else None,
        'estimator': {
            'id': appt.estimator.id,
            'name': appt.estimator.name,
            'is_active': appt.estimator.is_active
        } if appt.estimator else None,
        'location': {
            'id': appt.location.id,
            'name': appt.location.name,
            'address': appt.location.address if hasattr(appt.location, 'address') else None
        } if appt.location else None,
        'payment_status': appt.payment_status,
        'payment_amount': float(appt.payment_amount) if appt.payment_amount else None,
        'is_recurring': appt.is_recurring,
        'checked_in_at': appt.checked_in_at.isoformat() + 'Z' if appt.checked_in_at else None,
        'checked_out_at': appt.checked_out_at.isoformat() + 'Z' if appt.checked_out_at else None,
        'intake_form_data': appt.intake_form_data or {},
        'reschedule_requests': reschedule_requests,
        'created_at': appt.created_at.isoformat() + 'Z' if appt.created_at else None,
        'updated_at': appt.updated_at.isoformat() + 'Z' if appt.updated_at else None
    })


@booking_admin_bp.route('/appointments/<int:appointment_id>/reschedule', methods=['POST'])
@login_required
@admin_required
def reschedule_appointment(appointment_id):
    """
    Admin-initiated reschedule - directly updates the appointment time.
    
    Body:
    - new_datetime: ISO string for new date/time
    - notify_customer: bool (default True) - send email notification
    - reason: optional reason for reschedule
    """
    appt = Appointment.query.get_or_404(appointment_id)
    data = request.json
    
    if not data or not data.get('new_datetime'):
        return jsonify({'error': 'new_datetime is required'}), 400
    
    try:
        new_dt = datetime.fromisoformat(data['new_datetime'].replace('Z', '+00:00'))
        new_dt_utc = new_dt.astimezone(pytz.utc).replace(tzinfo=None)
    except ValueError:
        return jsonify({'error': 'Invalid datetime format'}), 400
    
    old_dt = appt.preferred_date_time
    appt.preferred_date_time = new_dt_utc
    
    # Add staff note about reschedule
    reason = data.get('reason', '')
    staff_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Rescheduled from {old_dt.strftime('%Y-%m-%d %H:%M')} to {new_dt_utc.strftime('%Y-%m-%d %H:%M')}"
    if reason:
        staff_note += f". Reason: {reason}"
    staff_note += f" (by {current_user.username})"
    
    if appt.staff_notes:
        appt.staff_notes = appt.staff_notes + '\n' + staff_note
    else:
        appt.staff_notes = staff_note
    
    db.session.commit()
    
    # Send notification if requested
    notify = data.get('notify_customer', True)
    if notify:
        try:
            _send_reschedule_notification(appt, old_dt, new_dt_utc, reason)
        except Exception as e:
            # Log but don't fail the request
            from flask import current_app
            current_app.logger.warning(f"Failed to send reschedule notification: {e}")
    
    return jsonify({
        'message': 'Appointment rescheduled',
        'appointment_id': appt.id,
        'new_datetime': new_dt_utc.isoformat() + 'Z',
        'notification_sent': notify
    })


@booking_admin_bp.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_appointment(appointment_id):
    """
    Cancel an appointment.
    
    Body:
    - reason: cancellation reason
    - notify_customer: bool (default True)
    """
    appt = Appointment.query.get_or_404(appointment_id)
    data = request.json or {}
    
    old_status = appt.status
    appt.status = 'Cancelled'
    
    # Add cancellation note
    reason = data.get('reason', 'No reason provided')
    staff_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Cancelled. Reason: {reason} (by {current_user.username})"
    
    if appt.staff_notes:
        appt.staff_notes = appt.staff_notes + '\n' + staff_note
    else:
        appt.staff_notes = staff_note
    
    db.session.commit()
    
    # Send notification if requested
    notify = data.get('notify_customer', True)
    if notify:
        try:
            _send_cancellation_notification(appt, reason)
        except Exception as e:
            from flask import current_app
            current_app.logger.warning(f"Failed to send cancellation notification: {e}")
    
    return jsonify({
        'message': 'Appointment cancelled',
        'appointment_id': appt.id,
        'previous_status': old_status,
        'notification_sent': notify
    })


@booking_admin_bp.route('/appointments/<int:appointment_id>/request-reschedule', methods=['POST'])
@login_required
@admin_required
def request_customer_reschedule(appointment_id):
    """
    Request the customer to pick a new time slot.
    Creates a RescheduleRequest and sends an email to the customer.
    
    Body:
    - reason: why the customer needs to reschedule
    - suggested_datetime: optional suggested new time
    """
    appt = Appointment.query.get_or_404(appointment_id)
    data = request.json or {}
    
    reason = data.get('reason', 'The business has requested you reschedule your appointment.')
    
    # Parse suggested datetime if provided
    suggested_dt = None
    if data.get('suggested_datetime'):
        try:
            suggested_dt = datetime.fromisoformat(data['suggested_datetime'].replace('Z', '+00:00'))
            suggested_dt = suggested_dt.astimezone(pytz.utc).replace(tzinfo=None)
        except ValueError:
            pass
    
    # Create reschedule request record
    reschedule_request = RescheduleRequest(
        appointment_id=appt.id,
        user_id=current_user.id,
        proposed_datetime=suggested_dt or appt.preferred_date_time,  # Use current time if no suggestion
        reason=reason,
        status='pending'
    )
    
    db.session.add(reschedule_request)
    
    # Add staff note
    staff_note = f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Requested customer to reschedule. Reason: {reason} (by {current_user.username})"
    if appt.staff_notes:
        appt.staff_notes = appt.staff_notes + '\n' + staff_note
    else:
        appt.staff_notes = staff_note
    
    db.session.commit()
    
    # Send notification to customer
    try:
        _send_reschedule_request_notification(appt, reschedule_request)
    except Exception as e:
        from flask import current_app
        current_app.logger.warning(f"Failed to send reschedule request notification: {e}")
    
    return jsonify({
        'message': 'Reschedule request sent to customer',
        'appointment_id': appt.id,
        'reschedule_request_id': reschedule_request.id
    }), 201


@booking_admin_bp.route('/appointments/stats')
@login_required
@admin_required
def get_appointment_stats():
    """
    Get appointment statistics for the dashboard.
    
    Returns counts for:
    - today: appointments today
    - this_week: appointments this week
    - pending: appointments with pending status
    - pending_reschedule: reschedule requests pending response
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Week start (Monday) and end (Sunday)
    week_start = today_start - timedelta(days=now.weekday())
    week_end = week_start + timedelta(days=7)
    
    # Base query (filtered by user's location if set)
    base_query = Appointment.query
    if current_user.location_id:
        base_query = base_query.filter(Appointment.location_id == current_user.location_id)
    
    # Today's count
    today_count = base_query.filter(
        Appointment.preferred_date_time >= today_start,
        Appointment.preferred_date_time < today_end,
        Appointment.status != 'Cancelled'
    ).count()
    
    # This week's count
    week_count = base_query.filter(
        Appointment.preferred_date_time >= week_start,
        Appointment.preferred_date_time < week_end,
        Appointment.status != 'Cancelled'
    ).count()
    
    # Pending (status = 'New' or 'Pending')
    pending_count = base_query.filter(
        Appointment.status.in_(['New', 'Pending', 'Contacted'])
    ).count()
    
    # Pending reschedule requests
    pending_reschedule = RescheduleRequest.query.filter(
        RescheduleRequest.status == 'pending'
    ).count()
    
    # Upcoming (next 7 days, excluding today)
    upcoming_count = base_query.filter(
        Appointment.preferred_date_time >= today_end,
        Appointment.preferred_date_time < today_start + timedelta(days=7),
        Appointment.status != 'Cancelled'
    ).count()
    
    return jsonify({
        'today': today_count,
        'this_week': week_count,
        'pending': pending_count,
        'pending_reschedule': pending_reschedule,
        'upcoming': upcoming_count
    })


# =============================================================================
# Notification Helpers
# =============================================================================

def _send_reschedule_notification(appointment, old_datetime, new_datetime, reason=''):
    """Send email notification about appointment reschedule."""
    from app.modules.email_manager import send_email
    
    subject = "Your Appointment Has Been Rescheduled"
    body = f"""
Hello {appointment.first_name},

Your appointment has been rescheduled.

Previous Time: {old_datetime.strftime('%B %d, %Y at %I:%M %p')} UTC
New Time: {new_datetime.strftime('%B %d, %Y at %I:%M %p')} UTC
Service: {appointment.service.name if appointment.service else 'N/A'}
"""
    if reason:
        body += f"\nReason: {reason}"
    
    body += """

If this time doesn't work for you, please contact us to reschedule.

Thank you!
"""
    
    send_email(appointment.email, subject, body)


def _send_cancellation_notification(appointment, reason=''):
    """Send email notification about appointment cancellation."""
    from app.modules.email_manager import send_email
    
    subject = "Your Appointment Has Been Cancelled"
    body = f"""
Hello {appointment.first_name},

We regret to inform you that your appointment has been cancelled.

Original Time: {appointment.preferred_date_time.strftime('%B %d, %Y at %I:%M %p')} UTC
Service: {appointment.service.name if appointment.service else 'N/A'}

Reason: {reason}

If you would like to book a new appointment, please visit our booking page.

We apologize for any inconvenience.

Thank you!
"""
    
    send_email(appointment.email, subject, body)


def _send_reschedule_request_notification(appointment, reschedule_request):
    """Send email requesting customer to pick a new time slot."""
    from app.modules.email_manager import send_email
    from flask import url_for
    
    # Generate a booking link (customer can use general booking page)
    booking_link = url_for('booking.booking_page', _external=True)
    
    subject = "Please Reschedule Your Appointment"
    body = f"""
Hello {appointment.first_name},

We need to reschedule your upcoming appointment.

Current Time: {appointment.preferred_date_time.strftime('%B %d, %Y at %I:%M %p')} UTC
Service: {appointment.service.name if appointment.service else 'N/A'}

Reason: {reschedule_request.reason}

Please use the link below to select a new time that works for you:
{booking_link}

If you have any questions, please don't hesitate to contact us.

Thank you for your understanding!
"""
    
    send_email(appointment.email, subject, body)

