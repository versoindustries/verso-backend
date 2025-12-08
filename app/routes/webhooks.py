from flask import Blueprint, request, jsonify, current_app
from app.models import Order, Product, OrderItem, DownloadToken, Subscription, db
import stripe
import secrets
from datetime import datetime, timedelta

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')

@webhooks_bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    event_type = event['type']
    data = event['data']['object']

    # Handle the event
    if event_type == 'checkout.session.completed':
        handle_checkout_session(data)
    elif event_type == 'invoice.paid':
        handle_invoice_paid(data)
    elif event_type == 'invoice.payment_failed':
        handle_invoice_payment_failed(data)
    elif event_type == 'customer.subscription.updated':
        handle_subscription_updated(data)
    elif event_type == 'customer.subscription.deleted':
        handle_subscription_deleted(data)

    return jsonify(success=True)


def handle_checkout_session(session):
    """Handle successful checkout - mark order as paid."""
    order_id = session.get('client_reference_id')
    payment_intent_id = session.get('payment_intent')
    
    if order_id:
        order = Order.query.get(order_id)
        if order:
            order.status = 'paid'
            order.stripe_payment_intent_id = payment_intent_id
            
            # Release inventory locks for this order (inventory already reserved)
            from app.routes.cart import release_inventory_locks
            release_inventory_locks(order.id)
            
            # Process each item
            for item in order.items:
                product = item.product
                
                # Decrement inventory for physical products
                if not product.is_digital and product.inventory_count > 0:
                    product.inventory_count -= item.quantity
                
                # Generate download tokens for digital products
                if product.is_digital and product.file_id:
                    token = DownloadToken(
                        token=secrets.token_urlsafe(32),
                        order_item_id=item.id,
                        user_id=order.user_id,
                        max_downloads=3,
                        download_count=0,
                        expires_at=datetime.utcnow() + timedelta(days=30)
                    )
                    db.session.add(token)
            
            db.session.commit()
            current_app.logger.info(f"Order {order.id} marked as paid.")
            
            # TODO: Send order confirmation email via worker
        else:
            current_app.logger.warning(f"Order {order_id} not found.")


def handle_invoice_paid(invoice):
    """Handle successful subscription invoice payment."""
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return
    
    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
    if subscription:
        subscription.status = 'active'
        
        # Update period dates from Stripe
        period_start = invoice.get('period_start')
        period_end = invoice.get('period_end')
        if period_start:
            subscription.current_period_start = datetime.fromtimestamp(period_start)
        if period_end:
            subscription.current_period_end = datetime.fromtimestamp(period_end)
        
        db.session.commit()
        current_app.logger.info(f"Subscription {subscription_id} invoice paid.")


def handle_invoice_payment_failed(invoice):
    """Handle failed subscription invoice payment."""
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return
    
    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
    if subscription:
        subscription.status = 'past_due'
        db.session.commit()
        current_app.logger.warning(f"Subscription {subscription_id} payment failed.")
        
        # TODO: Send payment failed notification email


def handle_subscription_updated(stripe_sub):
    """Handle subscription updates from Stripe."""
    subscription_id = stripe_sub.get('id')
    
    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
    if subscription:
        subscription.status = stripe_sub.get('status', subscription.status)
        subscription.cancel_at_period_end = stripe_sub.get('cancel_at_period_end', False)
        
        # Update period dates
        if stripe_sub.get('current_period_start'):
            subscription.current_period_start = datetime.fromtimestamp(stripe_sub['current_period_start'])
        if stripe_sub.get('current_period_end'):
            subscription.current_period_end = datetime.fromtimestamp(stripe_sub['current_period_end'])
        
        db.session.commit()
        current_app.logger.info(f"Subscription {subscription_id} updated to status: {subscription.status}")


def handle_subscription_deleted(stripe_sub):
    """Handle subscription cancellation/deletion from Stripe."""
    subscription_id = stripe_sub.get('id')
    
    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()
    if subscription:
        subscription.status = 'canceled'
        db.session.commit()
        current_app.logger.info(f"Subscription {subscription_id} canceled.")
        
        # TODO: Send cancellation confirmation email


