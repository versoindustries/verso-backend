"""
Shopping Cart Routes
Session-based cart using Flask's secure cookie session.
Cart stored as {product_id: quantity} dictionary in session.
For logged-in users, cart is persisted to UserCart model.
"""
from flask import Blueprint, render_template, request, session, jsonify, flash, redirect, url_for, current_app, send_file
from flask_login import current_user
from app.models import Product, Order, OrderItem, DownloadToken, UserCart, InventoryLock, DownloadLog, db
from app.modules.security import rate_limiter
import stripe
import secrets
import hashlib
from datetime import datetime, timedelta
from io import BytesIO

cart_bp = Blueprint('cart', __name__, url_prefix='/shop')

# Inventory lock timeout in minutes
INVENTORY_LOCK_TIMEOUT = 15


def get_cart():
    """
    Get cart from session, initialize if not exists.
    For logged-in users, merge session cart with DB cart.
    """
    if 'cart' not in session:
        session['cart'] = {}
    
    # For logged-in users, load cart from DB and merge with session
    if current_user.is_authenticated:
        db_cart = UserCart.query.filter_by(user_id=current_user.id).first()
        if db_cart and db_cart.cart_data:
            # Merge DB cart into session (session takes precedence for quantities)
            for product_id, qty in db_cart.cart_data.items():
                if product_id not in session['cart']:
                    session['cart'][product_id] = qty
            session.modified = True
    
    return session['cart']


def save_cart(cart):
    """
    Save cart to session and optionally to DB for logged-in users.
    """
    session['cart'] = cart
    session.modified = True
    
    # Persist to DB for logged-in users
    if current_user.is_authenticated:
        save_cart_to_db(cart)


def save_cart_to_db(cart):
    """Persist cart to UserCart model for logged-in user."""
    if not current_user.is_authenticated:
        return
    
    db_cart = UserCart.query.filter_by(user_id=current_user.id).first()
    if not db_cart:
        db_cart = UserCart(user_id=current_user.id, cart_data={})
        db.session.add(db_cart)
    
    db_cart.cart_data = cart
    db.session.commit()


def merge_cart_on_login():
    """
    Call this after user login to merge guest cart with DB cart.
    Session cart items take precedence.
    """
    if not current_user.is_authenticated:
        return
    
    session_cart = session.get('cart', {})
    db_cart = UserCart.query.filter_by(user_id=current_user.id).first()
    
    if db_cart and db_cart.cart_data:
        # Merge: DB cart as base, session cart overrides
        merged = dict(db_cart.cart_data)
        merged.update(session_cart)
        session['cart'] = merged
        db_cart.cart_data = merged
        db.session.commit()
    elif session_cart:
        # No existing DB cart, save session cart to DB
        save_cart_to_db(session_cart)
    
    session.modified = True


def get_available_inventory(product):
    """Get available inventory considering active locks."""
    if product.is_digital:
        return float('inf')
    
    # Clean up expired locks first
    cleanup_expired_locks()
    
    # Calculate locked quantity
    locked_qty = db.session.query(db.func.sum(InventoryLock.quantity))\
        .filter_by(product_id=product.id)\
        .filter(InventoryLock.expires_at > datetime.utcnow())\
        .scalar() or 0
    
    return max(0, product.inventory_count - locked_qty)


def create_inventory_locks(order, items):
    """Create inventory locks for checkout items."""
    session_id = session.get('_id', secrets.token_hex(16))
    expires_at = datetime.utcnow() + timedelta(minutes=INVENTORY_LOCK_TIMEOUT)
    
    locks = []
    for item in items:
        product = item['product']
        if not product.is_digital:
            lock = InventoryLock(
                product_id=product.id,
                quantity=item['quantity'],
                session_id=session_id,
                order_id=order.id,
                expires_at=expires_at
            )
            db.session.add(lock)
            locks.append(lock)
    
    db.session.commit()
    return locks


def release_inventory_locks(order_id):
    """Release inventory locks for a completed or cancelled order."""
    InventoryLock.query.filter_by(order_id=order_id).delete()
    db.session.commit()


