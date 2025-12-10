from flask import Blueprint, jsonify, request, current_app, url_for
from app.models import Estimator, Service, Availability, Appointment, db
from app.modules.availability_service import get_available_slots, check_slot_available
from app.modules.security import rate_limiter
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import stripe

booking_api_bp = Blueprint('booking_api', __name__, url_prefix='/api/booking')

# Payment hold duration (minutes) - how long a pending payment reservation lasts
PAYMENT_HOLD_MINUTES = 15


@booking_api_bp.route('/estimators')
@rate_limiter.exempt
def get_estimators():
    """Get all active estimators for booking selection.
    
    Returns estimators linked to employee users with their details.
    """
    estimators = Estimator.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'user_id': e.user_id,
        'email': e.user.email if e.user else None,
        'display_name': f"{e.user.first_name or ''} {e.user.last_name or ''}".strip() or e.name if e.user else e.name,
        'job_title': e.user.job_title if e.user else None,
        'avatar_url': e.user.avatar_url if e.user else None
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
        'price': float(s.price) if s.price else 0,
        'icon': s.icon or 'fa-clipboard-list',
        'requires_payment': s.price is not None and s.price > 0
    } for s in services])


@booking_api_bp.route('/slots')
@rate_limiter.exempt
def get_slots():
    """Get available time slots for a specific estimator and date.
    
    Excludes slots that are:
    - Already booked
    - Held for pending payment (within PAYMENT_HOLD_MINUTES)
    """
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
        
        # Also filter out slots held for pending payments
        now = datetime.utcnow()
        pending_appointments = Appointment.query.filter(
            Appointment.estimator_id == estimator_id,
            Appointment.payment_status == 'pending',
            Appointment.payment_expires_at > now
        ).all()
        
        pending_times = set()
        for appt in pending_appointments:
            if appt.preferred_date_time and appt.preferred_date_time.date() == target_date:
                pending_times.add(appt.preferred_date_time.time())
        
        # Remove slots that overlap with pending payments
        available_slots = [s for s in slots if s not in pending_times]
        
        return jsonify({
            'slots': [s.strftime('%H:%M') for s in available_slots]
        })
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@booking_api_bp.route('/create', methods=['POST'])
@rate_limiter.exempt
def create_booking():
    """Create a new appointment booking.
    
    For paid services: Creates appointment with status='pending_payment' and returns Stripe checkout URL.
    For free services: Creates appointment with status='New' immediately.
    """
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
        
        # Determine if payment is required (explicit flag, not just price > 0)
        requires_payment = service and service.requires_payment and service.price and service.price > 0
        
        # Create the appointment
        appointment = Appointment(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            email=email,
            phone=data.get('phone', '').strip(),
            preferred_date_time=preferred_datetime,
            service_id=service_id,
            estimator_id=estimator_id,
            status='pending_payment' if requires_payment else 'New',
            payment_status='pending' if requires_payment else 'not_required',
            payment_amount=Decimal(str(service.price)) if requires_payment else None,
            payment_expires_at=datetime.utcnow() + timedelta(minutes=PAYMENT_HOLD_MINUTES) if requires_payment else None
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # If payment required, create Stripe checkout session
        if requires_payment:
            try:
                checkout_url = create_stripe_checkout_session(appointment, service)
                return jsonify({
                    'success': True,
                    'requires_payment': True,
                    'checkout_url': checkout_url,
                    'appointment_id': appointment.id,
                    'expires_in_minutes': PAYMENT_HOLD_MINUTES
                })
            except Exception as e:
                # Rollback if Stripe fails
                db.session.delete(appointment)
                db.session.commit()
                current_app.logger.error(f"Stripe checkout creation failed: {e}")
                return jsonify({'error': 'Payment processing unavailable. Please try again.'}), 500
        
        # Free booking - return success immediately
        return jsonify({
            'success': True,
            'requires_payment': False,
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
        current_app.logger.error(f"Booking failed: {e}")
        return jsonify({'error': f'Booking failed: {str(e)}'}), 500


def create_stripe_checkout_session(appointment, service):
    """Create a Stripe checkout session for the appointment.
    
    Returns the checkout URL to redirect the user to.
    """
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    domain_url = current_app.config.get('SITE_URL', request.url_root.rstrip('/'))
    
    # Format price for Stripe (cents)
    price_cents = int(float(service.price) * 100)
    
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'{service.name} Appointment',
                    'description': f'Appointment on {appointment.preferred_date_time.strftime("%B %d, %Y at %I:%M %p")}',
                },
                'unit_amount': price_cents,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=domain_url + url_for('booking_api.payment_success') + f'?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=domain_url + url_for('booking_api.payment_cancel') + f'?appointment_id={appointment.id}',
        metadata={
            'appointment_id': appointment.id,
            'type': 'booking_payment'
        },
        expires_at=int((datetime.utcnow() + timedelta(minutes=PAYMENT_HOLD_MINUTES)).timestamp()),
        customer_email=appointment.email
    )
    
    # Save session ID to appointment
    appointment.stripe_checkout_session_id = checkout_session.id
    db.session.commit()
    
    return checkout_session.url


@booking_api_bp.route('/payment/success')
def payment_success():
    """Handle successful payment redirect from Stripe."""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'Missing session ID'}), 400
    
    try:
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        session = stripe.checkout.Session.retrieve(session_id)
        
        appointment_id = session.metadata.get('appointment_id')
        if appointment_id:
            appointment = Appointment.query.get(int(appointment_id))
            if appointment and appointment.payment_status == 'pending':
                appointment.payment_status = 'paid'
                appointment.status = 'New'  # Promote from pending_payment
                appointment.stripe_payment_intent_id = session.payment_intent
                appointment.payment_expires_at = None  # Clear the expiry
                db.session.commit()
                
                current_app.logger.info(f"Booking payment completed for appointment {appointment_id}")
                
                # Return success page or redirect
                return jsonify({
                    'success': True,
                    'message': 'Payment successful! Your appointment is confirmed.',
                    'appointment_id': appointment_id
                })
        
        return jsonify({'error': 'Appointment not found'}), 404
        
    except Exception as e:
        current_app.logger.error(f"Payment success handling error: {e}")
        return jsonify({'error': 'Error processing payment confirmation'}), 500


