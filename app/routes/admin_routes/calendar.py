from flask import Blueprint, render_template, request, jsonify, abort, Response
from flask_login import login_required, current_user
from app.modules.auth_manager import admin_required
from app.models import Appointment, Estimator, Service
from app.database import db
from datetime import timedelta, datetime
import pytz

calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')


@calendar_bp.route('/view')
@login_required
@admin_required
def view_calendar():
    return render_template('admin/calendar.html')


@calendar_bp.route('/api/events')
@login_required
@admin_required
def get_events():
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    query = Appointment.query
    if start_str and end_str:
        start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        query = query.filter(Appointment.preferred_date_time >= start_date, Appointment.preferred_date_time <= end_date)
        
    appointments = query.all()
    events = []
    
    for appt in appointments:
        start = appt.preferred_date_time.isoformat()
        if not start.endswith('Z'):
             start += 'Z'
        
        # Phase 2: Use service duration instead of hardcoded 1 hour
        duration_minutes = 60  # Default
        if appt.service and appt.service.duration_minutes:
            duration_minutes = appt.service.duration_minutes
             
        end_dt = appt.preferred_date_time + timedelta(minutes=duration_minutes)
        end = end_dt.isoformat()
        if not end.endswith('Z'):
            end += 'Z'
            
        events.append({
            'id': appt.id,
            'title': f"{appt.first_name} {appt.last_name} ({appt.service.name if appt.service else 'Service'})",
            'start': start,
            'end': end,
            'extendedProps': {
                'description': f"Email: {appt.email}, Phone: {appt.phone}, Estimator: {appt.estimator.name if appt.estimator else 'None'}"
            }
        })
        
    return jsonify(events)


@calendar_bp.route('/api/event/<int:event_id>/update', methods=['POST'])
@login_required
@admin_required
def update_event(event_id):
    appt = Appointment.query.get_or_404(event_id)
    new_start_str = request.form.get('start')
    
    if new_start_str:
        try:
            new_start = datetime.fromisoformat(new_start_str.replace('Z', '+00:00'))
            new_start_utc = new_start.astimezone(pytz.utc).replace(tzinfo=None)
            
            appt.preferred_date_time = new_start_utc
            db.session.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400
            
    return jsonify({'status': 'error', 'message': 'No start time provided'}), 400


# Phase 2: ICS Feed Export
@calendar_bp.route('/ics/<int:estimator_id>.ics')
@login_required
def ics_feed(estimator_id):
    """
    Generate ICS (iCalendar) feed for an estimator.
    Subscribe to this URL in Google Calendar, Outlook, etc.
    """
    from icalendar import Calendar, Event
    
    estimator = Estimator.query.get_or_404(estimator_id)
    
    # Only allow access to own calendar or admin
    if current_user.estimator_profile and current_user.estimator_profile.id != estimator_id:
        if not current_user.has_role('admin'):
            abort(403)
    
    # Get future appointments
    now = datetime.utcnow()
    appointments = Appointment.query.filter(
        Appointment.estimator_id == estimator_id,
        Appointment.preferred_date_time >= now - timedelta(days=7)  # Include recent past
    ).order_by(Appointment.preferred_date_time).limit(100).all()
    
    # Create iCal calendar
    cal = Calendar()
    cal.add('prodid', '-//Verso Industries//Calendar//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', f'{estimator.name} - Appointments')
    
    for appt in appointments:
        event = Event()
        event.add('summary', f"{appt.first_name} {appt.last_name}")
        event.add('dtstart', appt.preferred_date_time.replace(tzinfo=pytz.UTC))
        
        # Calculate end time from service duration
        duration = 60  # Default
        if appt.service and appt.service.duration_minutes:
            duration = appt.service.duration_minutes
        end_dt = appt.preferred_date_time + timedelta(minutes=duration)
        event.add('dtend', end_dt.replace(tzinfo=pytz.UTC))
        
        # Description with contact info
        description = f"Service: {appt.service.name if appt.service else 'N/A'}\n"
        description += f"Phone: {appt.phone}\n"
        description += f"Email: {appt.email}\n"
        if appt.notes:
            description += f"Notes: {appt.notes}"
        event.add('description', description)
        
        event.add('uid', f'appt-{appt.id}@verso.industries')
        event.add('created', appt.created_at.replace(tzinfo=pytz.UTC) if appt.created_at else now.replace(tzinfo=pytz.UTC))
        
        if appt.location:
            event.add('location', appt.location.address or appt.location.name)
        
        cal.add_component(event)
    
    response = Response(cal.to_ical(), mimetype='text/calendar')
    response.headers['Content-Disposition'] = f'attachment; filename={estimator.name.replace(" ", "_")}_calendar.ics'
    return response

