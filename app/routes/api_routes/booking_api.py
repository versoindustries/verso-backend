from flask import Blueprint, jsonify, request, current_app, url_for, render_template
from app.models import Estimator, Service, Availability, Appointment, RescheduleRequest, User, db
from flask_login import login_required, current_user
from app.modules.availability_service import get_available_slots, check_slot_available
from app.modules.security import rate_limiter
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import stripe

# API routes for booking
booking_api_bp = Blueprint('booking_api', __name__, url_prefix='/api/booking')

# Public booking page route
booking_pages_public_bp = Blueprint('booking_pages_public', __name__)


@booking_pages_public_bp.route('/booking')
@rate_limiter.exempt
def booking_page():
    """Public standalone booking page with the booking wizard."""
    return render_template('booking/standalone.html')

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


# ============================================================================
# Customer Appointment Management APIs
# Endpoints for logged-in users to manage their own appointments
# ============================================================================

@booking_api_bp.route('/my', methods=['GET'])
@login_required
def get_my_appointments():
    """Get all appointments for the current logged-in user.
    
    Returns appointments matching the user's email address.
    """
    appointments = Appointment.query.filter(
        Appointment.email == current_user.email
    ).order_by(Appointment.preferred_date_time.desc()).all()
    
    now = datetime.utcnow()
    result = []
    for appt in appointments:
        # Check if there's a pending reschedule request
        pending_reschedule = RescheduleRequest.query.filter(
            RescheduleRequest.appointment_id == appt.id,
            RescheduleRequest.status == 'pending'
        ).first()
        
        result.append({
            'id': appt.id,
            'service': appt.service.name if appt.service else 'Consultation',
            'date_time': appt.preferred_date_time.isoformat() if appt.preferred_date_time else None,
            'formatted_date': appt.preferred_date_time.strftime('%b %d, %Y at %I:%M %p') if appt.preferred_date_time else 'TBD',
            'estimator': appt.estimator.name if appt.estimator else 'TBA',
            'status': appt.status,
            'is_past': appt.preferred_date_time < now if appt.preferred_date_time else False,
            'can_cancel': appt.status not in ['Cancelled', 'Completed', 'No Show'] and (
                appt.preferred_date_time > now if appt.preferred_date_time else False
            ),
            'can_reschedule': appt.status not in ['Cancelled', 'Completed', 'No Show'] and (
                appt.preferred_date_time > now if appt.preferred_date_time else False
            ) and not pending_reschedule,
            'pending_reschedule': {
                'id': pending_reschedule.id,
                'proposed_datetime': pending_reschedule.proposed_datetime.strftime('%b %d, %Y at %I:%M %p'),
                'reason': pending_reschedule.reason
            } if pending_reschedule else None,
            'notes': appt.notes
        })
    
    return jsonify({'appointments': result})


@booking_api_bp.route('/my/<int:appointment_id>', methods=['GET'])
@login_required
def get_my_appointment_detail(appointment_id):
    """Get details of a specific appointment owned by the current user."""
    appt = Appointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if appt.email.lower() != current_user.email.lower():
        return jsonify({'error': 'Appointment not found'}), 404
    
    now = datetime.utcnow()
    pending_reschedule = RescheduleRequest.query.filter(
        RescheduleRequest.appointment_id == appt.id,
        RescheduleRequest.status == 'pending'
    ).first()
    
    return jsonify({
        'id': appt.id,
        'first_name': appt.first_name,
        'last_name': appt.last_name,
        'email': appt.email,
        'phone': appt.phone,
        'service': {
            'id': appt.service.id,
            'name': appt.service.name,
            'duration': appt.service.duration_minutes
        } if appt.service else None,
        'estimator': {
            'id': appt.estimator.id,
            'name': appt.estimator.name
        } if appt.estimator else None,
        'date_time': appt.preferred_date_time.isoformat() if appt.preferred_date_time else None,
        'formatted_date': appt.preferred_date_time.strftime('%b %d, %Y at %I:%M %p') if appt.preferred_date_time else 'TBD',
        'status': appt.status,
        'is_past': appt.preferred_date_time < now if appt.preferred_date_time else False,
        'can_cancel': appt.status not in ['Cancelled', 'Completed', 'No Show'] and (
            appt.preferred_date_time > now if appt.preferred_date_time else False
        ),
        'can_reschedule': appt.status not in ['Cancelled', 'Completed', 'No Show'] and (
            appt.preferred_date_time > now if appt.preferred_date_time else False
        ) and not pending_reschedule,
        'payment_status': appt.payment_status,
        'notes': appt.notes,
        'pending_reschedule': {
            'id': pending_reschedule.id,
            'proposed_datetime': pending_reschedule.proposed_datetime.isoformat(),
            'formatted_datetime': pending_reschedule.proposed_datetime.strftime('%b %d, %Y at %I:%M %p'),
            'reason': pending_reschedule.reason,
            'status': pending_reschedule.status
        } if pending_reschedule else None,
        'reschedule_history': [{
            'id': r.id,
            'proposed_datetime': r.proposed_datetime.strftime('%b %d, %Y at %I:%M %p'),
            'reason': r.reason,
            'status': r.status,
            'admin_notes': r.admin_notes,
            'created_at': r.created_at.strftime('%b %d, %Y') if r.created_at else None
        } for r in appt.reschedule_requests if r.status != 'pending']
    })


