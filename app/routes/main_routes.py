import os
from datetime import datetime, time, timedelta
import icalendar
import pytz
import requests
from dateutil import parser
from flask import (Blueprint, Response, current_app, flash, jsonify,
                   redirect, render_template, request, session,
                   url_for)
from flask_login import current_user, login_required
from markupsafe import Markup
from pytz import UTC

from app import csrf, db, mail
from app.forms import AcceptTOSForm, EstimateRequestForm, ContactForm
from app.models import Appointment, Estimator, Service, User, ContactFormSubmission
from app.modules.locations import get_locations
import random

main = Blueprint('main_routes', __name__)

@main.context_processor
def combined_context_processor():
    locations = get_locations()
    erf_form = EstimateRequestForm()
    return dict(locations=locations, erf_form=erf_form)

@main.route('/')
def index():
    # For regular user visitors, include the gallery logic
    image_folder = os.path.join(current_app.static_folder, 'images/gallery')
    gallery_images = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]
    random.shuffle(gallery_images)

    page = int(request.args.get('page', 1))
    per_page = 5
    total_images = len(gallery_images)
    start = (page - 1) * per_page
    end = start + per_page

    paginated_images = gallery_images[start:end]
    has_more = end < total_images
    # Check for bot user agents in the request
    bot_agents = ['Googlebot', 'Bingbot', 'Slurp', 'DuckDuckBot', 'Baiduspider', 'YandexBot', 'Sogou']
    user_agent = request.headers.get('User-Agent', '')
    if any(bot in user_agent for bot in bot_agents):
        # Serve a static version of the homepage suitable for indexing
        return render_template('index.html', gallery_images=paginated_images, has_more=has_more, page=page)

    # For authenticated users, redirect based on their role
    if current_user.is_authenticated:
        if current_user.has_role('commercial'):
            return redirect(url_for('user.commercial_dashboard'))
        else:
            return redirect(url_for('user.dashboard'))

    # For regular user visitors, include the gallery logic
    image_folder = os.path.join(current_app.static_folder, 'images/gallery')
    gallery_images = [f for f in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, f))]
    random.shuffle(gallery_images)

    page = int(request.args.get('page', 1))
    per_page = 5
    total_images = len(gallery_images)
    start = (page - 1) * per_page
    end = start + per_page

    paginated_images = gallery_images[start:end]
    has_more = end < total_images

    return render_template('index.html', gallery_images=paginated_images, has_more=has_more, page=page)

@main.route('/accept-terms', methods=['GET', 'POST'])
@login_required
def accept_terms():
    form = AcceptTOSForm()
    if form.validate_on_submit() and form.accept_tos.data:
        current_user.tos_accepted = True
        current_user.tos_accepted_on = datetime.utcnow()
        db.session.commit()
        flash('Thank you for accepting the terms of service.', 'success')
        return redirect(url_for('main_routes.index'))
    return render_template('accept_terms.html', form=form)

@main.route('/about')
def about():
    return render_template('aboutus.html')

@main.route('/services')
def services():
    return render_template('services.html')

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        submission = ContactFormSubmission(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            message=form.message.data
        )
        db.session.add(submission)
        db.session.commit()
        return redirect(url_for('main_routes.contact_confirmation'))
    return render_template('contact.html', form=form)

@main.route('/contact-confirmation')
def contact_confirmation():
    return render_template('contact_confirmation.html')   

