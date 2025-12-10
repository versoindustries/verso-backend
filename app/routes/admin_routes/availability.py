"""
Phase 2: Availability Management Routes

Admin routes for managing estimator availability and exceptions.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.modules.auth_manager import admin_required
from app.models import Estimator, Availability, AvailabilityException
from app.forms import AvailabilityForm, AvailabilityExceptionForm, CSRFTokenForm
from app.database import db
from app.modules.availability_service import get_estimator_availability, get_available_slots
from datetime import datetime, date

availability_bp = Blueprint('availability', __name__, url_prefix='/admin/availability')


@availability_bp.route('/')
@login_required
@admin_required
def list_estimators():
    """List all estimators for availability management."""
    estimators = Estimator.query.order_by(Estimator.name).all()
    return render_template('admin/availability/list_estimators.html', estimators=estimators)


@availability_bp.route('/estimator/<int:estimator_id>')
@login_required
@admin_required
def edit_availability(estimator_id):
    """Edit weekly availability for an estimator."""
    estimator = Estimator.query.get_or_404(estimator_id)
    availabilities = Availability.query.filter_by(estimator_id=estimator_id).order_by(
        Availability.day_of_week, Availability.start_time
    ).all()
    
    form = AvailabilityForm()
    delete_form = CSRFTokenForm()
    
    # Group by day of week for display
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    availability_by_day = {i: [] for i in range(7)}
    for a in availabilities:
        availability_by_day[a.day_of_week].append(a)
    
    return render_template(
        'admin/availability/edit_availability.html',
        estimator=estimator,
        availability_by_day=availability_by_day,
        days=days,
        form=form,
        delete_form=delete_form
    )


@availability_bp.route('/estimator/<int:estimator_id>/add', methods=['POST'])
@login_required
@admin_required
def add_availability(estimator_id):
    """Add a new availability slot for an estimator."""
    estimator = Estimator.query.get_or_404(estimator_id)
    form = AvailabilityForm()
    
    if form.validate_on_submit():
        from datetime import time
        start_time = datetime.strptime(form.start_time.data, '%H:%M').time()
        end_time = datetime.strptime(form.end_time.data, '%H:%M').time()
        
        availability = Availability(
            estimator_id=estimator_id,
            day_of_week=form.day_of_week.data,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(availability)
        db.session.commit()
        flash('Availability added successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('availability.edit_availability', estimator_id=estimator_id))


@availability_bp.route('/availability/<int:availability_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_availability(availability_id):
    """Delete an availability slot."""
    availability = Availability.query.get_or_404(availability_id)
    estimator_id = availability.estimator_id
    db.session.delete(availability)
    db.session.commit()
    flash('Availability deleted.', 'success')
    return redirect(url_for('availability.edit_availability', estimator_id=estimator_id))


@availability_bp.route('/estimator/<int:estimator_id>/exceptions')
@login_required
@admin_required
def list_exceptions(estimator_id):
    """List exception dates for an estimator."""
    import json
    
    estimator = Estimator.query.get_or_404(estimator_id)
    exceptions = AvailabilityException.query.filter_by(estimator_id=estimator_id).order_by(
        AvailabilityException.date.desc()
    ).all()
    
    form = AvailabilityExceptionForm()
    delete_form = CSRFTokenForm()
    
    # Serialize exceptions for React AdminDataTable
    exceptions_json = json.dumps([{
        'id': ex.id,
        'date': ex.date.strftime('%Y-%m-%d (%a)'),
        'type': '<span class="badge bg-danger">Blocked</span>' if ex.is_blocked else '<span class="badge bg-warning">Custom Hours</span>',
        'hours': '<span class="text-muted">N/A</span>' if ex.is_blocked else f'{ex.custom_start_time.strftime("%H:%M")} - {ex.custom_end_time.strftime("%H:%M")}',
        'reason': ex.reason or '-',
        'actions': f'''<form method="POST" class="d-inline" action="{url_for('availability.delete_exception', exception_id=ex.id)}">
            <input type="hidden" name="csrf_token" value="{delete_form.csrf_token._value()}">
            <button type="submit" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete this exception?')">
                <i class="fas fa-trash"></i>
            </button>
        </form>'''
    } for ex in exceptions])
    
    return render_template(
        'admin/availability/list_exceptions.html',
        estimator=estimator,
        exceptions=exceptions,
        exceptions_json=exceptions_json,
        form=form,
        delete_form=delete_form
    )


@availability_bp.route('/estimator/<int:estimator_id>/exceptions/add', methods=['POST'])
@login_required
@admin_required
def add_exception(estimator_id):
    """Add an exception date for an estimator."""
    estimator = Estimator.query.get_or_404(estimator_id)
    form = AvailabilityExceptionForm()
    
    if form.validate_on_submit():
        custom_start = None
        custom_end = None
        
        if not form.is_blocked.data:
            custom_start = datetime.strptime(form.custom_start_time.data, '%H:%M').time()
            custom_end = datetime.strptime(form.custom_end_time.data, '%H:%M').time()
        
        exception = AvailabilityException(
            estimator_id=estimator_id,
            date=form.date.data,
            is_blocked=form.is_blocked.data,
            custom_start_time=custom_start,
            custom_end_time=custom_end,
            reason=form.reason.data
        )
        db.session.add(exception)
        db.session.commit()
        flash('Exception added successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('availability.list_exceptions', estimator_id=estimator_id))


@availability_bp.route('/exception/<int:exception_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_exception(exception_id):
    """Delete an exception date."""
    exception = AvailabilityException.query.get_or_404(exception_id)
    estimator_id = exception.estimator_id
    db.session.delete(exception)
    db.session.commit()
    flash('Exception deleted.', 'success')
    return redirect(url_for('availability.list_exceptions', estimator_id=estimator_id))


# HTMX Endpoint for Real-Time Slot Availability
@availability_bp.route('/api/slots')
def get_slots():
    """
    HTMX endpoint to get available slots for a date/estimator combination.
    
    Query params:
        estimator_id: int
        date: YYYY-MM-DD
        service_id: int (optional)
    
    Returns HTML options for time select.
    """
    try:
        estimator_id = request.args.get('estimator_id', type=int)
        date_str = request.args.get('date')
        service_id = request.args.get('service_id', type=int)
        
        if not estimator_id or not date_str:
            return '<option value="">Please select date and estimator</option>'
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Don't allow past dates
        if target_date < date.today():
            return '<option value="">Cannot book past dates</option>'
        
        slots = get_available_slots(estimator_id, target_date, service_id)
        
        if not slots:
            return '<option value="">No available slots on this date</option>'
        
        options = ['<option value="">Select a time</option>']
        for slot in slots:
            time_str = slot.strftime('%H:%M')
            display_time = slot.strftime('%I:%M %p')  # 12-hour format for display
            options.append(f'<option value="{time_str}">{display_time}</option>')
        
        return '\n'.join(options)
        
    except Exception as e:
        return f'<option value="">Error: {str(e)}</option>'


@availability_bp.route('/api/check-slot')
def check_slot():
    """
    API endpoint to check if a specific slot is available.
    
    Returns JSON: {available: bool, reason: string|null}
    """
    from app.modules.availability_service import check_slot_available
    
    try:
        estimator_id = request.args.get('estimator_id', type=int)
        datetime_str = request.args.get('datetime')  # ISO format
        service_id = request.args.get('service_id', type=int)
        
        if not estimator_id or not datetime_str:
            return jsonify({'available': False, 'reason': 'Missing parameters'})
        
        slot_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Get duration from service
        from app.models import Service
        duration = 60
        if service_id:
            service = Service.query.get(service_id)
            if service and service.duration_minutes:
                duration = service.duration_minutes
        
        config = get_business_config()
        buffer = int(config.get('buffer_time_minutes', 30))
        
        available, reason = check_slot_available(estimator_id, slot_datetime, duration, buffer)
        
        return jsonify({'available': available, 'reason': reason})
        
    except Exception as e:
        return jsonify({'available': False, 'reason': str(e)})


def get_business_config():
    """Get business config dict."""
    from app.models import BusinessConfig
    configs = BusinessConfig.query.all()
    return {c.setting_name: c.setting_value for c in configs}
