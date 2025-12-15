"""
Admin Schedule Management API Routes.

Provides comprehensive endpoints for managing employee schedules,
shift templates, shift swaps, and recurring schedules.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.database import db
from app.models import (
    EmployeeSchedule, ShiftTemplate, ShiftSwapRequest, ScheduleRecurrence,
    User, Location
)
from app.modules.auth_manager import role_required
from app.modules.security import rate_limiter
from datetime import datetime, date, time, timedelta
from sqlalchemy import and_, or_

schedule_bp = Blueprint('schedule', __name__, url_prefix='/admin/api')


# ============================================================================
# Rate Limit Exemption - All routes in this blueprint are role-protected
# ============================================================================
# Note: We exempt admin schedule routes from rate limiting since they
# already require admin/manager/owner roles for access.


# ============================================================================
# Shift Templates
# ============================================================================

@schedule_bp.route('/shift-templates', methods=['GET'])
@rate_limiter.exempt
@login_required
@role_required('admin', 'manager', 'owner')
def list_shift_templates():
    """Get all shift templates."""
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    query = ShiftTemplate.query
    if active_only:
        query = query.filter_by(is_active=True)
    
    templates = query.order_by(ShiftTemplate.name).all()
    return jsonify({
        'success': True,
        'templates': [t.to_dict() for t in templates]
    })


@schedule_bp.route('/shift-templates', methods=['POST'])
@login_required
@role_required('admin', 'manager', 'owner')
def create_shift_template():
    """Create a new shift template."""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    # Validate required fields
    required = ['name', 'start_time', 'end_time']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field} is required'}), 400
    
    try:
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid time format. Use HH:MM'}), 400
    
    template = ShiftTemplate(
        name=data['name'],
        description=data.get('description'),
        start_time=start_time,
        end_time=end_time,
        color=data.get('color', '#3B82F6'),
        icon=data.get('icon'),
        shift_type=data.get('shift_type', 'regular')
    )
    
    db.session.add(template)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Template created successfully',
        'template': template.to_dict()
    }), 201


@schedule_bp.route('/shift-templates/<int:template_id>', methods=['PUT'])
@login_required
@role_required('admin', 'manager', 'owner')
def update_shift_template(template_id):
    """Update a shift template."""
    template = ShiftTemplate.query.get_or_404(template_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    if 'name' in data:
        template.name = data['name']
    if 'description' in data:
        template.description = data['description']
    if 'start_time' in data:
        try:
            template.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid start_time format'}), 400
    if 'end_time' in data:
        try:
            template.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid end_time format'}), 400
    if 'color' in data:
        template.color = data['color']
    if 'icon' in data:
        template.icon = data['icon']
    if 'shift_type' in data:
        template.shift_type = data['shift_type']
    if 'is_active' in data:
        template.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Template updated successfully',
        'template': template.to_dict()
    })


@schedule_bp.route('/shift-templates/<int:template_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'owner')
def delete_shift_template(template_id):
    """Delete a shift template (soft delete by setting inactive)."""
    template = ShiftTemplate.query.get_or_404(template_id)
    
    # Soft delete - keep for historical reference
    template.is_active = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Template deactivated successfully'
    })


# ============================================================================
# Employee Schedules
# ============================================================================

@schedule_bp.route('/schedules', methods=['GET'])
@rate_limiter.exempt
@login_required
@role_required('admin', 'manager', 'owner')
def list_schedules():
    """Get schedules with filtering options."""
    # Date range (default: current week)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    user_id = request.args.get('user_id', type=int)
    location_id = request.args.get('location_id', type=int)
    status = request.args.get('status')
    
    # Default to current week
    today = date.today()
    if not start_date_str:
        start_date = today - timedelta(days=today.weekday())  # Monday
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid start_date format'}), 400
    
    if not end_date_str:
        end_date = start_date + timedelta(days=6)  # Sunday
    else:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid end_date format'}), 400
    
    # Build query
    query = EmployeeSchedule.query.filter(
        EmployeeSchedule.date >= start_date,
        EmployeeSchedule.date <= end_date
    )
    
    if user_id:
        query = query.filter(EmployeeSchedule.user_id == user_id)
    if location_id:
        query = query.filter(EmployeeSchedule.location_id == location_id)
    if status:
        query = query.filter(EmployeeSchedule.status == status)
    
    schedules = query.order_by(EmployeeSchedule.date, EmployeeSchedule.start_time).all()
    
    # Group by date for easier frontend consumption
    schedules_by_date = {}
    for s in schedules:
        date_str = s.date.isoformat()
        if date_str not in schedules_by_date:
            schedules_by_date[date_str] = []
        schedules_by_date[date_str].append(s.to_dict())
    
    return jsonify({
        'success': True,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'schedules': [s.to_dict() for s in schedules],
        'schedules_by_date': schedules_by_date
    })


@schedule_bp.route('/schedules', methods=['POST'])
@login_required
@role_required('admin', 'manager', 'owner')
def create_schedule():
    """Create a new schedule entry."""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    # Validate required fields
    required = ['user_id', 'date', 'start_time', 'end_time']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field} is required'}), 400
    
    # Parse date and times
    try:
        schedule_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date/time format'}), 400
    
    # Check for conflicts
    existing = EmployeeSchedule.query.filter(
        EmployeeSchedule.user_id == data['user_id'],
        EmployeeSchedule.date == schedule_date,
        EmployeeSchedule.status != 'cancelled'
    ).all()
    
    # Create temp schedule to check overlap
    new_schedule = EmployeeSchedule(
        user_id=data['user_id'],
        date=schedule_date,
        start_time=start_time,
        end_time=end_time
    )
    
    for existing_schedule in existing:
        if new_schedule.overlaps_with(existing_schedule):
            return jsonify({
                'success': False,
                'message': f'Schedule conflicts with existing shift: {existing_schedule.start_time.strftime("%H:%M")}-{existing_schedule.end_time.strftime("%H:%M")}',
                'conflict': existing_schedule.to_dict()
            }), 409
    
    # Create the schedule
    schedule = EmployeeSchedule(
        user_id=data['user_id'],
        date=schedule_date,
        start_time=start_time,
        end_time=end_time,
        shift_type=data.get('shift_type', 'regular'),
        template_id=data.get('template_id'),
        location_id=data.get('location_id'),
        notes=data.get('notes'),
        color=data.get('color'),
        created_by_id=current_user.id
    )
    
    db.session.add(schedule)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Schedule created successfully',
        'schedule': schedule.to_dict()
    }), 201


@schedule_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
@login_required
@role_required('admin', 'manager', 'owner')
def update_schedule(schedule_id):
    """Update a schedule entry."""
    schedule = EmployeeSchedule.query.get_or_404(schedule_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    # Update fields
    if 'date' in data:
        try:
            schedule.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
    if 'start_time' in data:
        try:
            schedule.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid start_time format'}), 400
    if 'end_time' in data:
        try:
            schedule.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid end_time format'}), 400
    if 'shift_type' in data:
        schedule.shift_type = data['shift_type']
    if 'location_id' in data:
        schedule.location_id = data['location_id']
    if 'status' in data:
        schedule.status = data['status']
    if 'notes' in data:
        schedule.notes = data['notes']
    if 'color' in data:
        schedule.color = data['color']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Schedule updated successfully',
        'schedule': schedule.to_dict()
    })


@schedule_bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'manager', 'owner')
def delete_schedule(schedule_id):
    """Cancel/delete a schedule entry."""
    schedule = EmployeeSchedule.query.get_or_404(schedule_id)
    
    # Soft delete - set status to cancelled
    schedule.status = 'cancelled'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Schedule cancelled successfully'
    })


@schedule_bp.route('/schedules/bulk', methods=['POST'])
@login_required
@role_required('admin', 'manager', 'owner')
def bulk_create_schedules():
    """Create multiple schedules at once (e.g., copy a week)."""
    data = request.get_json()
    
    if not data or 'schedules' not in data:
        return jsonify({'success': False, 'message': 'schedules array is required'}), 400
    
    created = []
    errors = []
    
    for idx, sched_data in enumerate(data['schedules']):
        try:
            schedule_date = datetime.strptime(sched_data['date'], '%Y-%m-%d').date()
            start_time = datetime.strptime(sched_data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(sched_data['end_time'], '%H:%M').time()
            
            schedule = EmployeeSchedule(
                user_id=sched_data['user_id'],
                date=schedule_date,
                start_time=start_time,
                end_time=end_time,
                shift_type=sched_data.get('shift_type', 'regular'),
                template_id=sched_data.get('template_id'),
                location_id=sched_data.get('location_id'),
                notes=sched_data.get('notes'),
                color=sched_data.get('color'),
                created_by_id=current_user.id
            )
            db.session.add(schedule)
            created.append(schedule)
        except Exception as e:
            errors.append({'index': idx, 'error': str(e)})
    
    if created:
        db.session.commit()
    
    return jsonify({
        'success': len(created) > 0,
        'message': f'Created {len(created)} schedules',
        'created_count': len(created),
        'error_count': len(errors),
        'errors': errors
    })


# ============================================================================
# Shift Swap Requests (Admin)
# ============================================================================

@schedule_bp.route('/shift-swaps', methods=['GET'])
@login_required
@role_required('admin', 'manager', 'owner')
def list_shift_swaps():
    """Get shift swap requests."""
    status = request.args.get('status', 'pending')
    
    query = ShiftSwapRequest.query
    if status:
        query = query.filter(ShiftSwapRequest.status == status)
    
    swaps = query.order_by(ShiftSwapRequest.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'swaps': [s.to_dict() for s in swaps]
    })


@schedule_bp.route('/shift-swaps/<int:swap_id>', methods=['PUT'])
@login_required
@role_required('admin', 'manager', 'owner')
def handle_shift_swap(swap_id):
    """Approve or reject a shift swap request."""
    swap = ShiftSwapRequest.query.get_or_404(swap_id)
    data = request.get_json()
    
    if not data or 'action' not in data:
        return jsonify({'success': False, 'message': 'action is required (approve/reject)'}), 400
    
    action = data['action']
    
    if action == 'approve':
        swap.status = 'approved'
        swap.approved_by_id = current_user.id
        swap.approved_at = datetime.utcnow()
        swap.admin_notes = data.get('admin_notes')
        
        # Update the schedule to reassign to target user
        if swap.target_user_id and swap.schedule:
            swap.schedule.user_id = swap.target_user_id
        
        message = 'Shift swap approved'
        
    elif action == 'reject':
        swap.status = 'rejected'
        swap.approved_by_id = current_user.id
        swap.approved_at = datetime.utcnow()
        swap.admin_notes = data.get('admin_notes')
        message = 'Shift swap rejected'
        
    else:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': message,
        'swap': swap.to_dict()
    })


# ============================================================================
# Schedule Statistics
# ============================================================================

@schedule_bp.route('/schedules/stats', methods=['GET'])
@rate_limiter.exempt
@login_required
@role_required('admin', 'manager', 'owner')
def schedule_stats():
    """Get scheduling statistics for a date range."""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    today = date.today()
    if not start_date_str:
        start_date = today - timedelta(days=today.weekday())
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    
    if not end_date_str:
        end_date = start_date + timedelta(days=6)
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Get all schedules in range
    schedules = EmployeeSchedule.query.filter(
        EmployeeSchedule.date >= start_date,
        EmployeeSchedule.date <= end_date,
        EmployeeSchedule.status != 'cancelled'
    ).all()
    
    # Calculate stats
    total_shifts = len(schedules)
    total_hours = sum(s.duration_minutes() for s in schedules) / 60
    employees_scheduled = len(set(s.user_id for s in schedules))
    
    # Pending swaps
    pending_swaps = ShiftSwapRequest.query.filter_by(status='pending').count()
    
    return jsonify({
        'success': True,
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'stats': {
            'total_shifts': total_shifts,
            'total_hours': round(total_hours, 1),
            'employees_scheduled': employees_scheduled,
            'pending_swaps': pending_swaps
        }
    })


# ============================================================================
# Employees List (for scheduling interface)
# ============================================================================

@schedule_bp.route('/schedulable-employees', methods=['GET'])
@rate_limiter.exempt
@login_required
@role_required('admin', 'manager', 'owner')
def list_schedulable_employees():
    """Get list of employees available for scheduling."""
    from app.models import Role
    
    # Get users with employee role or higher (use capitalized role names)
    schedulable_roles = ['Employee', 'Manager', 'Admin', 'Owner']
    role_objects = Role.query.filter(Role.name.in_(schedulable_roles)).all()
    role_ids = [r.id for r in role_objects]
    
    employees = User.query.join(User.roles).filter(
        Role.id.in_(role_ids)
    ).distinct().order_by(User.last_name, User.first_name).all()
    
    return jsonify({
        'success': True,
        'employees': [
            {
                'id': e.id,
                'username': e.username,
                'first_name': e.first_name,
                'last_name': e.last_name,
                'full_name': f"{e.first_name or ''} {e.last_name or ''}".strip() or e.username,
                'email': e.email,
                'department': e.department
            }
            for e in employees
        ]
    })
