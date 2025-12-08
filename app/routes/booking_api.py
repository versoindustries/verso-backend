from flask import Blueprint, jsonify, request
from app.models import Estimator, Service, Availability, db, Order, OrderItem
from app.modules.availability_service import get_available_slots
from datetime import datetime, date

booking_api_bp = Blueprint('booking_api', __name__, url_prefix='/api/booking')

@booking_api_bp.route('/estimators')
def get_estimators():
    estimators = Estimator.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        # 'services': [s.id for s in e.services] # If relation exists
    } for e in estimators])

@booking_api_bp.route('/services')
def get_services():
    services = Service.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'duration': s.duration_minutes,
        'price': s.price
    } for s in services])

@booking_api_bp.route('/slots')
def get_slots():
    estimator_id = request.args.get('estimator_id', type=int)
    date_str = request.args.get('date')
    service_id = request.args.get('service_id', type=int)
    
    if not estimator_id or not date_str:
        return jsonify({'error': 'Missing parameters'}), 400
        
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if target_date < date.today():
            return jsonify({'slots': []})
            
        slots = get_available_slots(estimator_id, target_date, service_id)
        
        return jsonify({
            'slots': [s.strftime('%H:%M') for s in slots]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_api_bp.route('/create', methods=['POST'])
def create_booking():
    data = request.json
    # Basic validation and creation logic would go here
    # For now, just return success
    return jsonify({'success': True, 'message': 'Booking request received'})