@booking_api_bp.route('/payment/cancel')
def payment_cancel():
    """Handle cancelled payment from Stripe."""
    appointment_id = request.args.get('appointment_id')
    
    if appointment_id:
        try:
            appointment = Appointment.query.get(int(appointment_id))
            if appointment and appointment.payment_status == 'pending':
                # Mark as failed and release the slot
                appointment.payment_status = 'failed'
                appointment.status = 'Cancelled'
                db.session.commit()
                
                current_app.logger.info(f"Booking payment cancelled for appointment {appointment_id}")
        except Exception as e:
            current_app.logger.error(f"Payment cancel handling error: {e}")
    
    return jsonify({
        'success': False,
        'message': 'Payment cancelled. The time slot has been released.'
    })


@booking_api_bp.route('/cleanup-expired', methods=['POST'])
def cleanup_expired_holds():
    """Clean up expired payment holds (called by worker/cron).
    
    This releases slots that were held for payment but never completed.
    """
    now = datetime.utcnow()
    
    expired_appointments = Appointment.query.filter(
        Appointment.payment_status == 'pending',
        Appointment.payment_expires_at < now
    ).all()
    
    count = 0
    for appt in expired_appointments:
        appt.payment_status = 'failed'
        appt.status = 'Expired'
        count += 1
    
    if count > 0:
        db.session.commit()
        current_app.logger.info(f"Cleaned up {count} expired booking payment holds")
    
    return jsonify({'cleaned_up': count})
