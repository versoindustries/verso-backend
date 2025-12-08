"""
Phase 2: Availability Service Module

Core logic for availability management, conflict detection, and slot generation.
"""
from datetime import datetime, date, time, timedelta
from typing import List, Tuple, Optional
from app.database import db
from app.models import (
    Availability, AvailabilityException, Appointment, Estimator, Service, BusinessConfig
)


def get_business_config() -> dict:
    """Get business configuration settings."""
    configs = BusinessConfig.query.all()
    return {c.setting_name: c.setting_value for c in configs}


def get_estimator_availability(estimator_id: int, target_date: date) -> List[Tuple[time, time]]:
    """
    Get available time ranges for an estimator on a specific date.
    
    Checks:
    1. Recurring weekly availability
    2. Exception dates (blocked or custom hours)
    
    Returns list of (start_time, end_time) tuples.
    """
    # Check for exception on this date first
    exception = AvailabilityException.query.filter_by(
        estimator_id=estimator_id,
        date=target_date
    ).first()
    
    if exception:
        if exception.is_blocked:
            return []  # Fully blocked, no availability
        if exception.custom_start_time and exception.custom_end_time:
            return [(exception.custom_start_time, exception.custom_end_time)]
    
    # Get recurring availability for this day of week
    day_of_week = target_date.weekday()  # Monday=0, Sunday=6
    availabilities = Availability.query.filter_by(
        estimator_id=estimator_id,
        day_of_week=day_of_week
    ).order_by(Availability.start_time).all()
    
    if not availabilities:
        return []
    
    return [(a.start_time, a.end_time) for a in availabilities]


def get_booked_slots(estimator_id: int, target_date: date) -> List[Tuple[datetime, datetime]]:
    """
    Get all booked appointment slots for an estimator on a specific date.
    
    Returns list of (start, end) datetime tuples.
    """
    config = get_business_config()
    
    # Create datetime range for the target date (in UTC)
    day_start = datetime.combine(target_date, time.min)
    day_end = datetime.combine(target_date, time.max)
    
    appointments = Appointment.query.filter(
        Appointment.estimator_id == estimator_id,
        Appointment.preferred_date_time >= day_start,
        Appointment.preferred_date_time <= day_end
    ).all()
    
    booked = []
    for appt in appointments:
        # Get duration from service or default to 60 minutes
        duration = 60
        if appt.service:
            duration = appt.service.duration_minutes or 60
        
        start = appt.preferred_date_time
        end = start + timedelta(minutes=duration)
        booked.append((start, end))
    
    return booked


def check_slot_available(
    estimator_id: int,
    slot_start: datetime,
    duration_minutes: int = 60,
    buffer_minutes: int = 30
) -> Tuple[bool, Optional[str]]:
    """
    Check if a specific time slot is available for booking.
    
    Returns:
        (True, None) if available
        (False, reason) if not available
    """
    target_date = slot_start.date()
    slot_end = slot_start + timedelta(minutes=duration_minutes)
    slot_start_time = slot_start.time()
    slot_end_time = slot_end.time()
    
    # 1. Check if estimator has availability on this day
    availability_ranges = get_estimator_availability(estimator_id, target_date)
    
    if not availability_ranges:
        return False, "Estimator is not available on this day"
    
    # Check if slot fits within any availability window
    slot_in_availability = False
    for avail_start, avail_end in availability_ranges:
        if slot_start_time >= avail_start and slot_end_time <= avail_end:
            slot_in_availability = True
            break
    
    if not slot_in_availability:
        return False, "Requested time is outside available hours"
    
    # 2. Check for conflicts with existing appointments
    booked_slots = get_booked_slots(estimator_id, target_date)
    
    for booked_start, booked_end in booked_slots:
        # Add buffer time
        buffered_start = booked_start - timedelta(minutes=buffer_minutes)
        buffered_end = booked_end + timedelta(minutes=buffer_minutes)
        
        # Check for overlap
        if slot_start < buffered_end and slot_end > buffered_start:
            return False, "Time slot conflicts with existing appointment"
    
    return True, None


