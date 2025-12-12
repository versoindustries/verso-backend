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
    """Redirect to unified settings dashboard."""
    return redirect(url_for('user.unified_settings', tab='profile'))


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
    """Redirect to unified settings dashboard with appropriate tab."""
    tab = request.args.get('tab', 'orders')
    # Map old tab names to new tab names
    tab_mapping = {
        'overview': 'orders',
        'orders': 'orders',
        'appointments': 'appointments',
        'subscriptions': 'subscriptions',
        'downloads': 'downloads'
    }
    new_tab = tab_mapping.get(tab, 'orders')
    return redirect(url_for('user.unified_settings', tab=new_tab))


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
    """Redirect to unified settings dashboard preferences tab."""
    return redirect(url_for('user.unified_settings', tab='preferences'))


@user.route('/dashboard/saved-items')
@login_required
def saved_items():
    """Redirect to unified settings dashboard saved items tab."""
    return redirect(url_for('user.unified_settings', tab='saved'))


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


# ============================================================================
# Unified User Settings Dashboard API
# ============================================================================

@user.route('/api/user/settings-data')
@login_required
def get_settings_data():
    """Get all user settings data for the unified React dashboard."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[get_settings_data] Called by user {current_user.id} ({current_user.email})")
    print(f"[get_settings_data] Called by user {current_user.id} ({current_user.email})")
    try:
        from app.models import (
            UserPreference, NotificationPreference, SavedItem, 
            Product, Post, Order, Appointment, Subscription, DownloadToken
        )
        
        now = datetime.utcnow()
        
        # Get or create user preferences
        user_prefs = UserPreference.query.filter_by(user_id=current_user.id).first()
        if not user_prefs:
            user_prefs = UserPreference(user_id=current_user.id)
            db.session.add(user_prefs)
            db.session.commit()
        
        # Get notification preferences
        notif_prefs = NotificationPreference.query.filter_by(user_id=current_user.id).first()
        if not notif_prefs:
            notif_prefs = NotificationPreference(user_id=current_user.id)
            db.session.add(notif_prefs)
            db.session.commit()
        
        # Get saved items with hydration
        saved_items_query = SavedItem.query.filter_by(user_id=current_user.id)\
            .order_by(SavedItem.created_at.desc()).all()
        
        saved_items = []
        for item in saved_items_query:
            item_data = {
                'id': item.id,
                'item_type': item.item_type,
                'item_id': item.item_id,
                'notes': item.notes,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'item': None
            }
            if item.item_type == 'product':
                product = Product.query.get(item.item_id)
                if product:
                    item_data['item'] = {
                        'id': product.id,
                        'name': product.name,
                        'price': product.price,
                        'image': product.image
                    }
            elif item.item_type == 'post':
                post = Post.query.get(item.item_id)
                if post:
                    item_data['item'] = {
                        'id': post.id,
                        'title': post.title,
                        'excerpt': post.content[:100] if post.content else ''
                    }
            if item_data['item']:
                saved_items.append(item_data)
        
        # Get orders
        orders = Order.query.filter_by(user_id=current_user.id)\
            .order_by(Order.created_at.desc()).limit(50).all()
        orders_data = [{
            'id': o.id,
            'total_amount': o.total_amount or 0,
            'status': o.status or 'pending',
            'created_at': o.created_at.isoformat() if o.created_at else None,
            'items_count': len(o.items) if o.items else 0
        } for o in orders]
        
        # Get appointments
        appointments = Appointment.query.filter(
            Appointment.email == current_user.email
        ).order_by(Appointment.preferred_date_time.desc()).limit(50).all()
        appointments_data = [{
            'id': a.id,
            'service_name': a.service.name if a.service else 'Appointment',
            'preferred_date_time': a.preferred_date_time.isoformat() if a.preferred_date_time else None,
            'status': 'upcoming' if a.preferred_date_time and a.preferred_date_time > now else 'past',
            'notes': a.notes
        } for a in appointments]
        
        # Get subscriptions
        subscriptions = Subscription.query.filter_by(user_id=current_user.id)\
            .order_by(Subscription.created_at.desc()).all()
        subscriptions_data = [{
            'id': s.id,
            'plan_name': s.plan.name if hasattr(s, 'plan') and s.plan else 'Subscription',
            'status': s.status,
            'current_period_end': s.current_period_end.isoformat() if s.current_period_end else None,
            'cancel_at_period_end': s.cancel_at_period_end if hasattr(s, 'cancel_at_period_end') else False
        } for s in subscriptions]
        
        # Get download tokens
        downloads = DownloadToken.query.filter_by(user_id=current_user.id)\
            .order_by(DownloadToken.created_at.desc()).all()
        downloads_data = [{
            'id': t.id,
            'product_name': t.order_item.product.name if t.order_item and t.order_item.product else 'Digital Product',
            'download_count': t.download_count or 0,
            'max_downloads': t.max_downloads or 5,
            'is_valid': t.is_valid() if hasattr(t, 'is_valid') else True,
            'download_url': f'/download/{t.token}' if t.token else '#'
        } for t in downloads]
        
        # Stats
        stats = {
            'total_orders': Order.query.filter_by(user_id=current_user.id).count(),
            'pending_orders': Order.query.filter_by(user_id=current_user.id, status='pending').count(),
            'total_downloads': len(downloads),
            'upcoming_appointments': len([a for a in appointments_data if a['status'] == 'upcoming']),
            'active_subscriptions': len([s for s in subscriptions_data if s['status'] in ['active', 'trialing']]),
            'saved_items': len(saved_items)
        }
        
        # Notification types for preferences UI
        notification_types = [
            {'value': 'message', 'label': 'New Messages'},
            {'value': 'mention', 'label': '@Mentions'},
            {'value': 'leave_approved', 'label': 'Leave Approved'},
            {'value': 'leave_rejected', 'label': 'Leave Rejected'},
            {'value': 'appointment_reminder', 'label': 'Appointment Reminders'},
            {'value': 'order_placed', 'label': 'Order Placed'},
            {'value': 'order_shipped', 'label': 'Order Shipped'},
            {'value': 'comment', 'label': 'New Comments'},
        ]
        
        return jsonify({
            'success': True,
            'profile': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'first_name': current_user.first_name or '',
                'last_name': current_user.last_name or '',
                'bio': current_user.bio or '',
                'location': current_user.location or '',
                'phone': current_user.phone if hasattr(current_user, 'phone') else ''
            },
            'preferences': {
                'email_marketing': user_prefs.email_marketing if hasattr(user_prefs, 'email_marketing') else True,
                'email_order_updates': user_prefs.email_order_updates if hasattr(user_prefs, 'email_order_updates') else True,
                'email_appointment_reminders': user_prefs.email_appointment_reminders if hasattr(user_prefs, 'email_appointment_reminders') else True,
                'email_digest_weekly': user_prefs.email_digest_weekly if hasattr(user_prefs, 'email_digest_weekly') else False,
                'email_newsletter': user_prefs.email_newsletter if hasattr(user_prefs, 'email_newsletter') else True,
                'push_enabled': user_prefs.push_enabled if hasattr(user_prefs, 'push_enabled') else False,
                'sms_enabled': user_prefs.sms_enabled if hasattr(user_prefs, 'sms_enabled') else False,
                'show_activity_status': user_prefs.show_activity_status if hasattr(user_prefs, 'show_activity_status') else True,
                'show_profile_publicly': user_prefs.show_profile_publicly if hasattr(user_prefs, 'show_profile_publicly') else False,
                'theme': user_prefs.theme if hasattr(user_prefs, 'theme') else 'dark',
                'language': user_prefs.language if hasattr(user_prefs, 'language') else 'en'
            },
            'notification_preferences': {
                'email_digest_enabled': notif_prefs.email_digest_enabled if hasattr(notif_prefs, 'email_digest_enabled') else True,
                'email_digest_frequency': notif_prefs.email_digest_frequency if hasattr(notif_prefs, 'email_digest_frequency') else 'daily',
                'muted_types': notif_prefs.muted_types or []
            },
            'notification_types': notification_types,
            'saved_items': saved_items,
            'orders': orders_data,
            'appointments': appointments_data,
            'subscriptions': subscriptions_data,
            'downloads': downloads_data,
            'stats': stats
        })
    except Exception as e:
        import traceback
        print(f"Error in get_settings_data: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to load settings: {str(e)}'
        }), 500


@user.route('/api/user/profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile fields."""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    # Update allowed fields
    if 'email' in data:
        # Check if email is already taken
        existing = User.query.filter(User.email == data['email'], User.id != current_user.id).first()
        if existing:
            return jsonify({'success': False, 'message': 'Email already in use'}), 400
        current_user.email = data['email']
    
    if 'username' in data:
        existing = User.query.filter(User.username == data['username'], User.id != current_user.id).first()
        if existing:
            return jsonify({'success': False, 'message': 'Username already taken'}), 400
        current_user.username = data['username']
    
    if 'bio' in data:
        current_user.bio = data['bio']
    
    if 'location' in data:
        current_user.location = data['location']
    
    if 'first_name' in data:
        current_user.first_name = data['first_name']
    
    if 'last_name' in data:
        current_user.last_name = data['last_name']
    
    current_user.log_activity(
        activity_type='profile_updated',
        title='Updated profile',
        description='Profile information modified',
        icon='fa-user-edit'
    )
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Profile updated successfully'})