@main.route('/request_estimate', methods=['POST'])
def request_estimate():
    form = EstimateRequestForm()

    if request.method == 'POST':
        current_app.logger.info(f"Form data received: {request.form}")

        selected_date = request.form.get('preferred_date')
        user_timezone_str = request.form.get('timezone', 'America/Denver')
        user_timezone = pytz.timezone(user_timezone_str)

        if selected_date:
            try:
                response = requests.post(
                    url_for('main_routes.get_available_time_slots', _external=True),
                    json={'date': selected_date, 'timezone': user_timezone_str},
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                response.raise_for_status()
                time_slots_data = response.json()
                time_slots = time_slots_data.get('timeSlots', [])

                form.preferred_time.choices = [(slot, convert_utc_to_local(slot, user_timezone)) for slot in time_slots]
            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"Error fetching time slots: {e}")
                flash('There was an error fetching available time slots.', 'danger')
                return redirect(url_for('main_routes.index'))

        if form.validate_on_submit():
            current_app.logger.info("Form validation successful.")
            
            try:
                preferred_date_time = parser.isoparse(form.preferred_time.data)
                current_app.logger.info(f"Parsed preferred date and time: {preferred_date_time}")

                if preferred_date_time.tzinfo is None:
                    preferred_date_time_localized = user_timezone.localize(preferred_date_time)
                    current_app.logger.info(f"Localized preferred date and time: {preferred_date_time_localized}")
                else:
                    preferred_date_time_localized = preferred_date_time.astimezone(user_timezone)
                    current_app.logger.info(f"Converted preferred date and time to user's timezone: {preferred_date_time_localized}")

                preferred_date_time_utc = preferred_date_time_localized.astimezone(pytz.utc)
                current_app.logger.info(f"Preferred time (UTC): {preferred_date_time_utc}")
            except Exception as e:
                current_app.logger.error(f"Error parsing date and time: {e}")
                flash('There was an error with the selected date or time.', 'danger')
                return redirect(url_for('main_routes.index'))

            try:
                appointment = Appointment(
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    phone=form.phone.data,
                    email=form.email.data,
                    preferred_date_time=preferred_date_time_utc,
                    service_id=form.service.data,
                    estimator_id=form.estimator.data
                )
                db.session.add(appointment)
                db.session.commit()
                current_app.logger.info(f"Appointment created: {appointment}")

                flash('Your estimate request has been submitted.', 'success')
                return redirect(url_for('main_routes.estimate_submitted',
                                        estimator=form.estimator.data,
                                        date=preferred_date_time.strftime('%Y-%m-%d'),
                                        time=preferred_date_time.strftime('%H:%M')))
            except Exception as e:
                current_app.logger.error(f"Error creating appointment: {e}")
                flash('There was an error processing your request.', 'danger')
                return redirect(url_for('main_routes.index'))
        else:
            current_app.logger.info("Form validation failed.")
            for field, errors in form.errors.items():
                for error in errors:
                    current_app.logger.error(f"Error in {field}: {error}")

    return redirect(url_for('main_routes.index'))

def convert_utc_to_local(utc_time_str, user_timezone):
    utc_date_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
    local_date_time = utc_date_time.astimezone(user_timezone)
    return local_date_time.strftime('%Y-%m-%d %H:%M:%S')

def get_upcoming_appointments():
    now = datetime.utcnow()
    return Appointment.query.filter(Appointment.preferred_date_time > now).all()

@main.route('/api/upcoming_appointments')
@csrf.exempt
def api_upcoming_appointments():
    try:
        appointments = get_upcoming_appointments()
        if appointments is None:
            current_app.logger.info("No upcoming appointments found.")
            return jsonify([]), 200

        appointments_data = [{
            'start': appointment.preferred_date_time.replace(tzinfo=pytz.utc).isoformat(),
            'end': (appointment.preferred_date_time + timedelta(hours=1)).replace(tzinfo=pytz.utc).isoformat()
        } for appointment in appointments]
        return jsonify(appointments_data), 200
    except Exception as e:
        current_app.logger.error(f"An error occurred fetching appointments: {e}")
        return jsonify({'error': 'An error occurred fetching appointments'}), 500

