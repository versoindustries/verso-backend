"""
Phase 15: Push Notification Routes

Web Push notification management using VAPID:
- Subscribe/unsubscribe endpoints
- Push configuration
- Category preferences
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
import json
import os

from app.database import db
from app.models import PushSubscription

push_bp = Blueprint('push', __name__, url_prefix='/api/push')


def get_vapid_public_key():
    """Get VAPID public key from config or environment."""
    return current_app.config.get('VAPID_PUBLIC_KEY') or os.environ.get('VAPID_PUBLIC_KEY', '')


def get_vapid_private_key():
    """Get VAPID private key from config or environment."""
    return current_app.config.get('VAPID_PRIVATE_KEY') or os.environ.get('VAPID_PRIVATE_KEY', '')


def get_vapid_claims():
    """Get VAPID claims for web push."""
    return {
        'sub': current_app.config.get('VAPID_CLAIMS_EMAIL') or os.environ.get('VAPID_CLAIMS_EMAIL', 'mailto:admin@example.com')
    }


@push_bp.route('/vapid-public-key')
@login_required
def vapid_public_key():
    """Return VAPID public key for client-side subscription."""
    key = get_vapid_public_key()
    
    if not key:
        return jsonify({
            'error': 'Push notifications not configured',
            'configured': False
        }), 503
    
    return jsonify({
        'publicKey': key,
        'configured': True
    })


@push_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Create a new push subscription."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    endpoint = data.get('endpoint')
    keys = data.get('keys', {})
    p256dh_key = keys.get('p256dh')
    auth_key = keys.get('auth')
    
    if not endpoint or not p256dh_key or not auth_key:
        return jsonify({'error': 'Missing subscription data'}), 400
    
    # Check if this subscription already exists
    existing = PushSubscription.query.filter_by(
        user_id=current_user.id,
        endpoint=endpoint
    ).first()
    
    if existing:
        # Update existing subscription
        existing.p256dh_key = p256dh_key
        existing.auth_key = auth_key
        existing.is_active = True
        existing.subscribed_at = datetime.utcnow()
        existing.user_agent = request.user_agent.string[:500] if request.user_agent else None
        db.session.commit()
        
        return jsonify({
            'success': True,
            'subscription_id': existing.id,
            'message': 'Subscription updated'
        })
    
    # Create new subscription
    subscription = PushSubscription(
        user_id=current_user.id,
        endpoint=endpoint,
        p256dh_key=p256dh_key,
        auth_key=auth_key,
        user_agent=request.user_agent.string[:500] if request.user_agent else None,
        categories=['orders', 'messages', 'appointments'],  # Default categories
        is_active=True
    )
    
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'subscription_id': subscription.id,
        'message': 'Subscribed to push notifications'
    }), 201


@push_bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """Deactivate a push subscription."""
    data = request.get_json()
    
    endpoint = data.get('endpoint') if data else None
    
    if endpoint:
        # Unsubscribe specific endpoint
        subscription = PushSubscription.query.filter_by(
            user_id=current_user.id,
            endpoint=endpoint
        ).first()
        
        if subscription:
            subscription.is_active = False
            db.session.commit()
    else:
        # Unsubscribe all endpoints for user
        PushSubscription.query.filter_by(
            user_id=current_user.id
        ).update({'is_active': False})
        db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Unsubscribed from push notifications'
    })


@push_bp.route('/preferences', methods=['GET', 'PUT'])
@login_required
def preferences():
    """Get or update push notification category preferences."""
    if request.method == 'GET':
        # Get all active subscriptions for user
        subscriptions = PushSubscription.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()
        
        # Merge categories from all subscriptions
        all_categories = set()
        for sub in subscriptions:
            if sub.categories:
                all_categories.update(sub.categories)
        
        available_categories = [
            {'id': 'orders', 'label': 'Order Updates', 'description': 'Shipping, delivery, and order status'},
            {'id': 'messages', 'label': 'Messages', 'description': 'New messages and mentions'},
            {'id': 'appointments', 'label': 'Appointments', 'description': 'Appointment reminders'},
            {'id': 'marketing', 'label': 'Marketing', 'description': 'Promotions and announcements'},
        ]
        
        return jsonify({
            'enabled_categories': list(all_categories),
            'available_categories': available_categories,
            'subscription_count': len(subscriptions)
        })
    
    # PUT - update preferences
    data = request.get_json()
    categories = data.get('categories', [])
    
    # Validate categories
    valid_categories = {'orders', 'messages', 'appointments', 'marketing'}
    categories = [c for c in categories if c in valid_categories]
    
    # Update all active subscriptions
    subscriptions = PushSubscription.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    
    for sub in subscriptions:
        sub.categories = categories
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'categories': categories
    })


@push_bp.route('/subscriptions')
@login_required
def list_subscriptions():
    """List user's push subscriptions."""
    subscriptions = PushSubscription.query.filter_by(
        user_id=current_user.id
    ).order_by(PushSubscription.subscribed_at.desc()).all()
    
    return jsonify({
        'subscriptions': [{
            'id': sub.id,
            'device_name': sub.device_name or 'Unknown Device',
            'user_agent': sub.user_agent,
            'is_active': sub.is_active,
            'categories': sub.categories or [],
            'subscribed_at': sub.subscribed_at.isoformat() if sub.subscribed_at else None,
            'last_used_at': sub.last_used_at.isoformat() if sub.last_used_at else None
        } for sub in subscriptions]
    })


@push_bp.route('/subscriptions/<int:id>/name', methods=['PUT'])
@login_required
def rename_subscription(id):
    """Rename a push subscription device."""
    subscription = PushSubscription.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    subscription.device_name = data.get('name', '')[:100]
    db.session.commit()
    
    return jsonify({'success': True})


@push_bp.route('/subscriptions/<int:id>', methods=['DELETE'])
@login_required
def delete_subscription(id):
    """Delete a push subscription."""
    subscription = PushSubscription.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(subscription)
    db.session.commit()
    
    return jsonify({'success': True})


# ============================================================================
# Push Sending (for internal use)
# ============================================================================

def send_push_notification(user_id, title, body, url=None, category='general', icon=None):
    """Send push notification to all active subscriptions for a user.
    
    Args:
        user_id: Target user ID
        title: Notification title
        body: Notification body
        url: Optional click action URL
        category: Notification category (for filtering)
        icon: Optional icon URL
        
    Returns:
        Number of notifications sent
    """
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        current_app.logger.warning('pywebpush not installed, push notifications disabled')
        return 0
    
    vapid_private_key = get_vapid_private_key()
    vapid_claims = get_vapid_claims()
    
    if not vapid_private_key:
        current_app.logger.warning('VAPID private key not configured')
        return 0
    
    subscriptions = PushSubscription.query.filter(
        PushSubscription.user_id == user_id,
        PushSubscription.is_active == True
    ).all()
    
    sent_count = 0
    
    for sub in subscriptions:
        # Check if subscription has this category enabled
        if sub.categories and category not in sub.categories:
            continue
        
        payload = json.dumps({
            'title': title,
            'body': body,
            'url': url,
            'icon': icon or '/static/img/notification-icon.png',
            'category': category
        })
        
        try:
            webpush(
                subscription_info=sub.to_webpush_dict(),
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
            
            sub.last_used_at = datetime.utcnow()
            sent_count += 1
            
        except WebPushException as e:
            if e.response and e.response.status_code in [404, 410]:
                # Subscription expired or unsubscribed
                sub.is_active = False
            else:
                current_app.logger.error(f'Push notification failed: {e}')
    
    db.session.commit()
    return sent_count
