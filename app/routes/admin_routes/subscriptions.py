"""
Subscription Routes
Handles recurring billing subscriptions via Stripe.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app.models import Product, Subscription, db
import stripe
from datetime import datetime

subscriptions_bp = Blueprint('subscriptions', __name__)


@subscriptions_bp.route('/shop/subscribe/<int:product_id>', methods=['POST'])
@login_required
def create_subscription(product_id):
    """Create Stripe subscription checkout session for a subscription product."""
    product = Product.query.get_or_404(product_id)
    
    if not product.is_subscription or not product.stripe_price_id:
        flash('This product is not available for subscription.', 'danger')
        return redirect(url_for('shop.product_detail', product_id=product_id))
    
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    domain_url = request.url_root.rstrip('/')
    
    try:
        # Get or create Stripe customer for user
        customer_id = get_or_create_stripe_customer(current_user)
        
        # Create subscription checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer=customer_id,
            line_items=[{
                'price': product.stripe_price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=domain_url + url_for('subscriptions.subscription_success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + url_for('shop.product_detail', product_id=product_id),
            metadata={
                'product_id': product.id,
                'user_id': current_user.id
            }
        )
        
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        current_app.logger.error(f"Stripe subscription error: {e}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('shop.product_detail', product_id=product_id))


@subscriptions_bp.route('/shop/subscribe/success')
@login_required
def subscription_success():
    """Handle successful subscription creation."""
    session_id = request.args.get('session_id')
    
    if session_id:
        try:
            stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            # Get subscription details
            subscription_id = checkout_session.subscription
            if subscription_id:
                stripe_sub = stripe.Subscription.retrieve(subscription_id)
                product_id = checkout_session.metadata.get('product_id')
                
                # Create local subscription record
                subscription = Subscription(
                    user_id=current_user.id,
                    product_id=product_id,
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=checkout_session.customer,
                    status=stripe_sub.status,
                    current_period_start=datetime.fromtimestamp(stripe_sub.current_period_start),
                    current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end)
                )
                db.session.add(subscription)
                db.session.commit()
                
        except Exception as e:
            current_app.logger.error(f"Error processing subscription success: {e}")
    
    flash('Subscription created successfully!', 'success')
    return redirect(url_for('subscriptions.my_subscriptions'))


@subscriptions_bp.route('/account/subscriptions')
@login_required
def my_subscriptions():
    """View user's active subscriptions."""
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.created_at.desc()).all()
    return render_template('account/subscriptions.html', subscriptions=subscriptions)


@subscriptions_bp.route('/account/subscriptions/api')
@login_required
def subscriptions_api():
    """JSON API for subscriptions dashboard React component."""
    from flask_wtf.csrf import generate_csrf
    
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.created_at.desc()).all()
    
    return jsonify({
        'subscriptions': [{
            'id': s.id,
            'product_name': s.product.name if s.product else 'Unknown Product',
            'product_description': s.product.description if s.product else '',
            'status': s.status or 'unknown',
            'cancel_at_period_end': s.cancel_at_period_end or False,
            'current_period_end': s.current_period_end.isoformat() if s.current_period_end else None,
            'created_at': s.created_at.isoformat() if s.created_at else None
        } for s in subscriptions],
        'stats': {
            'active': sum(1 for s in subscriptions if s.status == 'active'),
            'trialing': sum(1 for s in subscriptions if s.status == 'trialing'),
            'past_due': sum(1 for s in subscriptions if s.status == 'past_due'),
            'canceled': sum(1 for s in subscriptions if s.status == 'canceled')
        },
        'csrf_token': generate_csrf()
    })


@subscriptions_bp.route('/account/subscriptions/<int:subscription_id>/cancel', methods=['POST'])
@login_required
def cancel_subscription(subscription_id):
    """Cancel a subscription."""
    subscription = Subscription.query.get_or_404(subscription_id)
    
    if subscription.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('subscriptions.my_subscriptions'))
    
    if subscription.status == 'canceled':
        flash('Subscription is already canceled.', 'warning')
        return redirect(url_for('subscriptions.my_subscriptions'))
    
    try:
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        
        # Cancel at period end (user keeps access until billing period ends)
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        subscription.cancel_at_period_end = True
        db.session.commit()
        
        flash('Subscription will be canceled at the end of the billing period.', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Stripe cancel error: {e}")
        flash('An error occurred. Please try again.', 'danger')
    
    return redirect(url_for('subscriptions.my_subscriptions'))


@subscriptions_bp.route('/account/subscriptions/portal')
@login_required
def customer_portal():
    """Redirect to Stripe Customer Portal for self-service subscription management."""
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    # Get user's Stripe customer ID from any subscription
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription:
        flash('No active subscriptions found.', 'warning')
        return redirect(url_for('subscriptions.my_subscriptions'))
    
    try:
        domain_url = request.url_root.rstrip('/')
        portal_session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=domain_url + url_for('subscriptions.my_subscriptions')
        )
        return redirect(portal_session.url, code=303)
        
    except Exception as e:
        current_app.logger.error(f"Stripe portal error: {e}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('subscriptions.my_subscriptions'))


def get_or_create_stripe_customer(user):
    """Get existing Stripe customer ID or create new one."""
    # Check if user has any subscription with a customer ID
    existing_sub = Subscription.query.filter_by(user_id=user.id).first()
    if existing_sub and existing_sub.stripe_customer_id:
        return existing_sub.stripe_customer_id
    
    # Create new customer
    customer = stripe.Customer.create(
        email=user.email,
        name=f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
        metadata={'user_id': user.id}
    )
    return customer.id