def cleanup_expired_locks():
    """Remove expired inventory locks."""
    InventoryLock.query.filter(InventoryLock.expires_at < datetime.utcnow()).delete()
    db.session.commit()


def get_cart_items():
    """Get cart items with product details and calculated totals."""
    cart = get_cart()
    items = []
    subtotal = 0
    
    for product_id_str, quantity in cart.items():
        product_id = int(product_id_str)
        product = Product.query.get(product_id)
        if product:
            item_total = product.price * quantity
            subtotal += item_total
            items.append({
                'product': product,
                'quantity': quantity,
                'item_total': item_total
            })
    
    return items, subtotal



@cart_bp.route('/cart')
def view_cart():
    """Display shopping cart page with totals including discounts and gift cards."""
    items, subtotal = get_cart_items()
    
    # Import Phase 13 calculations
    from app.modules.ecommerce import calculate_cart_totals
    
    # Convert items to format expected by calculate_cart_totals
    cart_items_for_calc = [
        {
            'product_id': item['product'].id,
            'price': item['product'].price,
            'quantity': item['quantity']
        }
        for item in items
    ]
    
    # Calculate totals with any applied discounts/gift cards
    totals = calculate_cart_totals(
        cart_items_for_calc,
        discount_code=session.get('discount_code'),
        gift_card_code=session.get('gift_card_code')
    )
    
    # Serialize items for React component
    # NOTE: React CartPage expects prices in CENTS (it divides by 100 for display)
    import json
    items_json = json.dumps([{
        'productId': item['product'].id,
        'name': item['product'].name,
        'price': int(item['product'].price * 100),  # Convert dollars to cents
        'quantity': item['quantity'],
        'maxQuantity': item['product'].inventory_count if not item['product'].is_digital else 99,
        'imageUrl': url_for('media_bp.serve_media', media_id=item['product'].media_id) if item['product'].media_id else None,
        'productUrl': url_for('shop.product_detail', product_id=item['product'].id),
        'isDigital': item['product'].is_digital,
        'itemTotal': int(item['item_total'] * 100)  # Convert dollars to cents
    } for item in items])
    
    # Convert subtotal to cents for React component
    subtotal_cents = int(subtotal * 100)
    
    return render_template('shop/cart.html', 
                          items=items, 
                          subtotal=subtotal_cents,
                          items_json=items_json,
                          totals=totals)


