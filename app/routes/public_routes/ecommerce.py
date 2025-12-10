"""
E-Commerce Public Routes

Customer-facing routes for browsing collections, viewing bundles,
managing wishlist, applying discounts, and checkout flow.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app.database import db
from app.models import (
    Collection, CollectionProduct, Product,
    ProductBundle, BundleItem, ProductVariant,
    Discount, GiftCard,
    Wishlist, RecentlyViewed
)
from app.modules.ecommerce import (
    calculate_cart_totals, get_collection_products, 
    get_related_products, validate_discount, validate_gift_card
)
from datetime import datetime

ecommerce_bp = Blueprint('ecommerce', __name__)


# =============================================================================
# Collections
# =============================================================================

@ecommerce_bp.route('/collections')
def list_collections():
    """Browse all published collections."""
    collections = Collection.query.filter_by(
        is_published=True
    ).order_by(Collection.name).all()
    
    # Filter to only active collections
    active_collections = [c for c in collections if c.is_active()]
    
    return render_template('shop/collections/index.html', collections=active_collections)


@ecommerce_bp.route('/collections/<slug>')
def view_collection(slug):
    """View a single collection with its products."""
    collection = Collection.query.filter_by(slug=slug, is_published=True).first_or_404()
    
    if not collection.is_active():
        flash('This collection is not currently available.', 'info')
        return redirect(url_for('ecommerce.list_collections'))
    
    # Get products for this collection
    products = get_collection_products(collection)
    
    # Apply sorting from query params
    sort = request.args.get('sort', collection.sort_order)
    if sort == 'price_asc':
        products = sorted(products, key=lambda p: p.price)
    elif sort == 'price_desc':
        products = sorted(products, key=lambda p: p.price, reverse=True)
    elif sort == 'newest':
        products = sorted(products, key=lambda p: p.created_at, reverse=True)
    elif sort == 'alpha':
        products = sorted(products, key=lambda p: p.name)
    
    return render_template('shop/collections/detail.html', 
                          collection=collection, 
                          products=products,
                          current_sort=sort)


# =============================================================================
# Bundles
# =============================================================================

@ecommerce_bp.route('/bundles/<slug>')
def view_bundle(slug):
    """View a product bundle."""
    bundle = ProductBundle.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Check date range
    now = datetime.utcnow()
    if bundle.starts_at and now < bundle.starts_at:
        flash('This bundle is not yet available.', 'info')
        return redirect(url_for('shop.index'))
    if bundle.ends_at and now > bundle.ends_at:
        flash('This bundle has expired.', 'info')
        return redirect(url_for('shop.index'))
    
    return render_template('shop/bundles/detail.html', bundle=bundle)


@ecommerce_bp.route('/bundles/<slug>/add-to-cart', methods=['POST'])
def add_bundle_to_cart(slug):
    """Add all bundle items to cart."""
    bundle = ProductBundle.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Get the cart helper functions from cart.py
    from app.routes.cart import get_cart, save_cart
    
    cart = get_cart()
    
    # Add each bundle item to cart
    for item in bundle.items:
        if not item.is_optional or request.form.get(f'include_{item.id}') == 'on':
            product_id = str(item.product_id)
            quantity = item.quantity
            
            if product_id in cart:
                cart[product_id] += quantity
            else:
                cart[product_id] = quantity
    
    save_cart(cart)
    flash(f'"{bundle.name}" added to cart!', 'success')
    
    # Return HTMX response or redirect
    if request.headers.get('HX-Request'):
        return '', 204, {'HX-Trigger': 'cartUpdated'}
    
    return redirect(url_for('cart.view_cart'))


# =============================================================================
# Wishlist
# =============================================================================

@ecommerce_bp.route('/wishlist')
@login_required
def view_wishlist():
    """View user's wishlist."""
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id)\
        .order_by(Wishlist.added_at.desc()).all()
    
    return render_template('shop/wishlist.html', wishlist_items=wishlist_items)


