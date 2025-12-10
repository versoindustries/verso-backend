"""
Booking Admin API Routes

API endpoints for the unified booking admin dashboard.
Supports CRUD operations for services, staff (from employees), and other booking entities.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.modules.auth_manager import admin_required
from app.database import db
from app.models import (
    Service, Estimator, User, Role, AppointmentType, Resource
)

booking_admin_bp = Blueprint('booking_admin', __name__, url_prefix='/api/admin/booking')


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
    employee_role = Role.query.filter_by(name='employee').first()
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
    db.session.commit()
    
    return jsonify({'id': estimator.id, 'message': 'Staff member added'}), 201


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