@cart_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart. HTMX-friendly."""
    product = Product.query.get_or_404(product_id)
    
    # Check inventory
    if product.inventory_count < 1 and not product.is_digital:
        if request.headers.get('HX-Request'):
            return jsonify({'error': 'Out of stock'}), 400
        flash('Sorry, this product is out of stock.', 'danger')
        return redirect(url_for('shop.product_detail', product_id=product_id))
    
    cart = get_cart()
    product_id_str = str(product_id)
    
    # Get requested quantity (default 1)
    quantity = int(request.form.get('quantity', 1))
    
    # Add or update quantity
    current_qty = cart.get(product_id_str, 0)
    new_qty = current_qty + quantity
    
    # Check inventory for physical products
    if not product.is_digital and new_qty > product.inventory_count:
        new_qty = product.inventory_count
        flash(f'Only {product.inventory_count} available.', 'warning')
    
    cart[product_id_str] = new_qty
    save_cart(cart)
    
    # HTMX response - return cart drawer partial
    if request.headers.get('HX-Request'):
        items, subtotal = get_cart_items()
        return render_template('shop/partials/cart_drawer.html', 
                             items=items, subtotal=subtotal, 
                             cart_count=sum(cart.values()))
                             
    # JSON response for React
    if request.headers.get('Accept') == 'application/json':
        items, subtotal = get_cart_items()
        return jsonify({
            'success': True,
            'message': f'{product.name} added to cart!',
            'cart_count': sum(cart.values()),
            'subtotal': subtotal,
            'items': [{
                'product_id': item['product'].id,
                'name': item['product'].name,
                'price': item['product'].price,
                'quantity': item['quantity'],
                'item_total': item['item_total'],
                'image_url': url_for('media_bp.serve_media', media_id=item['product'].media_id) if item['product'].media_id else None
            } for item in items]
        })
    
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Remove product from cart."""
    cart = get_cart()
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        del cart[product_id_str]
        save_cart(cart)
    
    # HTMX response
    if request.headers.get('HX-Request'):
        items, subtotal = get_cart_items()
        return render_template('shop/partials/cart_drawer.html', 
                             items=items, subtotal=subtotal,
                             cart_count=sum(cart.values()))

    # JSON response for React
    if request.headers.get('Accept') == 'application/json':
        items, subtotal = get_cart_items()
        return jsonify({
            'success': True,
            'message': 'Item removed from cart.',
            'cart_count': sum(cart.values()),
            'subtotal': subtotal,
            'items': [{
                'product_id': item['product'].id,
                'name': item['product'].name,
                'price': item['product'].price,
                'quantity': item['quantity'],
                'item_total': item['item_total'],
                'image_url': url_for('media_bp.serve_media', media_id=item['product'].media_id) if item['product'].media_id else None
            } for item in items]
        })
    
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/cart/update/<int:product_id>', methods=['POST'])
def update_cart_quantity(product_id):
    """Update product quantity in cart."""
    product = Product.query.get_or_404(product_id)
    cart = get_cart()
    product_id_str = str(product_id)
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        # Remove if quantity is 0 or negative
        if product_id_str in cart:
            del cart[product_id_str]
    else:
        # Check inventory for physical products
        if not product.is_digital and quantity > product.inventory_count:
            quantity = product.inventory_count
            flash(f'Only {product.inventory_count} available.', 'warning')
        cart[product_id_str] = quantity
    
    save_cart(cart)
    
    # HTMX response
    if request.headers.get('HX-Request'):
        items, subtotal = get_cart_items()
        return render_template('shop/partials/cart_drawer.html', 
                             items=items, subtotal=subtotal,
                             cart_count=sum(cart.values()))
                             
    # JSON response for React
    if request.headers.get('Accept') == 'application/json':
        items, subtotal = get_cart_items()
        return jsonify({
            'success': True,
            'message': 'Cart updated.',
            'cart_count': sum(cart.values()),
            'subtotal': subtotal,
            'items': [{
                'product_id': item['product'].id,
                'name': item['product'].name,
                'price': item['product'].price,
                'quantity': item['quantity'],
                'item_total': item['item_total'],
                'image_url': url_for('media_bp.serve_media', media_id=item['product'].media_id) if item['product'].media_id else None
            } for item in items]
        })
    
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/cart/data')
@rate_limiter.exempt
def cart_data():
    """Return cart data as JSON. Useful for HTMX/JS updates."""
    cart = get_cart()
    items, subtotal = get_cart_items()
    
    return jsonify({
        'items': [{
            'product_id': item['product'].id,
            'name': item['product'].name,
            'price': item['product'].price,
            'quantity': item['quantity'],
            'item_total': item['item_total'],
            'image_url': url_for('media_bp.serve_media', media_id=item['product'].media_id) if item['product'].media_id else None
        } for item in items],
        'subtotal': subtotal,
        'item_count': sum(cart.values())
    })


@cart_bp.route('/cart/clear', methods=['POST'])
def clear_cart():
    """Clear entire cart."""
    session['cart'] = {}
    session.modified = True
    
    if request.headers.get('HX-Request'):
        items, subtotal = get_cart_items()
        return render_template('shop/partials/cart_drawer.html', 
                             items=items, subtotal=subtotal, cart_count=0)
    
    flash('Cart cleared.', 'info')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/cart/count')
def cart_count():
    """Return just the cart count for header badge. HTMX partial."""
    cart = get_cart()
    count = sum(cart.values())
    return f'<span class="cart-count">{count}</span>' if count > 0 else ''


