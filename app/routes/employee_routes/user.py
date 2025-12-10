from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import app
import os
from app import db, mail, bcrypt
from app.models import User, Order, Appointment, Subscription, DownloadToken, Notification
from app.forms import RegistrationForm, LoginForm, SettingsForm, EstimateRequestForm
from flask_mail import Message
from datetime import datetime, timedelta, date
import logging
from sqlalchemy import and_, cast, String
import pytz

user = Blueprint('user', __name__)

@user.context_processor
def combined_context_processor():
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form)

@user.route('/reset_password', methods=['POST'])
def reset_password():
    token = request.form.get('token')
    password = request.form.get('password')
    user = User.verify_reset_token(token)
    if user:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('main.register'))

@user.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    settings_form = SettingsForm()

    if settings_form.validate_on_submit():
        current_user.email = settings_form.email.data
        current_user.bio = settings_form.bio.data
        current_user.location = settings_form.location.data

        if settings_form.password.data:
            current_user.set_password(settings_form.password.data)

        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user.settings'))

    elif request.method == 'GET':
        settings_form.email.data = current_user.email
        settings_form.bio.data = current_user.bio
        settings_form.location.data = current_user.location

    return render_template('settings.html', settings_form=settings_form)


# ============================================================================
# Phase 11: Customer Portal & Self-Service Dashboard
# ============================================================================

@user.route('/dashboard')
@login_required
def dashboard():
    """Enhanced user dashboard with comprehensive account overview."""
    from app.models import BusinessConfig
    
    now = datetime.utcnow()
    
    # Get ecommerce_enabled from BusinessConfig
    ecommerce_config = BusinessConfig.query.filter_by(setting_name='ecommerce_enabled').first()
    ecommerce_enabled = ecommerce_config.setting_value.lower() == 'true' if ecommerce_config else True
    
    # Get recent orders (last 5) - only if ecommerce enabled
    recent_orders = []
    if ecommerce_enabled:
        recent_orders = Order.query.filter_by(user_id=current_user.id)\
            .order_by(Order.created_at.desc()).limit(5).all()
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.email == current_user.email,
        Appointment.preferred_date_time >= now
    ).order_by(Appointment.preferred_date_time.asc()).limit(5).all()
    
    # Get active subscriptions
    active_subscriptions = Subscription.query.filter(
        Subscription.user_id == current_user.id,
        Subscription.status.in_(['active', 'trialing'])
    ).all() if ecommerce_enabled else []
    
    # Get digital downloads
    download_tokens = DownloadToken.query.filter_by(user_id=current_user.id)\
        .order_by(DownloadToken.created_at.desc()).limit(5).all()
    
    # Get unread notifications
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    # Summary stats
    stats = {
        'total_orders': Order.query.filter_by(user_id=current_user.id).count() if ecommerce_enabled else 0,
        'total_downloads': DownloadToken.query.filter_by(user_id=current_user.id).count(),
        'upcoming_appointments': Appointment.query.filter(
            Appointment.email == current_user.email,
            Appointment.preferred_date_time >= now
        ).count(),
        'active_subscriptions': len(active_subscriptions)
    }
    
    # Serialize data for React component
    orders_json = [{
        'id': o.id,
        'total_amount': o.total_amount or 0,
        'status': o.status or 'pending',
        'created_at': o.created_at.isoformat() if o.created_at else None
    } for o in recent_orders]
    
    appointments_json = [{
        'id': a.id,
        'service_name': a.service.name if a.service else 'Appointment',
        'preferred_date_time': a.preferred_date_time.isoformat() if a.preferred_date_time else None,
        'status': 'scheduled'
    } for a in upcoming_appointments]
    
    downloads_json = [{
        'id': t.id,
        'product_name': t.order_item.product.name if t.order_item and t.order_item.product else 'Digital Product',
        'download_count': t.download_count or 0,
        'max_downloads': t.max_downloads or 5,
        'is_valid': t.is_valid() if hasattr(t, 'is_valid') else True,
        'download_url': f'/download/{t.token}' if t.token else '#'
    } for t in download_tokens]
    
    notifications_json = [{
        'id': n.id,
        'title': n.title or 'Notification',
        'created_at': n.created_at.isoformat() if n.created_at else None,
        'is_read': n.is_read
    } for n in unread_notifications]
    
    return render_template(
        'UserDashboard/user_dashboard.html',
        recent_orders=orders_json,
        upcoming_appointments=appointments_json,
        active_subscriptions=active_subscriptions,
        download_tokens=downloads_json,
        unread_notifications=notifications_json,
        stats=stats,
        ecommerce_enabled=ecommerce_enabled
    )


