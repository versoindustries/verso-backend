"""
Phase 17: Scheduling Service Module

Core business logic for advanced scheduling:
- Slot generation based on appointment types
- Resource availability and conflict detection
- Waitlist processing
- Check-in token generation
"""
from datetime import datetime, timedelta, date, time
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy import and_, or_
from app.database import db
from app.models import (
    Appointment, AppointmentType, Resource, ResourceBooking, 
    Waitlist, BookingPolicy, CheckInToken, Estimator, 
    Availability, AvailabilityException
)
from app.modules.availability_service import get_estimator_availability, get_booked_slots

def get_appointment_type_slots(
    appointment_type_id: int, 
    target_date: date, 
    location_id: Optional[int] = None
) -> List[datetime]:
    """
    Get available start times for a specific appointment type on a date.
    Checks:
    1. Staff availability (if type has preferred/required staff or any staff)
    2. Resource availability (if type requires resource)
    3. Buffer times from appointment type
    """
    appt_type = AppointmentType.query.get(appointment_type_id)
    if not appt_type:
        return []
        
    duration = appt_type.duration_minutes
    buffer_before = appt_type.buffer_before
    buffer_after = appt_type.buffer_after
    total_duration = duration + buffer_after  # We need slot for duration + after buffer (before buffer handled by gap)

    # 1. Get eligible estimators
    # For now, get all active estimators. Phase 17.1 says "service-based scheduling with staff assignment"
    # We assume all estimators perform all services unless restricted (future enhancement)
    estimators = Estimator.query.all()
    
    available_slots = set()
    
    for estimator in estimators:
        # Get base availability for this estimator
        est_slots = get_available_slots_for_type(
            estimator.id, 
            target_date, 
            duration, 
            buffer_before, 
            buffer_after
        )
        
        # Filter by resource availability if needed
        if appt_type.required_resource_type:
            est_slots = filter_slots_by_resource(
                est_slots, 
                appt_type.required_resource_type, 
                duration,
                location_id
            )
            
        available_slots.update(est_slots)
        
    return sorted(list(available_slots))

def get_available_slots_for_type(
    estimator_id: int, 
    target_date: date, 
    duration_minutes: int, 
    buffer_before: int, 
    buffer_after: int
) -> List[datetime]:
    """Helper to get slots for specific estimator considering buffers."""
    
    # 1. Get raw working hours
    availabilities = get_estimator_availability(estimator_id, target_date)
    if not availabilities:
        return []
        
    # 2. Get existing bookings to calculate gaps
    booked_ranges = get_booked_slots(estimator_id, target_date)
    # Add buffer logic to booked ranges? 
    # Existing `get_booked_slots` returns (start, end).
    # We should treat booked_start - buffer_after (of prev appt) and booked_end + buffer_before (of next appt)
    # But for simplicity, we assume generic buffer or check gaps.
    
    # Let's generate potential slots every 15 mins and check if they fit
    interval = 15
    slots = []
    
    for start_time_range, end_time_range in availabilities:
        # Construct full datetime
        current = datetime.combine(target_date, start_time_range)
        end_abs = datetime.combine(target_date, end_time_range)
        
        while current + timedelta(minutes=duration_minutes) <= end_abs:
            slot_start = current
            slot_end = current + timedelta(minutes=duration_minutes)
            
            # Check conflicts
            is_conflict = False
            for b_start, b_end in booked_ranges:
                # Check overlap including buffers
                # Effective slot needed: [start - buffer_before, end + buffer_after]
                needed_start = slot_start - timedelta(minutes=buffer_before)
                needed_end = slot_end + timedelta(minutes=buffer_after)
                
                if (needed_start < b_end) and (needed_end > b_start):
                    is_conflict = True
                    break
            
            if not is_conflict:
                slots.append(slot_start)
                
            current += timedelta(minutes=interval)
            
    return slots

def filter_slots_by_resource(
    slots: List[datetime], 
    resource_type: str, 
    duration_minutes: int,
    location_id: Optional[int] = None
) -> List[datetime]:
    """Filter slots where at least one resource of type is available."""
    valid_slots = []
    
    resources_query = Resource.query.filter_by(resource_type=resource_type, is_active=True)
    if location_id:
        resources_query = resources_query.filter_by(location_id=location_id)
    resources = resources_query.all()
    
    if not resources:
        return []

    for slot in slots:
        slot_end = slot + timedelta(minutes=duration_minutes)
        
        # Check if ANY resource is free
        resource_available = False
        for res in resources:
            if check_resource_availability(res.id, slot, slot_end):
                resource_available = True
                break
        
        if resource_available:
            valid_slots.append(slot)
            
    return valid_slots