@cart_bp.route('/checkout', methods=['POST'])
def checkout():
    """Create Stripe checkout session for entire cart with inventory locking."""
    cart = get_cart()
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    items, subtotal = get_cart_items()
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    # Validate inventory availability (including existing locks)
    for item in items:
        product = item['product']
        available = get_available_inventory(product)
        if item['quantity'] > available:
            if available == 0:
                flash(f'Sorry, {product.name} is out of stock.', 'danger')
            else:
                flash(f'Only {available} units of {product.name} available.', 'warning')
            return redirect(url_for('cart.view_cart'))
    
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
    domain_url = request.url_root.rstrip('/')
    
    try:
        # Create order
        order = Order(
            user_id=current_user.id if current_user.is_authenticated else None,
            total_amount=subtotal,
            status='pending',
            email=current_user.email if current_user.is_authenticated else None
        )
        db.session.add(order)
        db.session.commit()
        
        # Create inventory locks for this order
        create_inventory_locks(order, items)
        
        # Create order items
        line_items = []
        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product'].id,
                quantity=item['quantity'],
                price_at_purchase=item['product'].price
            )
            db.session.add(order_item)
            
            # Build Stripe line item
            product_data = {'name': item['product'].name}
            if item['product'].media_id:
                try:
                    product_data['images'] = [url_for('media_bp.serve_media', media_id=item['product'].media_id, _external=True)]
                except:
                    pass
            
            # Stripe expects amount in cents (integer)
            unit_amount_cents = int(item['product'].price * 100)
            
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': product_data,
                    'unit_amount': unit_amount_cents,
                },
                'quantity': item['quantity'],
            })

        
        db.session.commit()
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=domain_url + url_for('cart.checkout_success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=domain_url + url_for('cart.view_cart'),
            client_reference_id=str(order.id),
            metadata={'order_id': order.id}
        )
        
        # For AJAX/fetch requests, return JSON with redirect URL
        # This is needed because fetch() redirect:follow doesn't work for cross-origin redirects
        if request.headers.get('Accept') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'redirect_url': checkout_session.url
            })
        
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        current_app.logger.error(f"Stripe checkout error: {e}")
        if request.headers.get('Accept') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'An error occurred during checkout. Please try again.'}), 500
        flash('An error occurred during checkout. Please try again.', 'danger')
        return redirect(url_for('cart.view_cart'))


@cart_bp.route('/checkout/success')
def checkout_success():
    """Handle successful checkout - clear cart and show success page."""
    # Clear the cart
    session['cart'] = {}
    session.modified = True
    
    # Get order info from session_id if available
    session_id = request.args.get('session_id')
    order_id = None
    
    if session_id:
        try:
            stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            order_id = checkout_session.client_reference_id
        except:
            pass
    
    return render_template('shop/checkout_success.html', order_id=order_id)


@cart_bp.route('/download/<token>')
def download_file(token):
    """Serve digital download with token verification and logging."""
    download_token = DownloadToken.query.filter_by(token=token).first_or_404()
    
    # Check validity
    if not download_token.is_valid():
        if datetime.utcnow() > download_token.expires_at:
            flash('This download link has expired.', 'danger')
        else:
            flash('Download limit reached.', 'danger')
        return redirect(url_for('shop.index'))
    
    # Get the product file
    order_item = download_token.order_item
    product = order_item.product
    
    if not product.is_digital or not product.file_id:
        flash('This product does not have a downloadable file.', 'danger')
        return redirect(url_for('shop.index'))
    
    # Log the download attempt
    ip_hash = hashlib.sha256(request.remote_addr.encode()).hexdigest() if request.remote_addr else None
    download_log = DownloadLog(
        download_token_id=download_token.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        ip_hash=ip_hash,
        user_agent=request.user_agent.string[:200] if request.user_agent else None
    )
    db.session.add(download_log)
    
    # Increment download count
    download_token.use()
    
    # Serve the file
    from app.models import Media
    file_media = Media.query.get(product.file_id)
    if not file_media:
        flash('File not found.', 'danger')
        return redirect(url_for('shop.index'))
    
    return send_file(
        BytesIO(file_media.data),
        mimetype=file_media.mimetype,
        as_attachment=True,
        download_name=file_media.filename
    )


@cart_bp.route('/my-downloads')
def my_downloads():
    """Show user's digital downloads."""
    if not current_user.is_authenticated:
        flash('Please log in to view your downloads.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Get user's download tokens
    tokens = DownloadToken.query.filter_by(user_id=current_user.id).order_by(DownloadToken.created_at.desc()).all()
    
    return render_template('shop/my_downloads.html', tokens=tokens)

