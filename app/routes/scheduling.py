"""
Phase 17: Scheduling Blueprint

Routes for:
1. Admin management of Appointment Types, Resources, Policies
2. Public booking flow (wizard)
3. Waitlist management
4. API endpoints for slots and availability
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.modules.auth_manager import admin_required
from app.database import db
from app.models import (
    AppointmentType, Resource, ResourceBooking, Waitlist, 
    BookingPolicy, Appointment, CheckInToken
)
from app.forms import CSRFTokenForm  # Needs new forms
from app.modules.scheduling_service import (
    get_appointment_type_slots, book_with_resources, 
    generate_checkin_token
)
from datetime import datetime

scheduling_bp = Blueprint('scheduling', __name__)

# ============================================================================
# Admin Routes
# ============================================================================

@scheduling_bp.route('/admin/scheduling/types')
@login_required
@admin_required
def list_types():
    import json
    types = AppointmentType.query.order_by(AppointmentType.name).all()
    
    # Serialize for AdminDataTable
    types_json = json.dumps([{
        'id': t.id,
        'name': f'<strong>{t.name}</strong><br><small class="text-muted">/book/{t.slug}</small>',
        'duration': f'{t.duration_minutes} min',
        'price': f'${t.price:.2f}' if t.price else 'Free',
        'status': '<span class="badge bg-success">Active</span>' if t.is_active else '<span class="badge bg-secondary">Inactive</span>',
        'actions': f'<a href="#" class="btn btn-sm btn-outline-secondary">Edit</a>'
    } for t in types])
    
    return render_template('admin/scheduling/types/index.html', types=types, types_json=types_json)

@scheduling_bp.route('/admin/scheduling/types/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_type():
    # Placeholder for AppointmentTypeForm
    if request.method == 'POST':
        # Simplify for first pass: manually extracting or using generic form
        # In real impl, would use AppointmentTypeForm
        appt_type = AppointmentType(
            name=request.form.get('name'),
            slug=request.form.get('slug'),
            duration_minutes=int(request.form.get('duration_minutes', 60)),
            price=float(request.form.get('price', 0)) if request.form.get('price') else None,
            description=request.form.get('description'),
            max_attendees=int(request.form.get('max_attendees', 1))
        )
        db.session.add(appt_type)
        db.session.commit()
        flash('Appointment Type created', 'success')
        return redirect(url_for('scheduling.list_types'))
    
    return render_template('admin/scheduling/types/form.html', form=None)

@scheduling_bp.route('/admin/scheduling/resources')
@login_required
@admin_required
def list_resources():
    import json
    resources = Resource.query.order_by(Resource.name).all()
    
    # Serialize for AdminDataTable
    resources_json = json.dumps([{
        'id': r.id,
        'name': f'<strong>{r.name}</strong>' + (f'<br><small class="text-muted">{r.description[:50]}...</small>' if r.description and len(r.description) > 50 else (f'<br><small class="text-muted">{r.description}</small>' if r.description else '')),
        'type': f'<span class="badge bg-info text-dark">{r.resource_type}</span>',
        'capacity': r.capacity,
        'status': '<span class="badge bg-success">Active</span>' if r.is_active else '<span class="badge bg-secondary">Inactive</span>',
        'actions': '<a href="#" class="btn btn-sm btn-outline-secondary">Edit</a>'
    } for r in resources])
    
    return render_template('admin/scheduling/resources/index.html', resources=resources, resources_json=resources_json)

@scheduling_bp.route('/admin/scheduling/resources/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_resource():
    if request.method == 'POST':
        resource = Resource(
            name=request.form.get('name'),
            resource_type=request.form.get('resource_type'),
            capacity=int(request.form.get('capacity', 1)),
            description=request.form.get('description')
        )
        db.session.add(resource)
        db.session.commit()
        flash('Resource created', 'success')
        return redirect(url_for('scheduling.list_resources'))
        
    return render_template('admin/scheduling/resources/form.html')

@scheduling_bp.route('/admin/scheduling/waitlist')
@login_required
@admin_required
def waitlist():
    import json
    entries = Waitlist.query.order_by(Waitlist.created_at.desc()).all()
    
    # Status color mapping
    status_colors = {'waiting': 'warning', 'offered': 'info', 'booked': 'success', 'expired': 'danger'}
    
    # Serialize for AdminDataTable
    entries_json = json.dumps([{
        'id': e.id,
        'created_at': e.created_at.strftime('%Y-%m-%d %H:%M') if e.created_at else '-',
        'customer': (f'<a href="#">{e.user.full_name}</a>' if e.user else f'{e.first_name} {e.last_name}<br><small class="text-muted">{e.email}</small>'),
        'type': e.appointment_type.name if e.appointment_type else '-',
        'priority': '<span class="badge bg-warning text-dark">High</span>' if e.priority > 0 else 'Normal',
        'status': f'<span class="badge bg-{status_colors.get(e.status, "secondary")}">{e.status.title() if e.status else "-"}</span>',
        'actions': '<div class="btn-group"><button type="button" class="btn btn-sm btn-outline-primary dropdown-toggle" data-bs-toggle="dropdown">Action</button><ul class="dropdown-menu"><li><a class="dropdown-item" href="#">Make Offer</a></li><li><a class="dropdown-item" href="#">View Details</a></li><li><hr class="dropdown-divider"></li><li><a class="dropdown-item text-danger" href="#">Remove</a></li></ul></div>'
    } for e in entries])
    
    return render_template('admin/scheduling/waitlist/index.html', entries=entries, entries_json=entries_json)

@scheduling_bp.route('/admin/scheduling/capacity')
@login_required
@admin_required
def capacity_dashboard():
    return render_template('admin/scheduling/capacity.html')

# ============================================================================
# Public Booking Routes
# ============================================================================

@scheduling_bp.route('/book')
def booking_index():
    """Landing page for public booking."""
    types = AppointmentType.query.filter_by(is_active=True).all()
    return render_template('booking/index.html', types=types)

@scheduling_bp.route('/book/<slug>')
def booking_wizard(slug):
    """Booking wizard for specific type."""
    import json
    appt_type = AppointmentType.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Serialize appointment type data for React component
    appt_type_json = json.dumps({
        'id': appt_type.id,
        'name': appt_type.name,
        'slug': appt_type.slug,
        'duration_minutes': appt_type.duration_minutes,
        'price': float(appt_type.price) if appt_type.price else None,
        'description': appt_type.description or '',
        'max_attendees': appt_type.max_attendees or 1
    })
    
    # Generate URLs for React component
    slots_api_url = url_for('scheduling.api_slots', slug=slug)
    submit_url = url_for('scheduling.submit_booking', slug=slug)
    
    return render_template('booking/book.html', 
                          type=appt_type,
                          appt_type_json=appt_type_json,
                          slots_api_url=slots_api_url,
                          submit_url=submit_url)

@scheduling_bp.route('/book/<slug>/submit', methods=['POST'])
def submit_booking(slug):
    """Handle booking submission."""
    appt_type = AppointmentType.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Extract data
    data = {
        'first_name': request.form.get('first_name'),
        'last_name': request.form.get('last_name'),
        'email': request.form.get('email'),
        'phone': request.form.get('phone'),
        'appointment_type_id': appt_type.id,
        'preferred_date_time': datetime.fromisoformat(request.form.get('datetime').replace('Z', '+00:00')),
        'estimator_id': request.form.get('estimator_id'), # Optional or auto-assigned
        'current_attendees': int(request.form.get('attendees', 1))
    }
    
    # If type requires resource
    requirements = []
    if appt_type.required_resource_type:
        requirements.append(appt_type.required_resource_type)
        
    appt, error = book_with_resources(data, requirements)
    
    if error:
        flash(f'Booking failed: {error}', 'error')
        return redirect(url_for('scheduling.booking_wizard', slug=slug))
        
    # Generate check-in token
    if appt_type.confirmation_required: # or always
        generate_checkin_token(appt.id)
        
    return render_template('booking/confirmation.html', appointment=appt)

# ============================================================================
# API Endpoints
# ============================================================================

@scheduling_bp.route('/api/scheduling/types')
def api_types():
    types = AppointmentType.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'slug': t.slug,
        'duration': t.duration_minutes,
        'price': str(t.price) if t.price else None
    } for t in types])

@scheduling_bp.route('/api/scheduling/slots/<slug>')
def api_slots(slug):
    appt_type = AppointmentType.query.filter_by(slug=slug).first_or_404()
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date required'}), 400
        
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    slots = get_appointment_type_slots(appt_type.id, target_date)
    
    return jsonify({
        'date': date_str,
        'slots': [s.isoformat() for s in slots]
    })
