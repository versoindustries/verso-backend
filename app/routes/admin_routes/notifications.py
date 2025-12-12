"""
Phase 6: Notifications routes.

Provides API endpoints for the unified notification system.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Notification, NotificationPreference, User, Task
from app.database import db
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def index():
    """List all notifications for current user."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('notifications/index.html', notifications=notifications)


@notifications_bp.route('/poll')
@login_required
def poll():
    """AJAX endpoint for polling notifications (notification bell)."""
    # Get unread notifications (most recent 10)
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({
        'unread_count': unread_count,
        'notifications': [n.to_dict() for n in notifications]
    })


@notifications_bp.route('/all')
@login_required
def all_notifications():
    """AJAX endpoint for all notifications (paginated)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications.items],
        'page': notifications.page,
        'pages': notifications.pages,
        'total': notifications.total,
        'has_next': notifications.has_next,
        'has_prev': notifications.has_prev
    })


@notifications_bp.route('/<int:notification_id>/read', methods=['POST', 'GET'])
@login_required
def mark_read(notification_id):
    """Mark a single notification as read."""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    if not notification.is_read:
        notification.is_read = True
        db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    # If there's a link, redirect to it
    if notification.link:
        return redirect(notification.link)
    
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete a notification."""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'success': True})


@notifications_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Redirect to unified settings dashboard notifications tab."""
    return redirect(url_for('user.unified_settings', tab='notifications'))


# ============================================================================
# Helper Functions for Creating Notifications
# ============================================================================

def create_notification(user_id, notification_type, title, body=None, link=None, 
                        related_type=None, related_id=None):
    """
    Helper function to create a notification.
    
    Args:
        user_id: ID of the user to notify
        notification_type: Type of notification (message, leave_approved, etc.)
        title: Notification title
        body: Optional body text
        link: Optional link to navigate to
        related_type: Optional related entity type
        related_id: Optional related entity ID
    
    Returns:
        The created Notification object
    """
    # Check user preferences
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if prefs and notification_type in (prefs.muted_types or []):
        return None  # User has muted this type
    
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        link=link,
        related_type=related_type,
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()
    
    return notification


def notify_users(user_ids, notification_type, title, body=None, link=None,
                 related_type=None, related_id=None):
    """
    Create notifications for multiple users.
    
    Args:
        user_ids: List of user IDs to notify
        (other args same as create_notification)
    
    Returns:
        List of created Notification objects
    """
    notifications = []
    for user_id in user_ids:
        n = create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            link=link,
            related_type=related_type,
            related_id=related_id
        )
        if n:
            notifications.append(n)
    return notifications