@ecommerce_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    """Add a product to wishlist."""
    product = Product.query.get_or_404(product_id)
    variant_id = request.form.get('variant_id')
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id,
        variant_id=int(variant_id) if variant_id else None
    ).first()
    
    if existing:
        # HTMX response
        if request.headers.get('HX-Request'):
            return render_template('shop/partials/wishlist_button.html', 
                                  product=product, in_wishlist=True)
        flash('Already in your wishlist!', 'info')
        return redirect(request.referrer or url_for('shop.index'))
    
    wishlist_item = Wishlist(
        user_id=current_user.id,
        product_id=product_id,
        variant_id=int(variant_id) if variant_id else None
    )
    db.session.add(wishlist_item)
    db.session.commit()
    
    # HTMX response
    if request.headers.get('HX-Request'):
        return render_template('shop/partials/wishlist_button.html', 
                              product=product, in_wishlist=True)
    
    flash(f'"{product.name}" added to wishlist!', 'success')
    return redirect(request.referrer or url_for('shop.index'))


@ecommerce_bp.route('/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    """Remove a product from wishlist."""
    variant_id = request.form.get('variant_id')
    
    item = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id,
        variant_id=int(variant_id) if variant_id else None
    ).first()
    
    if item:
        db.session.delete(item)
        db.session.commit()
    
    product = Product.query.get(product_id)
    
    # HTMX response
    if request.headers.get('HX-Request'):
        return render_template('shop/partials/wishlist_button.html', 
                              product=product, in_wishlist=False)
    
    flash('Removed from wishlist.', 'success')
    return redirect(request.referrer or url_for('ecommerce.view_wishlist'))


@ecommerce_bp.route('/wishlist/move-to-cart/<int:id>', methods=['POST'])
@login_required
def move_wishlist_to_cart(id):
    """Move a wishlist item to cart."""
    item = Wishlist.query.filter_by(
        id=id, 
        user_id=current_user.id
    ).first_or_404()
    
    # Add to cart
    from app.routes.cart import get_cart, save_cart
    cart = get_cart()
    product_id = str(item.product_id)
    
    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1
    
    save_cart(cart)
    
    # Remove from wishlist
    db.session.delete(item)
    db.session.commit()
    
    flash('Moved to cart!', 'success')
    return redirect(url_for('ecommerce.view_wishlist'))


# =============================================================================
# Discounts & Gift Cards (Cart Integration)
# =============================================================================

