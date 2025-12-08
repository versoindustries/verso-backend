"""
Phase 9: Outbound Webhook Module

Handles firing webhooks to external URLs when events occur in the application.
Uses the Task queue for reliable delivery with retries.
"""
import hmac
import hashlib
import json
from datetime import datetime
from flask import current_app
from app.database import db


def fire_webhook(event_name, payload):
    """
    Queue webhook delivery tasks for all active webhooks subscribed to this event.
    
    Args:
        event_name: The event type (e.g., 'lead.created', 'order.updated')
        payload: Dictionary of data to send with the webhook
    
    Example:
        fire_webhook('lead.created', {'id': 123, 'email': 'test@example.com'})
    """
    from app.models import Webhook, Task
    
    # Find all active webhooks that subscribe to this event
    webhooks = Webhook.query.filter(
        Webhook.is_active == True
    ).all()
    
    for webhook in webhooks:
        # Check if webhook subscribes to this event
        if event_name not in (webhook.events or []):
            continue
        
        # Create task for webhook delivery
        task = Task(
            name='send_webhook',
            payload={
                'webhook_id': webhook.id,
                'event': event_name,
                'data': payload,
                'url': webhook.url,
                'secret': webhook.secret
            },
            priority=5  # Medium-high priority for webhooks
        )
        db.session.add(task)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to queue webhook tasks: {e}")


def generate_signature(secret, payload_bytes):
    """
    Generate HMAC-SHA256 signature for webhook payload.
    
    Args:
        secret: The webhook's secret key
        payload_bytes: The JSON payload as bytes
    
    Returns:
        Hex-encoded signature string
    """
    if not secret:
        return None
    
    return hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()


def handle_send_webhook(payload):
    """
    Worker task handler for sending webhooks.
    
    Expected payload:
        - webhook_id: ID of the Webhook record
        - event: Event name
        - data: Event data to send
        - url: Target URL
        - secret: HMAC signing secret
    """
    import requests
    from app.models import Webhook
    
    webhook_id = payload.get('webhook_id')
    event = payload.get('event')
    data = payload.get('data')
    url = payload.get('url')
    secret = payload.get('secret')
    
    if not url:
        current_app.logger.error(f"Webhook task missing URL")
        return {'success': False, 'error': 'Missing URL'}
    
    # Build the webhook payload
    webhook_payload = {
        'event': event,
        'timestamp': datetime.utcnow().isoformat(),
        'data': data
    }
    payload_json = json.dumps(webhook_payload, default=str)
    payload_bytes = payload_json.encode('utf-8')
    
    # Generate signature
    signature = generate_signature(secret, payload_bytes)
    
    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Verso-Webhook/1.0',
        'X-Webhook-Event': event,
        'X-Webhook-Timestamp': datetime.utcnow().isoformat()
    }
    
    if signature:
        headers['X-Webhook-Signature'] = f'sha256={signature}'
    
    try:
        response = requests.post(
            url,
            data=payload_bytes,
            headers=headers,
            timeout=30  # 30 second timeout
        )
        
        # Update webhook record
        if webhook_id:
            webhook = Webhook.query.get(webhook_id)
            if webhook:
                webhook.last_triggered_at = datetime.utcnow()
                webhook.last_status_code = response.status_code
                
                if response.status_code >= 200 and response.status_code < 300:
                    webhook.failure_count = 0
                else:
                    webhook.failure_count += 1
                    # Disable after 10 consecutive failures
                    if webhook.failure_count >= 10:
                        webhook.is_active = False
                        current_app.logger.warning(
                            f"Webhook {webhook.name} disabled after 10 failures"
                        )
                
                db.session.commit()
        
        if response.status_code >= 200 and response.status_code < 300:
            current_app.logger.info(f"Webhook delivered: {event} to {url} ({response.status_code})")
            return {'success': True, 'status_code': response.status_code}
        else:
            current_app.logger.warning(
                f"Webhook failed: {event} to {url} ({response.status_code})"
            )
            return {
                'success': False, 
                'status_code': response.status_code,
                'error': f'HTTP {response.status_code}'
            }
    
    except requests.exceptions.Timeout:
        current_app.logger.error(f"Webhook timeout: {url}")
        _update_webhook_failure(webhook_id)
        return {'success': False, 'error': 'Timeout'}
    
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Webhook request error: {url} - {e}")
        _update_webhook_failure(webhook_id)
        return {'success': False, 'error': str(e)}


def _update_webhook_failure(webhook_id):
    """Update webhook failure count on error."""
    if not webhook_id:
        return
    
    from app.models import Webhook
    webhook = Webhook.query.get(webhook_id)
    if webhook:
        webhook.failure_count += 1
        webhook.last_triggered_at = datetime.utcnow()
        if webhook.failure_count >= 10:
            webhook.is_active = False
        db.session.commit()


# Register the handler with the worker
def register_webhook_handler():
    """Register the webhook handler with the task worker."""
    try:
        from app.worker import register_handler
        register_handler('send_webhook', handle_send_webhook)
    except ImportError:
        pass  # Worker module not available