@user.route('/api/user/password', methods=['POST'])
@login_required
def update_password():
    """Change user password."""
    data = request.get_json()
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        return jsonify({'success': False, 'message': 'All password fields are required'}), 400
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
    
    if len(new_password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
    
    # Verify current password
    if not bcrypt.check_password_hash(current_user.password, current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
    
    # Update password
    current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    
    current_user.log_activity(
        activity_type='password_changed',
        title='Password changed',
        description='Account password was updated',
        icon='fa-lock'
    )
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Password updated successfully'})


@user.route('/api/user/preferences', methods=['POST'])
@login_required
def update_preferences_api():
    """Update user preferences via JSON API."""
    from app.models import UserPreference
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    user_prefs = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not user_prefs:
        user_prefs = UserPreference(user_id=current_user.id)
        db.session.add(user_prefs)
    
    # Update preferences
    pref_fields = [
        'email_marketing', 'email_order_updates', 'email_appointment_reminders',
        'email_digest_weekly', 'email_newsletter', 'push_enabled', 'sms_enabled',
        'show_activity_status', 'show_profile_publicly', 'theme', 'language'
    ]
    
    for field in pref_fields:
        if field in data:
            setattr(user_prefs, field, data[field])
    
    current_user.log_activity(
        activity_type='preferences_updated',
        title='Updated preferences',
        description='Account preferences modified',
        icon='fa-cog'
    )
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Preferences saved successfully'})


@user.route('/api/user/notification-preferences', methods=['POST'])
@login_required
def update_notification_preferences_api():
    """Update notification preferences via JSON API."""
    from app.models import NotificationPreference
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    prefs = NotificationPreference.query.filter_by(user_id=current_user.id).first()
    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id)
        db.session.add(prefs)
    
    if 'email_digest_enabled' in data:
        prefs.email_digest_enabled = data['email_digest_enabled']
    
    if 'email_digest_frequency' in data:
        prefs.email_digest_frequency = data['email_digest_frequency']
    
    if 'muted_types' in data:
        prefs.muted_types = data['muted_types']
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Notification preferences saved'})


@user.route('/api/user/saved-items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_saved_item(item_id):
    """Delete a saved item by ID."""
    from app.models import SavedItem
    
    saved = SavedItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not saved:
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    
    db.session.delete(saved)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Item removed'})


# ============================================================================
# Unified Settings Page Route
# ============================================================================

@user.route('/account')
@user.route('/account/<tab>')
@login_required
def unified_settings(tab='profile'):
    """Unified user settings dashboard - React island mount point."""
    import json
    from flask import get_flashed_messages
    
    # Get any flash messages for the React component
    messages = get_flashed_messages(with_categories=True)
    
    valid_tabs = ['profile', 'preferences', 'notifications', 'saved', 'orders', 'appointments', 'subscriptions', 'downloads']
    if tab not in valid_tabs:
        tab = 'profile'
    
    props = {
        'initialTab': tab,
        'csrfToken': session.get('csrf_token', ''),
        'apiBaseUrl': '/api/user',
        'flashMessages': [{'category': cat, 'message': msg} for cat, msg in messages]
    }
    
    return render_template(
        'UserDashboard/unified_settings.html',
        props_json=json.dumps(props)
    )