@booking_api_bp.route('/my/<int:appointment_id>/cancel', methods=['POST'])
@login_required  
def cancel_my_appointment(appointment_id):
    """Customer cancels their own appointment.
    
    Handles cancellation policy and refunds based on service configuration.
    
    Body (optional):
    - reason: cancellation reason
    
    Returns:
    - success: whether cancellation was processed
    - refund_info: details about any refund (amount, status, policy applied)
    """
    appt = Appointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if appt.email.lower() != current_user.email.lower():
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Check if appointment can be cancelled
    if appt.status in ['Cancelled', 'Completed', 'No Show']:
        return jsonify({'error': f'Cannot cancel appointment with status: {appt.status}'}), 400
    
    now = datetime.utcnow()
    if appt.preferred_date_time and appt.preferred_date_time < now:
        return jsonify({'error': 'Cannot cancel past appointments'}), 400
    
    data = request.json or {}
    reason = data.get('reason', 'Cancelled by customer')
    
    # Get cancellation policy from service
    service = appt.service
    policy = 'manual'  # Default
    refund_percentage = 0
    refund_info = None
    
    if service:
        policy = service.cancellation_policy or 'manual'
        window_hours = service.cancellation_window_hours or 24
        
        # Check if within free cancellation window
        hours_until_appt = 0
        if appt.preferred_date_time:
            hours_until_appt = (appt.preferred_date_time - now).total_seconds() / 3600
        
        # Determine refund based on policy and timing
        if policy == 'full_refund':
            refund_percentage = 100
        elif policy == 'partial_refund':
            if hours_until_appt >= window_hours:
                refund_percentage = 100  # Full refund if cancelled early enough
            else:
                refund_percentage = service.refund_percentage or 50
        elif policy == 'no_refund':
            refund_percentage = 0
        elif policy == 'deposit_only':
            # Refund everything except the deposit
            deposit_pct = service.deposit_percentage or 20
            refund_percentage = 100 - deposit_pct
        # 'manual' = no automatic refund, admin handles it
    
    # Process refund if appointment was paid and policy allows
    if appt.payment_status == 'paid' and appt.stripe_payment_intent_id and refund_percentage > 0:
        try:
            stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
            payment_amount_cents = int(float(appt.payment_amount or 0) * 100)
            refund_amount_cents = int(payment_amount_cents * refund_percentage / 100)
            
            if refund_amount_cents > 0:
                refund = stripe.Refund.create(
                    payment_intent=appt.stripe_payment_intent_id,
                    amount=refund_amount_cents,
                    reason='requested_by_customer'
                )
                
                # Update appointment with refund info
                appt.stripe_refund_id = refund.id
                appt.refund_amount = refund_amount_cents / 100
                appt.refund_reason = reason
                appt.refunded_at = now
                appt.payment_status = 'refunded' if refund_percentage == 100 else 'partial_refund'
                
                refund_info = {
                    'processed': True,
                    'amount': refund_amount_cents / 100,
                    'percentage': refund_percentage,
                    'policy': policy,
                    'refund_id': refund.id
                }
                
                current_app.logger.info(
                    f"Processed ${refund_amount_cents/100:.2f} refund for appointment {appointment_id}"
                )
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe refund error for appointment {appointment_id}: {e}")
            # Don't fail the cancellation, just note that refund needs manual processing
            refund_info = {
                'processed': False,
                'error': 'Refund requires manual processing',
                'policy': policy,
                'expected_amount': float(appt.payment_amount or 0) * refund_percentage / 100
            }
    elif appt.payment_status == 'paid' and policy == 'manual':
        refund_info = {
            'processed': False,
            'message': 'Refund will be reviewed by our team',
            'policy': 'manual'
        }
    
    # Update appointment
    old_status = appt.status
    appt.status = 'Cancelled'
    appt.cancellation_policy_applied = policy
    
    # Add cancellation note
    refund_note = f" Refund: ${appt.refund_amount:.2f}" if appt.refund_amount else ""
    cancel_note = f"[{now.strftime('%Y-%m-%d %H:%M')}] Cancelled by customer. Reason: {reason}{refund_note}"
    if appt.staff_notes:
        appt.staff_notes = appt.staff_notes + '\n' + cancel_note
    else:
        appt.staff_notes = cancel_note
    
    # Cancel any pending reschedule requests
    pending_reschedules = RescheduleRequest.query.filter(
        RescheduleRequest.appointment_id == appt.id,
        RescheduleRequest.status == 'pending'
    ).all()
    for r in pending_reschedules:
        r.status = 'cancelled'
        r.admin_notes = 'Appointment was cancelled by customer'
    
    db.session.commit()
    
    current_app.logger.info(f"Customer cancelled appointment {appointment_id} (was {old_status}, policy: {policy})")
    
    response = {
        'success': True,
        'message': 'Appointment cancelled successfully',
        'appointment_id': appt.id
    }
    
    if refund_info:
        response['refund'] = refund_info
    
    return jsonify(response)


