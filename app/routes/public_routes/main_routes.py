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
from app.forms import AcceptTOSForm, EstimateRequestForm, ContactForm
from app.models import Appointment, Estimator, Service, User, ContactFormSubmission, BusinessConfig, Task, UnsubscribedEmail
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





@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    
    # Handle AJAX/JSON POST from React component
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        # Check honeypot field (from form data)
        hp_value = request.form.get('hp_field', '')
        if hp_value:
            current_app.logger.warning(f"Honeypot caught spam from {request.remote_addr}")
            if is_ajax:
                return jsonify({'success': True}), 200  # Silent success for bots
            return redirect(url_for('main_routes.contact_confirmation'))
        
        # Get form data (works for both traditional form and FormData from React)
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        message = request.form.get('message', '').strip()
        
        # Basic validation
        errors = {}
        if not first_name:
            errors['first_name'] = 'First name is required'
        if not last_name:
            errors['last_name'] = 'Last name is required'
        if not email:
            errors['email'] = 'Email is required'
        if not message:
            errors['message'] = 'Message is required'
        
        if errors:
            if is_ajax:
                return jsonify({'success': False, 'errors': errors}), 400
            # For traditional form, flash errors
            for error in errors.values():
                flash(error, 'danger')
            return render_template('contact.html', form=form)
        
        # Create submission
        submission = ContactFormSubmission(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            message=message
        )
        db.session.add(submission)
        db.session.commit()
        
        # Trigger notification task
        task = Task(name='new_lead_notification', payload={'submission_id': submission.id})
        db.session.add(task)
        db.session.commit()
        
        if is_ajax:
            return jsonify({
                'success': True,
                'redirect': url_for('main_routes.contact_confirmation')
            }), 200
        
        return redirect(url_for('main_routes.contact_confirmation'))
    
    # GET request - pass business config for React component
    configs = BusinessConfig.query.all()
    config_dict = {config.setting_name: config.setting_value for config in configs}
    
    # Check for primary/HQ location first
    from app.models import Location
    primary_location = Location.query.filter_by(is_primary=True, is_active=True).first()
    
    # Use primary location's address if available, otherwise fall back to BusinessConfig
    if primary_location and primary_location.full_address and primary_location.full_address != 'No address':
        business_address = primary_location.full_address
    else:
        business_address = config_dict.get('company_address', 'Denver, Colorado')
    
    business_data = {
        'business_name': config_dict.get('company_name', 'Verso Industries'),
        'business_email': config_dict.get('contact_email', 'contact@versoindustries.com'),
        'business_phone': config_dict.get('contact_phone', '(555) 123-4567'),
        'business_address': business_address,
        'business_hours': config_dict.get('business_hours', 'Mon-Fri: 9AM - 6PM')
    }
    
    return render_template('contact.html', form=form, business_data=business_data)

@main.route('/contact-confirmation')
def contact_confirmation():
    return render_template('contact_confirmation.html')   

@main.route('/about')
def about():
    # If aboutus.html exists, render it, otherwise render a placeholder or the index
    # Assuming aboutus.html exists based on logs
    return render_template('aboutus.html')
   
@main.route('/accessibility')
def accessibility():
    return render_template('accessibility.html')

@main.route('/services')
def services():
    return render_template('services.html')

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

    # Load business configuration
    configs = BusinessConfig.query.all()
    config_dict = {config.setting_name: config.setting_value for config in configs}
    
    # Default values if not set
    business_start_time_str = config_dict.get('business_start_time', '08:00')
    business_end_time_str = config_dict.get('business_end_time', '17:00')
    buffer_time_minutes = int(config_dict.get('buffer_time_minutes', 30))
    company_timezone_str = config_dict.get('company_timezone', 'America/Denver')

    try:
        company_timezone = pytz.timezone(company_timezone_str)
        business_start_time = datetime.strptime(business_start_time_str, '%H:%M').time()
        business_end_time = datetime.strptime(business_end_time_str, '%H:%M').time()
    except (ValueError, pytz.UnknownTimeZoneError) as e:
        current_app.logger.error(f"Error parsing business config: {e}")
        return jsonify({'error': 'Invalid business configuration'}), 500

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
        
        current_time_utc += timedelta(minutes=buffer_time_minutes)

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

@main.route('/api/business_config', methods=['GET'])
@csrf.exempt
def get_business_config():
    try:
        configs = BusinessConfig.query.all()
        config_dict = {config.setting_name: config.setting_value for config in configs}
        # Ensure all required settings are included, with defaults
        response = {
            'company_timezone': config_dict.get('company_timezone', 'America/Denver'),
            'business_start_time': config_dict.get('business_start_time', '08:00'),
            'business_end_time': config_dict.get('business_end_time', '17:00'),
            'buffer_time_minutes': int(config_dict.get('buffer_time_minutes', 30))
        }
        current_app.logger.debug(f"Business config retrieved: {response}")
        return jsonify(response), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching business config: {e}")
        return jsonify({'error': 'Failed to fetch business configuration'}), 500

@main.route('/unsubscribe')
def unsubscribe():
    email = request.args.get('email')
    if not email:
        return "Invalid unsubscribe request.", 400
    
    # Check if already unsubscribed
    existing = UnsubscribedEmail.query.filter_by(email=email).first()
    if not existing:
        unsub = UnsubscribedEmail(email=email)
        db.session.add(unsub)
        db.session.commit()
        
    return render_template('unsubscribe_success.html', email=email)


# ============================================================================
# Phase 12: SEO Routes
# ============================================================================

@main.route('/sitemap.xml')
def sitemap_xml():
    """Generate and serve dynamic XML sitemap."""
    from app.modules.seo import generate_dynamic_sitemap
    
    sitemap_content = generate_dynamic_sitemap()
    return Response(sitemap_content, mimetype='application/xml')


@main.route('/robots.txt')
def robots_txt():
    """Serve robots.txt with sitemap reference."""
    from app.modules.seo import get_robots_txt_content
    
    sitemap_url = url_for('main_routes.sitemap_xml', _external=True)
    robots_content = get_robots_txt_content(sitemap_url=sitemap_url)
    return Response(robots_content, mimetype='text/plain')

@main.route('/set_language/<language>')
def set_language(language=None):
    current_app.logger.info(f"Setting language to: {language}")
    if language not in current_app.config['LANGUAGES']:
        current_app.logger.warning(f"Invalid language requested: {language}")
        return redirect(request.referrer or url_for('main_routes.index'))
    
    session['lang'] = language
    flash(f"Language changed to {current_app.config['LANGUAGES'][language]}")
    return redirect(request.referrer or url_for('main_routes.index'))


# ============================================================================
# Shortcut Routes (Fix 404s)
# ============================================================================

@main.route('/downloads')
@login_required
def downloads_redirect():
    """Redirect /downloads to /shop/my-downloads for convenience."""
    return redirect(url_for('cart.my_downloads'))


@main.route('/subscriptions')
@login_required
def subscriptions_redirect():
    """Redirect /subscriptions to /account/subscriptions for convenience."""
    return redirect(url_for('subscriptions.my_subscriptions'))