def check_resource_availability(resource_id: int, start: datetime, end: datetime) -> bool:
    """Check if a resource is free during range."""
    conflict = ResourceBooking.query.filter(
        ResourceBooking.resource_id == resource_id,
        ResourceBooking.status != 'cancelled',
        ResourceBooking.start_time < end,
        ResourceBooking.end_time > start
    ).first()
    return conflict is None

def book_with_resources(
    appointment_data: Dict[str, Any], 
    resource_requirements: List[str] = None
) -> Tuple[Optional[Appointment], Optional[str]]:
    """
    Create appointment and book required resources atomically.
    appointment_data: dict compatible with Appointment model
    resource_requirements: list of resource_types needed
    """
    try:
        # Create appointment
        appt = Appointment(**appointment_data)
        db.session.add(appt)
        db.session.flush()  # Get ID
        
        # Handle resources
        if resource_requirements:
            start = appt.preferred_date_time
            # Get duration
            duration = 60
            if appt.appointment_type:
                duration = appt.appointment_type.duration_minutes
            elif appt.service:
                duration = appt.service.duration_minutes
            
            end = start + timedelta(minutes=duration)
            
            for res_type in resource_requirements:
                # Find available resource
                resources = Resource.query.filter_by(resource_type=res_type, is_active=True).all()
                booked_res = None
                for res in resources:
                    if check_resource_availability(res.id, start, end):
                        booked_res = res
                        break
                
                if not booked_res:
                    db.session.rollback()
                    return None, f"No available {res_type} for this time slot"
                
                # Book it
                res_booking = ResourceBooking(
                    resource_id=booked_res.id,
                    appointment_id=appt.id,
                    start_time=start,
                    end_time=end,
                    booked_by_id=appt.estimator_id, # Or system user
                    status='confirmed'
                )
                db.session.add(res_booking)
        
        # Handle Waitlist: If this slot was offered to someone, or if we need to remove waitlist entry
        # Logic to remove *this user's* waitlist entry if they booked
        if appt.email and appt.appointment_type_id:
            wl_entry = Waitlist.query.filter_by(
                email=appt.email, 
                appointment_type_id=appt.appointment_type_id,
                status='offered'
            ).first() or Waitlist.query.filter_by(
                email=appt.email, 
                appointment_type_id=appt.appointment_type_id,
                status='waiting'
            ).first()
            
            if wl_entry:
                wl_entry.status = 'booked'
                wl_entry.booked_appointment_id = appt.id
        
        db.session.commit()
        return appt, None
        
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def process_waitlist(appointment_type_id: int):
    """
    Check waitlist for a specific type and make offers if slots are open.
    Should be run via worker task periodically or after cancellation.
    """
    # 1. Check for expired offers
    expired = Waitlist.query.filter(
        Waitlist.appointment_type_id == appointment_type_id,
        Waitlist.status == 'offered',
        Waitlist.offer_expires_at < datetime.utcnow()
    ).all()
    
    for entry in expired:
        entry.status = 'expired'
        # Notify user offer expired?
    
    db.session.commit()
    
    # 2. Check for available slots (simplified: just check if next week has any)
    # Real logic: find canceled slot, offer to top of list
    # Implementation: Admin manually triggers offer, or auto-trigger available?
    # Roadmap: "Automatic Waitlist Offers: Email when slot opens"
    
    # Get top waiting
    next_in_line = Waitlist.query.filter(
        Waitlist.appointment_type_id == appointment_type_id,
        Waitlist.status == 'waiting'
    ).order_by(Waitlist.priority.desc(), Waitlist.created_at.asc()).first()
    
    if next_in_line:
        # In a real system, we'd check if a slot MATCHING their preference opened
        # For now, just a placeholder for the logic
        pass

def generate_checkin_token(appointment_id: int) -> str:
    """Generate and save a check-in token."""
    token_str = CheckInToken.generate_token()
    token = CheckInToken(
        appointment_id=appointment_id,
        token=token_str,
        expires_at=datetime.utcnow() + timedelta(days=1) # Valid for 24 hours around appt
    )
    db.session.add(token)
    db.session.commit()
    return token_str