def get_available_slots(
    estimator_id: int,
    target_date: date,
    service_id: Optional[int] = None,
    slot_interval_minutes: int = 30
) -> List[datetime]:
    """
    Generate list of available booking slots for an estimator on a date.
    
    Args:
        estimator_id: The estimator's ID
        target_date: The date to check
        service_id: Optional service ID to get duration from
        slot_interval_minutes: Interval between slot start times
        
    Returns:
        List of datetime objects representing available slot start times
    """
    config = get_business_config()
    buffer_minutes = int(config.get('buffer_time_minutes', 30))
    
    # Get service duration
    duration_minutes = 60
    if service_id:
        service = Service.query.get(service_id)
        if service and service.duration_minutes:
            duration_minutes = service.duration_minutes
    
    # Get availability ranges
    availability_ranges = get_estimator_availability(estimator_id, target_date)
    if not availability_ranges:
        return []
    
    # Get booked slots
    booked_slots = get_booked_slots(estimator_id, target_date)
    
    available_slots = []
    
    for avail_start, avail_end in availability_ranges:
        # Generate slots within this availability window
        current_time = datetime.combine(target_date, avail_start)
        end_time = datetime.combine(target_date, avail_end)
        
        while current_time + timedelta(minutes=duration_minutes) <= end_time:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            # Check if slot conflicts with any booked appointment
            is_available = True
            for booked_start, booked_end in booked_slots:
                buffered_start = booked_start - timedelta(minutes=buffer_minutes)
                buffered_end = booked_end + timedelta(minutes=buffer_minutes)
                
                if current_time < buffered_end and slot_end > buffered_start:
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(current_time)
            
            current_time += timedelta(minutes=slot_interval_minutes)
    
    return available_slots


def get_conflicting_appointments(
    estimator_id: int,
    start: datetime,
    end: datetime
) -> List[Appointment]:
    """
    Find all appointments that conflict with a time range.
    
    Useful for detecting double-booking attempts.
    """
    return Appointment.query.filter(
        Appointment.estimator_id == estimator_id,
        Appointment.preferred_date_time < end,
        # Need to calculate end time dynamically, so we'll be conservative
        Appointment.preferred_date_time >= start - timedelta(hours=2)
    ).all()


def generate_recurring_appointments(
    base_appointment: Appointment,
    recurrence_type: str,  # 'weekly', 'biweekly', 'monthly'
    count: int
) -> List[Appointment]:
    """
    Generate a series of recurring appointments.
    
    Args:
        base_appointment: The original appointment to copy
        recurrence_type: 'weekly', 'biweekly', or 'monthly'
        count: Number of additional appointments to create
        
    Returns:
        List of new Appointment objects (not yet committed to DB)
    """
    intervals = {
        'weekly': timedelta(weeks=1),
        'biweekly': timedelta(weeks=2),
        'monthly': timedelta(days=30)  # Approximation
    }
    
    if recurrence_type not in intervals:
        raise ValueError(f"Invalid recurrence type: {recurrence_type}")
    
    interval = intervals[recurrence_type]
    new_appointments = []
    
    for i in range(1, count + 1):
        new_datetime = base_appointment.preferred_date_time + (interval * i)
        
        new_appt = Appointment(
            first_name=base_appointment.first_name,
            last_name=base_appointment.last_name,
            phone=base_appointment.phone,
            email=base_appointment.email,
            preferred_date_time=new_datetime,
            service_id=base_appointment.service_id,
            estimator_id=base_appointment.estimator_id,
            location_id=base_appointment.location_id,
            is_recurring=True,
            recurring_parent_id=base_appointment.id
        )
        new_appointments.append(new_appt)
    
    return new_appointments


def seed_default_availability(estimator_id: int):
    """
    Seed default 9-5 Mon-Fri availability for an estimator.
    Useful for initial setup.
    """
    existing = Availability.query.filter_by(estimator_id=estimator_id).first()
    if existing:
        return  # Don't override if already set
    
    # Monday through Friday
    for day in range(5):
        availability = Availability(
            estimator_id=estimator_id,
            day_of_week=day,
            start_time=time(9, 0),  # 9:00 AM
            end_time=time(17, 0)    # 5:00 PM
        )
        db.session.add(availability)
    
    db.session.commit()