@user.route('/my-account')
@login_required
def my_account():
    """Main customer portal with tabbed interface."""
    tab = request.args.get('tab', 'overview')
    now = datetime.utcnow()
    
    # Overview tab data
    recent_orders = Order.query.filter_by(user_id=current_user.id)\
        .order_by(Order.created_at.desc()).limit(5).all()
    
    upcoming_appointments = Appointment.query.filter(
        Appointment.email == current_user.email,
        Appointment.preferred_date_time >= now
    ).order_by(Appointment.preferred_date_time.asc()).limit(5).all()
    
    # Full data for tabs
    all_orders = Order.query.filter_by(user_id=current_user.id)\
        .order_by(Order.created_at.desc()).all() if tab == 'orders' else []
    
    all_appointments = Appointment.query.filter(
        Appointment.email == current_user.email
    ).order_by(Appointment.preferred_date_time.desc()).all() if tab == 'appointments' else []
    
    subscriptions = Subscription.query.filter_by(user_id=current_user.id)\
        .order_by(Subscription.created_at.desc()).all() if tab == 'subscriptions' else []
    
    download_tokens = DownloadToken.query.filter_by(user_id=current_user.id)\
        .order_by(DownloadToken.created_at.desc()).all() if tab == 'downloads' else []
    
    # Stats for overview
    stats = {
        'total_orders': Order.query.filter_by(user_id=current_user.id).count(),
        'pending_orders': Order.query.filter_by(user_id=current_user.id, status='pending').count(),
        'total_downloads': DownloadToken.query.filter_by(user_id=current_user.id).count(),
        'upcoming_appointments': Appointment.query.filter(
            Appointment.email == current_user.email,
            Appointment.preferred_date_time >= now
        ).count(),
        'active_subscriptions': Subscription.query.filter(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(['active', 'trialing'])
        ).count()
    }
    
    return render_template(
        'UserDashboard/customer_portal.html',
        tab=tab,
        recent_orders=recent_orders,
        upcoming_appointments=upcoming_appointments,
        all_orders=all_orders,
        all_appointments=all_appointments,
        subscriptions=subscriptions,
        download_tokens=download_tokens,
        stats=stats,
        now=now
    )


