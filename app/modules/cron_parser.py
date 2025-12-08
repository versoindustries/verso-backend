"""
Phase 8: Cron Expression Parser

Simple cron schedule parser supporting:
- Standard intervals: @hourly, @daily, @weekly, @monthly
- Basic cron expressions: minute hour day-of-month month day-of-week

This is a lightweight parser that doesn't require external dependencies.
"""

from datetime import datetime, timedelta
from typing import Optional


def parse_schedule(schedule: str, from_time: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse a schedule string and return the next run time.
    
    Args:
        schedule: Schedule string (@hourly, @daily, @weekly, @monthly, or cron expression)
        from_time: Base time to calculate from (defaults to now)
    
    Returns:
        Next run time as datetime, or None if invalid schedule
    """
    if from_time is None:
        from_time = datetime.utcnow()
    
    schedule = schedule.strip().lower()
    
    # Handle simple interval shortcuts
    if schedule == '@hourly':
        return next_hour(from_time)
    elif schedule == '@daily':
        return next_day(from_time)
    elif schedule == '@weekly':
        return next_week(from_time)
    elif schedule == '@monthly':
        return next_month(from_time)
    elif schedule.startswith('@every'):
        return parse_interval(schedule, from_time)
    else:
        # Try to parse as cron expression
        return parse_cron_expression(schedule, from_time)


def next_hour(from_time: datetime) -> datetime:
    """Return the start of the next hour."""
    return from_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def next_day(from_time: datetime, hour: int = 0, minute: int = 0) -> datetime:
    """Return the specified time on the next day."""
    next_dt = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_dt <= from_time:
        next_dt += timedelta(days=1)
    return next_dt


def next_week(from_time: datetime, weekday: int = 0, hour: int = 0, minute: int = 0) -> datetime:
    """
    Return the specified time on the specified weekday of next week.
    weekday: 0=Monday, 6=Sunday
    """
    next_dt = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    days_ahead = weekday - from_time.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    next_dt += timedelta(days=days_ahead)
    return next_dt


def next_month(from_time: datetime, day: int = 1, hour: int = 0, minute: int = 0) -> datetime:
    """Return the specified day and time of the next month."""
    year = from_time.year
    month = from_time.month + 1
    if month > 12:
        month = 1
        year += 1
    
    # Handle edge case for days that don't exist in some months
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    day = min(day, max_day)
    
    return datetime(year, month, day, hour, minute, 0)


def parse_interval(schedule: str, from_time: datetime) -> Optional[datetime]:
    """
    Parse @every interval schedules like @every 30m, @every 2h, @every 1d.
    """
    try:
        # Remove '@every ' prefix
        interval_str = schedule.replace('@every', '').strip()
        
        # Parse the interval
        if interval_str.endswith('m'):
            minutes = int(interval_str[:-1])
            return from_time + timedelta(minutes=minutes)
        elif interval_str.endswith('h'):
            hours = int(interval_str[:-1])
            return from_time + timedelta(hours=hours)
        elif interval_str.endswith('d'):
            days = int(interval_str[:-1])
            return from_time + timedelta(days=days)
        else:
            return None
    except (ValueError, IndexError):
        return None


def parse_cron_expression(cron_expr: str, from_time: datetime) -> Optional[datetime]:
    """
    Parse basic cron expression (minute hour day-of-month month day-of-week).
    
    Supports:
    - Specific values: 0 9 * * * (9:00 AM daily)
    - Asterisks for "any"
    
    This is a simplified parser. For full cron support, consider using croniter.
    """
    try:
        parts = cron_expr.split()
        if len(parts) != 5:
            return None
        
        minute, hour, day, month, weekday = parts
        
        # Start from the current time and find the next matching time
        next_dt = from_time.replace(second=0, microsecond=0)
        
        # Simple case: specific minute and hour, any day
        if minute != '*' and hour != '*' and day == '*' and month == '*' and weekday == '*':
            target_minute = int(minute)
            target_hour = int(hour)
            next_dt = next_dt.replace(hour=target_hour, minute=target_minute)
            if next_dt <= from_time:
                next_dt += timedelta(days=1)
            return next_dt
        
        # More complex expressions would need a full cron parser
        # For now, fall back to daily at the specified time if hour/minute are set
        if minute != '*' and hour != '*':
            target_minute = int(minute)
            target_hour = int(hour)
            next_dt = next_dt.replace(hour=target_hour, minute=target_minute)
            if next_dt <= from_time:
                next_dt += timedelta(days=1)
            return next_dt
        
        # If we can't parse, return None
        return None
        
    except (ValueError, IndexError):
        return None


def get_schedule_description(schedule: str) -> str:
    """Return a human-readable description of the schedule."""
    schedule = schedule.strip().lower()
    
    if schedule == '@hourly':
        return "Every hour"
    elif schedule == '@daily':
        return "Daily at midnight"
    elif schedule == '@weekly':
        return "Every Monday at midnight"
    elif schedule == '@monthly':
        return "First day of each month"
    elif schedule.startswith('@every'):
        interval = schedule.replace('@every', '').strip()
        return f"Every {interval}"
    else:
        # Try to describe cron expression
        parts = schedule.split()
        if len(parts) == 5:
            minute, hour, day, month, weekday = parts
            if minute != '*' and hour != '*' and day == '*' and month == '*' and weekday == '*':
                return f"Daily at {hour}:{minute.zfill(2)}"
        return f"Schedule: {schedule}"