@booking_api_bp.route('/my/<int:appointment_id>/reschedule', methods=['POST'])
@login_required
def request_reschedule_my_appointment(appointment_id):
    """Customer requests to reschedule their appointment.
    
    Creates a RescheduleRequest that needs admin/staff approval.
    
    Body:
    - new_date: YYYY-MM-DD date string
    - new_time: HH:MM time string (24hr format)
    - reason: reason for reschedule (optional)
    """
    appt = Appointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if appt.email.lower() != current_user.email.lower():
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Check if appointment can be rescheduled
    if appt.status in ['Cancelled', 'Completed', 'No Show']:
        return jsonify({'error': f'Cannot reschedule appointment with status: {appt.status}'}), 400
    
    now = datetime.utcnow()
    if appt.preferred_date_time and appt.preferred_date_time < now:
        return jsonify({'error': 'Cannot reschedule past appointments'}), 400
    
    # Check for existing pending reschedule request
    existing_pending = RescheduleRequest.query.filter(
        RescheduleRequest.appointment_id == appt.id,
        RescheduleRequest.status == 'pending'
    ).first()
    if existing_pending:
        return jsonify({
            'error': 'There is already a pending reschedule request for this appointment',
            'pending_request': {
                'proposed_datetime': existing_pending.proposed_datetime.strftime('%b %d, %Y at %I:%M %p'),
                'reason': existing_pending.reason
            }
        }), 400
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    new_date = data.get('new_date')
    new_time = data.get('new_time')
    reason = data.get('reason', 'Customer requested reschedule')
    
    if not new_date or not new_time:
        return jsonify({'error': 'new_date and new_time are required'}), 400
    
    try:
        proposed_date = datetime.strptime(new_date, '%Y-%m-%d').date()
        proposed_time = datetime.strptime(new_time, '%H:%M').time()
        proposed_datetime = datetime.combine(proposed_date, proposed_time)
        
        # Validate not in the past
        if proposed_datetime < now:
            return jsonify({'error': 'Cannot reschedule to a past date/time'}), 400
        
        # Check if the slot is available
        service_duration = appt.service.duration_minutes if appt.service else 60
        is_available, availability_reason = check_slot_available(
            appt.estimator_id,
            proposed_datetime,
            duration_minutes=service_duration
        )
        
        if not is_available:
            return jsonify({'error': f'Requested time slot is not available: {availability_reason}'}), 409
        
        # Create reschedule request
        reschedule_request = RescheduleRequest(
            appointment_id=appt.id,
            user_id=current_user.id,
            proposed_datetime=proposed_datetime,
            reason=reason,
            status='pending'
        )
        db.session.add(reschedule_request)
        db.session.commit()
        
        current_app.logger.info(
            f"Customer submitted reschedule request for appointment {appointment_id} "
            f"from {appt.preferred_date_time} to {proposed_datetime}"
        )
        
        return jsonify({
            'success': True,
            'message': 'Reschedule request submitted. You will be notified once it is reviewed.',
            'request_id': reschedule_request.id,
            'proposed_datetime': proposed_datetime.strftime('%b %d, %Y at %I:%M %p')
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date/time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Reschedule request failed: {e}")
        return jsonify({'error': 'Failed to submit reschedule request'}), 500


@booking_api_bp.route('/my/<int:appointment_id>/reschedule/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_my_reschedule_request(appointment_id, request_id):
    """Customer cancels their pending reschedule request."""
    appt = Appointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if appt.email.lower() != current_user.email.lower():
        return jsonify({'error': 'Appointment not found'}), 404
    
    reschedule_request = RescheduleRequest.query.get_or_404(request_id)
    
    # Verify the reschedule request belongs to this appointment
    if reschedule_request.appointment_id != appt.id:
        return jsonify({'error': 'Reschedule request not found'}), 404
    
    if reschedule_request.status != 'pending':
        return jsonify({'error': f'Cannot cancel reschedule request with status: {reschedule_request.status}'}), 400
    
    reschedule_request.status = 'cancelled'
    reschedule_request.admin_notes = 'Cancelled by customer'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Reschedule request cancelled'
    })