@user.route('/my-account/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """View detailed order information."""
    order = Order.query.get_or_404(order_id)
    
    # Security check: ensure user owns this order
    if order.user_id != current_user.id:
        flash('Order not found.', 'danger')
        return redirect(url_for('user.my_account', tab='orders'))
    
    # Get download tokens for digital items in this order
    download_tokens = []
    for item in order.items:
        if item.product and item.product.is_digital:
            tokens = DownloadToken.query.filter_by(order_item_id=item.id).all()
            download_tokens.extend(tokens)
    
    return render_template(
        'UserDashboard/order_detail.html',
        order=order,
        download_tokens=download_tokens
    )


@user.route('/dashboard/commercial')
@login_required
def commercial_dashboard():
    """Commercial user dashboard with business-specific data."""
    if not current_user.has_role('commercial'):
        flash('Access denied. This area is for commercial users only.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    now = datetime.utcnow()
    
    # Get commercial-specific data
    orders = Order.query.filter_by(user_id=current_user.id)\
        .order_by(Order.created_at.desc()).limit(10).all()
    
    # Calculate spending stats
    total_spent = db.session.query(db.func.sum(Order.total_amount))\
        .filter(Order.user_id == current_user.id, Order.status == 'paid').scalar() or 0
    
    return render_template(
        'UserDashboard/commercial_dashboard.html',
        orders=orders,
        total_spent=total_spent
    )


# ============================================================================
# Phase 22: User Experience Hardening Routes
# ============================================================================

@user.route('/dashboard/activity')
@login_required
def activity_feed():
    """User activity feed timeline with pagination."""
    from app.models import UserActivity
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    activities = UserActivity.query.filter_by(user_id=current_user.id)\
        .order_by(UserActivity.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'activities': [a.to_dict() for a in activities.items],
            'has_next': activities.has_next,
            'next_page': activities.next_num if activities.has_next else None
        })
    
    return render_template(
        'UserDashboard/activity_feed.html',
        activities=activities
    )


@user.route('/dashboard/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """User preference center for notifications, privacy, and display settings."""
    from app.models import UserPreference
    from app.forms import UserPreferenceForm
    
    form = UserPreferenceForm()
    
    # Get or create user preferences
    user_prefs = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not user_prefs:
        user_prefs = UserPreference(user_id=current_user.id)
        db.session.add(user_prefs)
        db.session.commit()
    
    if form.validate_on_submit():
        # Update all preference fields
        user_prefs.email_marketing = form.email_marketing.data
        user_prefs.email_order_updates = form.email_order_updates.data
        user_prefs.email_appointment_reminders = form.email_appointment_reminders.data
        user_prefs.email_digest_weekly = form.email_digest_weekly.data
        user_prefs.email_newsletter = form.email_newsletter.data
        user_prefs.push_enabled = form.push_enabled.data
        user_prefs.sms_enabled = form.sms_enabled.data
        user_prefs.show_activity_status = form.show_activity_status.data
        user_prefs.show_profile_publicly = form.show_profile_publicly.data
        user_prefs.theme = form.theme.data
        user_prefs.language = form.language.data
        
        # Log activity
        current_user.log_activity(
            activity_type='preferences_updated',
            title='Updated preferences',
            description='Account preferences modified',
            icon='fa-cog'
        )
        
        db.session.commit()
        flash('Preferences saved successfully!', 'success')
        return redirect(url_for('user.preferences'))
    
    # Pre-populate form on GET
    if request.method == 'GET':
        form.email_marketing.data = user_prefs.email_marketing
        form.email_order_updates.data = user_prefs.email_order_updates
        form.email_appointment_reminders.data = user_prefs.email_appointment_reminders
        form.email_digest_weekly.data = user_prefs.email_digest_weekly
        form.email_newsletter.data = user_prefs.email_newsletter
        form.push_enabled.data = user_prefs.push_enabled
        form.sms_enabled.data = user_prefs.sms_enabled
        form.show_activity_status.data = user_prefs.show_activity_status
        form.show_profile_publicly.data = user_prefs.show_profile_publicly
        form.theme.data = user_prefs.theme
        form.language.data = user_prefs.language
    
    return render_template(
        'UserDashboard/preferences.html',
        form=form,
        user_prefs=user_prefs
    )


@user.route('/dashboard/saved-items')
@login_required
def saved_items():
    """User's saved items / wishlist management."""
    from app.models import SavedItem, Product, Post
    
    item_type = request.args.get('type', 'all')
    
    query = SavedItem.query.filter_by(user_id=current_user.id)
    if item_type != 'all':
        query = query.filter_by(item_type=item_type)
    
    saved = query.order_by(SavedItem.created_at.desc()).all()
    
    # Hydrate items with actual product/post data
    items_with_data = []
    for item in saved:
        data = {'saved_item': item, 'item': None}
        if item.item_type == 'product':
            data['item'] = Product.query.get(item.item_id)
        elif item.item_type == 'post':
            data['item'] = Post.query.get(item.item_id)
        if data['item']:  # Only include if item still exists
            items_with_data.append(data)
    
    return render_template(
        'UserDashboard/saved_items.html',
        items=items_with_data,
        item_type=item_type
    )


@user.route('/dashboard/saved-items/add', methods=['POST'])
@login_required
def add_saved_item():
    """Add item to saved items / wishlist."""
    from app.models import SavedItem
    
    item_type = request.json.get('item_type')
    item_id = request.json.get('item_id')
    notes = request.json.get('notes', '')
    
    if not item_type or not item_id:
        return jsonify({'success': False, 'message': 'Missing item type or ID'}), 400
    
    # Check if already saved
    existing = SavedItem.query.filter_by(
        user_id=current_user.id,
        item_type=item_type,
        item_id=item_id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'Item already saved'})
    
    saved = SavedItem(
        user_id=current_user.id,
        item_type=item_type,
        item_id=item_id,
        notes=notes
    )
    db.session.add(saved)
    
    current_user.log_activity(
        activity_type='item_saved',
        title=f'Saved a {item_type}',
        related_type=item_type,
        related_id=item_id,
        icon='fa-heart'
    )
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Item saved!'})


@user.route('/dashboard/saved-items/remove', methods=['POST'])
@login_required
def remove_saved_item():
    """Remove item from saved items / wishlist."""
    from app.models import SavedItem
    
    saved_id = request.json.get('id')
    if not saved_id:
        return jsonify({'success': False, 'message': 'Missing saved item ID'}), 400
    
    saved = SavedItem.query.filter_by(id=saved_id, user_id=current_user.id).first()
    if not saved:
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    
    db.session.delete(saved)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Item removed from saved items'})


@user.route('/dashboard/export-data', methods=['POST'])
@login_required
def export_data():
    """Queue GDPR data export request."""
    from app.models import UserPreference
    from app.worker import queue_task
    
    user_prefs = UserPreference.query.filter_by(user_id=current_user.id).first()
    
    if user_prefs and user_prefs.data_export_requested_at:
        # Rate limit: one export per 24 hours
        time_diff = datetime.utcnow() - user_prefs.data_export_requested_at
        if time_diff.total_seconds() < 86400:
            remaining_hours = int((86400 - time_diff.total_seconds()) / 3600)
            flash(f'Please wait {remaining_hours} hours before requesting another export.', 'warning')
            return redirect(url_for('user.preferences'))
    
    if not user_prefs:
        user_prefs = UserPreference(user_id=current_user.id)
        db.session.add(user_prefs)
    
    user_prefs.data_export_requested_at = datetime.utcnow()
    
    # Log activity
    current_user.log_activity(
        activity_type='data_export_requested',
        title='Requested data export',
        description='GDPR data export queued',
        icon='fa-download'
    )
    
    db.session.commit()
    
    # Queue the export task
    try:
        queue_task('handle_gdpr_data_export', {'user_id': current_user.id})
    except Exception as e:
        current_app.logger.error(f"Failed to queue data export: {e}")
    
    flash('Your data export has been queued. You will receive an email when it is ready.', 'success')
    return redirect(url_for('user.preferences'))