@main.route('/get_available_time_slots', methods=['POST'])
@csrf.exempt
def get_available_time_slots():
    data = request.json
    current_app.logger.info(f"Received data: {data}")

    if 'date' not in data or 'timezone' not in data:
        current_app.logger.error('Missing date or timezone in request')
        return jsonify({'error': 'Missing date or timezone'}), 400

    try:
        selected_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        user_timezone_str = data['timezone']
        user_timezone = pytz.timezone(user_timezone_str)
        current_app.logger.info(f"User's timezone: {user_timezone_str}")

    except (ValueError, pytz.UnknownTimeZoneError) as e:
        current_app.logger.error(f"Error parsing date or timezone: {e}")
        return jsonify({'error': 'Invalid date or timezone format'}), 400

    company_timezone = pytz.timezone('America/Denver')
    business_start_time = time(8, 0)
    business_end_time = time(17, 0)

    start_time_local = datetime.combine(selected_date, business_start_time)
    end_time_local = datetime.combine(selected_date, business_end_time)

    start_time_localized = company_timezone.localize(start_time_local)
    end_time_localized = company_timezone.localize(end_time_local)

    start_time_utc = start_time_localized.astimezone(pytz.UTC)
    end_time_utc = end_time_localized.astimezone(pytz.UTC)

    time_slots = []
    current_time_utc = start_time_utc

    while current_time_utc < end_time_utc:
        existing_appointment = Appointment.query.filter_by(preferred_date_time=current_time_utc).first()
        
        if not existing_appointment:
            user_time_slot = current_time_utc.astimezone(user_timezone)
            time_slots.append(user_time_slot.isoformat())
        
        current_time_utc += timedelta(minutes=30)

    current_app.logger.info(f"Generated time slots in ISO format (UTC): {time_slots}")
    
    return jsonify({'timeSlots': time_slots})

@main.route('/estimate_submitted')
def estimate_submitted():
    referrer = request.args.get('referrer', url_for('main_routes.index'))
    estimator_id = request.args.get('estimator')
    date = request.args.get('date')
    time = request.args.get('time')

    # Query the Estimator model to get the name based on the ID
    estimator = None
    if estimator_id:
        try:
            estimator_obj = Estimator.query.get(int(estimator_id))
            if estimator_obj:
                estimator = estimator_obj.name
            else:
                current_app.logger.error(f"Estimator with ID {estimator_id} not found.")
                estimator = "Unknown Estimator"  # Fallback for invalid ID
        except ValueError:
            current_app.logger.error(f"Invalid estimator ID format: {estimator_id}")
            estimator = "Unknown Estimator"  # Fallback for non-integer ID
    else:
        current_app.logger.error("No estimator ID provided in request.")
        estimator = "Unknown Estimator"  # Fallback if no ID is provided

    try:
        time_obj = datetime.strptime(time, '%H:%M')
        formatted_time = time_obj.strftime('%I:%M %p')
    except ValueError as e:
        current_app.logger.error(f"Error parsing time: {e}")
        formatted_time = time  # Fallback to raw time if parsing fails

    return render_template(
        'estimate_submitted.html',
        referrer=referrer,
        estimator=estimator, 
        date=date,
        time=formatted_time,
        hide_estimate_form=True
    )

def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}
            
@main.route('/generate_ics')
def generate_ics():
    estimator = request.args.get('estimator')
    location = request.args.get('location')
    date = request.args.get('date')
    time = request.args.get('time')

    event = icalendar.Event()
    event.add('summary', f'Appointment with {estimator}')
    event.add('dtstart', datetime.strptime(f'{date} {time}', '%Y-%m-%d %I:%M %p'))
    event.add('dtend', datetime.strptime(f'{date} {time}', '%Y-%m-%d %I:%M %p') + timedelta(hours=1))
    event.add('location', location)
    event.add('description', f'Your appointment at {location}')

    cal = icalendar.Calendar()
    cal.add_component(event)

    ics_content = cal.to_ical()

    response = Response(ics_content, mimetype='text/calendar')
    response.headers['Content-Disposition'] = 'attachment; filename=appointment.ics'
    return response
