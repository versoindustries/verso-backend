from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import current_user
from app.models import Product, Order, OrderItem, db
import stripe

shop_bp = Blueprint('shop', __name__, url_prefix='/shop')

@shop_bp.route('/')
def index():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('shop/index.html', products=products)

@shop_bp.route('/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('shop/product.html', product=product)

@shop_bp.route('/checkout-session/<int:product_id>', methods=['POST'])
def checkout_session(product_id):
    product = Product.query.get_or_404(product_id)
    if product.inventory_count < 1:
        flash('Sorry, this product is out of stock.', 'danger')
        return redirect(url_for('shop.product_detail', product_id=product_id))

    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    domain_url = request.url_root.rstrip('/') # e.g. http://localhost:5000

    try:
        # Create a pending order effectively? Or wait until webhook?
        # Strategy: Metadata in session to create order later, OR create pending order now.
        # Creating pending order now is safer for inventory lock, but requires expiration.
        # Simple approach: Create pending order now.
        
        order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            total_amount=product.price, # For single item
            status='pending',
            email=current_user.email if current_user.is_authenticated else None 
        )
        db.session.add(order)
        db.session.commit()
        
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            price_at_purchase=product.price
        )
        db.session.add(item)
        db.session.commit()

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                        'images': [url_for('media_bp.serve_media', media_id=product.media_id, _external=True)] if product.media_id else [],
                    },
                    'unit_amount': product.price,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=domain_url + url_for('shop.success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + url_for('shop.product_detail', product_id=product_id),
            client_reference_id=str(order.id),
            metadata={
                'order_id': order.id
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        current_app.logger.error(f"Stripe error: {e}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('shop.product_detail', product_id=product_id))

@shop_bp.route('/success')
def success():
    return render_template('shop/success.html')
