from flask import Blueprint, jsonify, request
from app.models import Estimator, Service, Availability, Appointment, db
from app.modules.availability_service import get_available_slots, check_slot_available
from app.modules.security import rate_limiter
from datetime import datetime, date, time

booking_api_bp = Blueprint('booking_api', __name__, url_prefix='/api/booking')


@booking_api_bp.route('/estimators')
@rate_limiter.exempt
def get_estimators():
    """Get all active estimators for booking selection."""
    estimators = Estimator.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': e.id,
        'name': e.name
    } for e in estimators])


@booking_api_bp.route('/services')
@rate_limiter.exempt
def get_services():
    """Get all services with full details for booking display."""
    services = Service.query.order_by(Service.display_order).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'description': s.description or '',
        'duration': s.duration_minutes or 60,
        'price': s.price or 0,
        'icon': s.icon or 'fa-clipboard-list'
    } for s in services])


@booking_api_bp.route('/slots')
@rate_limiter.exempt
def get_slots():
    """Get available time slots for a specific estimator and date."""
    estimator_id = request.args.get('estimator_id', type=int)
    date_str = request.args.get('date')
    service_id = request.args.get('service_id', type=int)
    
    if not estimator_id or not date_str:
        return jsonify({'error': 'Missing required parameters: estimator_id and date'}), 400
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Don't allow booking in the past
        if target_date < date.today():
            return jsonify({'slots': []})
        
        slots = get_available_slots(estimator_id, target_date, service_id)
        
        return jsonify({
            'slots': [s.strftime('%H:%M') for s in slots]
        })
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@booking_api_bp.route('/create', methods=['POST'])
@rate_limiter.exempt
def create_booking():
    """Create a new appointment booking."""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Required field validation
    required_fields = ['service_id', 'date', 'time', 'first_name', 'last_name', 'email']
    missing_fields = [f for f in required_fields if not data.get(f)]
    
    if missing_fields:
        return jsonify({
            'error': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400
    
    # Email validation
    email = data.get('email', '').strip()
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Invalid email address'}), 400
    
    try:
        # Parse date and time
        booking_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        booking_time = datetime.strptime(data['time'], '%H:%M').time()
        preferred_datetime = datetime.combine(booking_date, booking_time)
        
        # Validate not in the past
        if preferred_datetime < datetime.now():
            return jsonify({'error': 'Cannot book appointments in the past'}), 400
        
        # Get estimator (use provided or pick first available)
        estimator_id = data.get('estimator_id')
        if not estimator_id:
            first_estimator = Estimator.query.filter_by(is_active=True).first()
            if first_estimator:
                estimator_id = first_estimator.id
            else:
                return jsonify({'error': 'No available staff members'}), 400
        
        # Verify the slot is still available
        service_id = data.get('service_id')
        service = Service.query.get(service_id)
        duration = service.duration_minutes if service else 60
        
        is_available, reason = check_slot_available(
            estimator_id, 
            preferred_datetime, 
            duration_minutes=duration
        )
        
        if not is_available:
            return jsonify({'error': reason or 'Time slot no longer available'}), 409
        
        # Create the appointment
        appointment = Appointment(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            email=email,
            phone=data.get('phone', '').strip(),
            preferred_date_time=preferred_datetime,
            service_id=service_id,
            estimator_id=estimator_id,
            status='New'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Appointment booked successfully',
            'appointment_id': appointment.id,
            'details': {
                'service': service.name if service else 'Unknown',
                'date': booking_date.isoformat(),
                'time': data['time']
            }
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Booking failed: {str(e)}'}), 500
