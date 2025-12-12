from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import current_user
from app.models import Product, Order, OrderItem, Category, Wishlist, db
from sqlalchemy import or_, func
import stripe

shop_bp = Blueprint('shop', __name__, url_prefix='/shop')


# =============================================================================
# API Endpoints for React ShopStorefront
# =============================================================================

@shop_bp.route('/api/products')
def api_products():
    """Get paginated products with filtering and sorting for the React storefront."""
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 12, type=int), 50)
        
        # Filters
        search = request.args.get('search', '').strip()
        category_id = request.args.get('category', type=int)
        min_price = request.args.get('min_price', type=int)
        max_price = request.args.get('max_price', type=int)
        product_type = request.args.get('type')  # 'digital' or 'physical'
        
        # Sorting
        sort = request.args.get('sort', 'newest')
        
        # Build query
        query = Product.query
        
        # Search filter
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f'%{search}%'),
                    Product.description.ilike(f'%{search}%')
                )
            )
        
        # Category filter
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        # Price filters
        if min_price:
            query = query.filter(Product.price >= min_price)
        if max_price:
            query = query.filter(Product.price <= max_price)
        
        # Product type filter
        if product_type == 'digital':
            query = query.filter(Product.is_digital == True)
        elif product_type == 'physical':
            query = query.filter(Product.is_digital == False)
        
        # Sorting
        if sort == 'newest':
            query = query.order_by(Product.created_at.desc())
        elif sort == 'price_low':
            query = query.order_by(Product.price.asc())
        elif sort == 'price_high':
            query = query.order_by(Product.price.desc())
        elif sort == 'popular':
            query = query.order_by(Product.created_at.desc())  # TODO: Add popularity tracking
        elif sort == 'rating':
            query = query.order_by(Product.created_at.desc())  # TODO: Add rating
        else:
            query = query.order_by(Product.created_at.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Check wishlist status for authenticated users
        wishlist_product_ids = set()
        if current_user.is_authenticated:
            wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
            wishlist_product_ids = {item.product_id for item in wishlist_items}
        
        # Serialize products
        products = []
        for product in paginated.items:
            # Get category name
            category_name = None
            if product.category_id:
                category = Category.query.get(product.category_id)
                category_name = category.name if category else None
            
            # Get image URL
            image_url = None
            if product.media_id:
                image_url = url_for('media_bp.serve_media', media_id=product.media_id)
            
            products.append({
                'id': product.id,
                'name': product.name,
                'description': product.description or '',
                'price': product.price,
                'price_display': f'${product.price / 100:.2f}',
                'inventory_count': product.inventory_count,
                'is_digital': product.is_digital,
                'category_id': product.category_id,
                'category_name': category_name,
                'image_url': image_url,
                'rating': 4.5,  # TODO: Calculate from reviews
                'reviews_count': 0,  # TODO: Get from reviews
                'is_new': False,  # TODO: Calculate based on created_at
                'is_featured': False,  # TODO: Add featured flag
                'in_wishlist': product.id in wishlist_product_ids
            })
        
        return jsonify({
            'products': products,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in api_products: {e}")
        return jsonify({'error': str(e)}), 500


@shop_bp.route('/api/categories')
def api_categories():
    """Get all product categories with product counts."""
    try:
        # Get categories with product counts
        categories = db.session.query(
            Category.id,
            Category.name,
            Category.slug,
            func.count(Product.id).label('product_count')
        ).outerjoin(
            Product, Category.id == Product.category_id
        ).group_by(
            Category.id
        ).order_by(
            Category.display_order
        ).all()
        
        result = [{
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug,
            'product_count': cat.product_count
        } for cat in categories]
        
        return jsonify({'categories': result})
    except Exception as e:
        current_app.logger.error(f"Error in api_categories: {e}")
        return jsonify({'error': str(e)}), 500


@shop_bp.route('/api/related/<int:product_id>')
def api_related(product_id):
    """Get related products for a product (same category)."""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Get products from the same category, excluding current product
        if product.category_id:
            related = Product.query.filter(
                Product.category_id == product.category_id,
                Product.id != product_id
            ).limit(4).all()
        else:
            # Fallback: get random products
            related = Product.query.filter(
                Product.id != product_id
            ).limit(4).all()
        
        result = []
        for p in related:
            image_url = None
            if p.media_id:
                image_url = url_for('media_bp.serve_media', media_id=p.media_id)
            
            result.append({
                'id': p.id,
                'name': p.name,
                'price': p.price,
                'price_display': f'${p.price / 100:.2f}',
                'image_url': image_url
            })
        
        return jsonify({'products': result})
    except Exception as e:
        current_app.logger.error(f"Error in api_related: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# Page Routes
# =============================================================================

@shop_bp.route('/')
def index():
    """Shop index page - renders the React ShopStorefront."""
    # Get initial data for server-side rendering / SEO
    products = Product.query.order_by(Product.created_at.desc()).limit(12).all()
    categories = Category.query.order_by(Category.display_order).all()
    return render_template('shop/index.html', products=products, categories=categories)

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

        # Stripe expects amount in cents (integer)
        unit_amount_cents = int(product.price * 100)
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                        'images': [url_for('media_bp.serve_media', media_id=product.media_id, _external=True)] if product.media_id else [],
                    },
                    'unit_amount': unit_amount_cents,
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


# =============================================================================
# Inline Content Editing API
# =============================================================================

@shop_bp.route('/api/product/<int:id>/content', methods=['PATCH'])
def update_product_content(id):
    """
    Update product content via inline editor.
    Accessible to Admin, Manager, Marketing, and Owner roles.
    """
    from flask_login import login_required, current_user
    from app.modules.auth_manager import role_required
    import bleach
    
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Check permissions
    privileged_roles = ['Admin', 'Manager', 'Marketing', 'Owner']
    is_privileged = any(current_user.has_role(role) for role in privileged_roles)
    
    if not is_privileged:
        return jsonify({'error': 'You do not have permission to edit products'}), 403
    
    product = Product.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Allowed HTML tags for descriptions
    ALLOWED_TAGS = [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul', 'ol', 'li', 'br',
        'strong', 'em', 'u', 'blockquote', 'code', 'pre', 'img', 'div', 'span'
    ]
    ALLOWED_ATTRS = {
        '*': ['class', 'id', 'style'],
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'width', 'height']
    }
    
    # Update name if provided
    if 'title' in data and data['title']:
        product.name = bleach.clean(data['title'], tags=[], strip=True)
    
    # Update description if provided (sanitize HTML)
    if 'content' in data and data['content']:
        product.description = bleach.clean(
            data['content'], 
            tags=ALLOWED_TAGS, 
            attributes=ALLOWED_ATTRS,
            strip=True
        )
    
    # Update SEO fields if product model supports them
    if hasattr(product, 'meta_title') and 'metaTitle' in data:
        product.meta_title = bleach.clean(data['metaTitle'], tags=[], strip=True)[:70]
    
    if hasattr(product, 'meta_description') and 'metaDescription' in data:
        product.meta_description = bleach.clean(data['metaDescription'], tags=[], strip=True)[:200]
    
    # Update Open Graph fields if product model supports them
    if hasattr(product, 'og_title') and 'ogTitle' in data:
        product.og_title = bleach.clean(data['ogTitle'], tags=[], strip=True)
    
    if hasattr(product, 'og_description') and 'ogDescription' in data:
        product.og_description = bleach.clean(data['ogDescription'], tags=[], strip=True)
    
    if hasattr(product, 'og_image') and 'ogImage' in data:
        product.og_image = bleach.clean(data['ogImage'], tags=[], strip=True)
    
    db.session.commit()
    current_app.logger.info(f"Product '{product.name}' updated via inline editor by {current_user.username}")
    
    return jsonify({
        'success': True,
        'message': 'Product updated successfully',
        'product': {
            'id': product.id,
            'name': product.name,
            'description': product.description[:100] if product.description else ''
        }
    })