@ecommerce_bp.route('/cart/apply-discount', methods=['POST'])
def apply_discount():
    """Apply a discount code to the cart."""
    code = request.form.get('discount_code', '').strip().upper()
    
    if not code:
        flash('Please enter a discount code.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    discount = Discount.query.filter_by(code=code, is_active=True).first()
    
    if not discount:
        flash('Invalid discount code.', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    # Validate the discount
    from app.routes.cart import get_cart_items
    cart_items = get_cart_items()
    
    is_valid, error = validate_discount(discount, cart_items, 
                                        current_user if current_user.is_authenticated else None)
    
    if not is_valid:
        flash(error, 'danger')
        return redirect(url_for('cart.view_cart'))
    
    # Store in session
    session['discount_code'] = code
    flash(f'Discount "{discount.name}" applied!', 'success')
    return redirect(url_for('cart.view_cart'))


@ecommerce_bp.route('/cart/remove-discount', methods=['POST'])
def remove_discount():
    """Remove applied discount from cart."""
    if 'discount_code' in session:
        del session['discount_code']
    flash('Discount removed.', 'success')
    return redirect(url_for('cart.view_cart'))


@ecommerce_bp.route('/cart/apply-gift-card', methods=['POST'])
def apply_gift_card():
    """Apply a gift card to the cart."""
    code = request.form.get('gift_card_code', '').strip().upper()
    
    if not code:
        flash('Please enter a gift card code.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    gift_card = GiftCard.query.filter_by(code=code, is_active=True).first()
    
    if not gift_card:
        flash('Invalid gift card code.', 'danger')
        return redirect(url_for('cart.view_cart'))
    
    is_valid, error = validate_gift_card(gift_card)
    
    if not is_valid:
        flash(error, 'danger')
        return redirect(url_for('cart.view_cart'))
    
    # Store in session
    session['gift_card_code'] = code
    flash(f'Gift card applied! Balance: ${gift_card.current_balance_cents/100:.2f}', 'success')
    return redirect(url_for('cart.view_cart'))


@ecommerce_bp.route('/cart/remove-gift-card', methods=['POST'])
def remove_gift_card():
    """Remove applied gift card from cart."""
    if 'gift_card_code' in session:
        del session['gift_card_code']
    flash('Gift card removed.', 'success')
    return redirect(url_for('cart.view_cart'))


# =============================================================================
# Gift Card Balance Check
# =============================================================================

@ecommerce_bp.route('/gift-cards/check-balance', methods=['GET', 'POST'])
def check_gift_card_balance():
    """Check gift card balance page."""
    balance_info = None
    error = None
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        
        if code:
            gift_card = GiftCard.query.filter_by(code=code).first()
            
            if gift_card:
                is_valid, err = validate_gift_card(gift_card)
                if is_valid:
                    balance_info = {
                        'code': gift_card.code,
                        'balance': gift_card.current_balance_cents / 100,
                        'initial': gift_card.initial_balance_cents / 100,
                        'expires_at': gift_card.expires_at
                    }
                else:
                    error = err
            else:
                error = "Gift card not found"
        else:
            error = "Please enter a gift card code"
    
    return render_template('shop/gift-cards/balance.html', 
                          balance_info=balance_info, error=error)


# =============================================================================
# Enhanced Checkout
# =============================================================================

@ecommerce_bp.route('/checkout')
def checkout():
    """Multi-step checkout page."""
    from app.routes.cart import get_cart_items
    
    cart_items = get_cart_items()
    if not cart_items:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))
    
    # Calculate totals with any applied discounts/gift cards
    totals = calculate_cart_totals(
        cart_items,
        discount_code=session.get('discount_code'),
        gift_card_code=session.get('gift_card_code')
    )
    
    return render_template('shop/checkout/index.html', 
                          cart_items=cart_items, 
                          totals=totals)


@ecommerce_bp.route('/checkout/calculate-shipping', methods=['POST'])
def calculate_shipping_rates():
    """Calculate shipping rates for the given address."""
    from app.routes.cart import get_cart_items
    from app.modules.ecommerce import calculate_shipping
    
    cart_items = get_cart_items()
    
    country = request.form.get('country', 'US')
    state = request.form.get('state')
    zip_code = request.form.get('zip_code')
    
    shipping_cents, rates = calculate_shipping(cart_items, country, state, zip_code)
    
    # Return as JSON for HTMX/JS
    return jsonify({
        'shipping_cents': shipping_cents,
        'rates': rates
    })


# =============================================================================
# Recently Viewed (Middleware Helper)
# =============================================================================

def track_product_view(product_id):
    """Track a product view for recommendations."""
    user_id = current_user.id if current_user.is_authenticated else None
    session_id = session.get('_id', session.sid if hasattr(session, 'sid') else None)
    
    # Check if already viewed recently (within last hour)
    existing = RecentlyViewed.query.filter(
        RecentlyViewed.product_id == product_id,
        (RecentlyViewed.user_id == user_id) if user_id else (RecentlyViewed.session_id == session_id)
    ).first()
    
    if existing:
        existing.viewed_at = datetime.utcnow()
    else:
        view = RecentlyViewed(
            user_id=user_id,
            session_id=session_id if not user_id else None,
            product_id=product_id
        )
        db.session.add(view)
    
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


def get_recently_viewed_products(limit=8):
    """Get recently viewed products for the current user/session."""
    user_id = current_user.id if current_user.is_authenticated else None
    session_id = session.get('_id')
    
    if user_id:
        query = RecentlyViewed.query.filter_by(user_id=user_id)
    elif session_id:
        query = RecentlyViewed.query.filter_by(session_id=session_id)
    else:
        return []
    
    recent = query.order_by(RecentlyViewed.viewed_at.desc()).limit(limit).all()
    return [r.product for r in recent if r.product]


# =============================================================================
# Context Processors
# =============================================================================

@ecommerce_bp.context_processor
def inject_wishlist_count():
    """Inject wishlist count into templates."""
    wishlist_count = 0
    if current_user.is_authenticated:
        wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()
    return dict(wishlist_count=wishlist_count)


@ecommerce_bp.context_processor
def inject_featured_collections():
    """Inject featured collections for homepage."""
    featured = Collection.query.filter_by(
        is_published=True,
        show_on_homepage=True
    ).order_by(Collection.name).limit(4).all()
    return dict(featured_collections=featured)
