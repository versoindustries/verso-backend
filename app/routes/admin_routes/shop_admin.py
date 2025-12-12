"""
Shop Admin Routes - Unified Dashboard & API
Enterprise-level shop management with JSON APIs for React consumption.
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models import Product, ProductImage, ProductVariant, Category, Media, Order, db
from app.modules.decorators import role_required
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import json

shop_admin_bp = Blueprint('shop_admin', __name__, url_prefix='/admin/shop')


# =============================================================================
# Unified Dashboard Route
# =============================================================================

@shop_admin_bp.route('/')
@login_required
@role_required('admin')
def shop_dashboard():
    """Unified shop dashboard with React component."""
    initial_tab = request.args.get('tab', 'overview')
    return render_template('admin/shop_dashboard.html', initial_tab=initial_tab)


# =============================================================================
# Product API Endpoints
# =============================================================================

@shop_admin_bp.route('/api/products')
@login_required
@role_required('admin')
def api_products_list():
    """List products with filtering, pagination, and search."""
    # Query params
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    product_type = request.args.get('type', '')  # 'digital' or 'physical'
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    low_stock = request.args.get('low_stock', False, type=bool)
    
    # Build query
    query = Product.query
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if product_type == 'digital':
        query = query.filter(Product.is_digital == True)
    elif product_type == 'physical':
        query = query.filter(Product.is_digital == False)
    
    if low_stock:
        query = query.filter(Product.inventory_count <= 5, Product.is_digital == False)
    
    # Location filter for non-super-admins
    if current_user.location_id and not current_user.has_role('super_admin'):
        query = query.filter(Product.location_id == current_user.location_id)
    
    # Sorting
    sort_col = getattr(Product, sort_by, Product.created_at)
    if sort_order == 'asc':
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())
    
    # Paginate
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Serialize
    products_data = []
    for p in products.items:
        image_url = None
        if p.media_id:
            image_url = url_for('media_bp.serve_media', media_id=p.media_id)
        
        products_data.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': p.price,
            'price_display': f'${p.price / 100:.2f}',
            'inventory_count': p.inventory_count,
            'is_digital': p.is_digital,
            'category_id': p.category_id,
            'image_url': image_url,
            'variants_count': len(p.variants) if hasattr(p, 'variants') else 0,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'updated_at': p.updated_at.isoformat() if p.updated_at else None,
        })
    
    return jsonify({
        'products': products_data,
        'pagination': {
            'page': products.page,
            'pages': products.pages,
            'per_page': products.per_page,
            'total': products.total,
            'has_next': products.has_next,
            'has_prev': products.has_prev,
        }
    })


@shop_admin_bp.route('/api/products/<int:product_id>')
@login_required
@role_required('admin')
def api_product_detail(product_id):
    """Get single product with all details."""
    product = Product.query.get_or_404(product_id)
    
    # Get primary image
    image_url = None
    if product.media_id:
        image_url = url_for('media_bp.serve_media', media_id=product.media_id)
    
    # Get additional images
    images = []
    if hasattr(product, 'images'):
        for img in product.images:
            images.append({
                'id': img.id,
                'url': url_for('media_bp.serve_media', media_id=img.media_id),
                'alt_text': img.alt_text,
                'position': img.position,
                'is_primary': img.is_primary,
            })
    
    # Get variants
    variants = []
    if hasattr(product, 'variants'):
        for v in product.variants:
            variants.append({
                'id': v.id,
                'sku': v.sku,
                'name': v.name,
                'price_adjustment': v.price_adjustment,
                'inventory_count': v.inventory_count,
                'attributes': v.attributes,
                'is_active': v.is_active,
            })
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'price_display': f'${product.price / 100:.2f}',
        'inventory_count': product.inventory_count,
        'is_digital': product.is_digital,
        'is_subscription': product.is_subscription,
        'stripe_price_id': product.stripe_price_id,
        'category_id': product.category_id,
        'image_url': image_url,
        'images': images,
        'variants': variants,
        'created_at': product.created_at.isoformat() if product.created_at else None,
        'updated_at': product.updated_at.isoformat() if product.updated_at else None,
    })


@shop_admin_bp.route('/api/products', methods=['POST'])
@login_required
@role_required('admin')
def api_create_product():
    """Create new product via JSON API."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Product name is required'}), 400
    
    price_dollars = data.get('price', 0)
    try:
        price_cents = int(float(price_dollars) * 100)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid price'}), 400
    
    product = Product(
        name=name,
        description=data.get('description', ''),
        price=price_cents,
        inventory_count=data.get('inventory_count', 0),
        is_digital=data.get('is_digital', False),
        category_id=data.get('category_id'),
        location_id=current_user.location_id,
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Product created successfully',
        'product': {
            'id': product.id,
            'name': product.name,
        }
    }), 201


@shop_admin_bp.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
@role_required('admin')
def api_update_product(product_id):
    """Update existing product."""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'name' in data:
        product.name = data['name'].strip()
    
    if 'description' in data:
        product.description = data['description']
    
    if 'price' in data:
        try:
            product.price = int(float(data['price']) * 100)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid price'}), 400
    
    if 'inventory_count' in data:
        product.inventory_count = int(data['inventory_count'])
    
    if 'is_digital' in data:
        product.is_digital = bool(data['is_digital'])
    
    if 'category_id' in data:
        product.category_id = data['category_id']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Product updated successfully',
    })


@shop_admin_bp.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def api_delete_product(product_id):
    """Delete product."""
    product = Product.query.get_or_404(product_id)
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Product deleted successfully',
    })


@shop_admin_bp.route('/api/products/<int:product_id>/image', methods=['POST'])
@login_required
@role_required('admin')
def api_upload_product_image(product_id):
    """Upload image for product."""
    product = Product.query.get_or_404(product_id)
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image_file = request.files['image']
    if not image_file.filename:
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(image_file.filename)
    mimetype = image_file.mimetype
    data = image_file.read()
    
    media = Media(
        filename=filename,
        data=data,
        mimetype=mimetype,
        size=len(data),
        uploaded_by_id=current_user.id
    )
    db.session.add(media)
    db.session.flush()
    
    # Set as primary image
    product.media_id = media.id
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Image uploaded successfully',
        'image_url': url_for('media_bp.serve_media', media_id=media.id),
    })


@shop_admin_bp.route('/api/stats')
@login_required
@role_required('admin')
def api_shop_stats():
    """Get shop statistics for dashboard."""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Product stats
    total_products = Product.query.count()
    digital_products = Product.query.filter(Product.is_digital == True).count()
    physical_products = total_products - digital_products
    low_stock_count = Product.query.filter(
        Product.inventory_count <= 5,
        Product.is_digital == False
    ).count()
    
    # Order stats (basic)
    total_orders = Order.query.count()
    orders_today = Order.query.filter(Order.created_at >= today_start).count()
    orders_month = Order.query.filter(Order.created_at >= month_start).count()
    
    # Revenue
    paid_orders = Order.query.filter(Order.status.in_(['paid', 'shipped', 'delivered']))
    revenue_month = sum(o.total_amount for o in paid_orders.filter(Order.created_at >= month_start).all())
    revenue_today = sum(o.total_amount for o in paid_orders.filter(Order.created_at >= today_start).all())
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    recent_orders_data = [{
        'id': o.id,
        'status': o.status,
        'total': f'${o.total_amount / 100:.2f}',
        'date': o.created_at.strftime('%b %d, %H:%M') if o.created_at else '',
        'email': o.email or 'N/A',
    } for o in recent_orders]
    
    # Low stock products
    low_stock_products = Product.query.filter(
        Product.inventory_count <= 5,
        Product.is_digital == False
    ).order_by(Product.inventory_count.asc()).limit(5).all()
    
    low_stock_data = [{
        'id': p.id,
        'name': p.name,
        'inventory': p.inventory_count,
    } for p in low_stock_products]
    
    return jsonify({
        'products': {
            'total': total_products,
            'digital': digital_products,
            'physical': physical_products,
            'low_stock': low_stock_count,
        },
        'orders': {
            'total': total_orders,
            'today': orders_today,
            'month': orders_month,
        },
        'revenue': {
            'month': revenue_month,
            'month_display': f'${revenue_month / 100:.2f}',
            'today': revenue_today,
            'today_display': f'${revenue_today / 100:.2f}',
        },
        'recent_orders': recent_orders_data,
        'low_stock_alerts': low_stock_data,
    })


@shop_admin_bp.route('/api/categories')
@login_required
@role_required('admin')
def api_categories():
    """Get categories for product filtering/selection."""
    categories = Category.query.order_by(Category.name).all()
    return jsonify({
        'categories': [{
            'id': c.id,
            'name': c.name,
            'slug': c.slug if hasattr(c, 'slug') else None,
        } for c in categories]
    })


# =============================================================================
# Legacy Routes (kept for backward compatibility, redirect to new dashboard)
# =============================================================================

@shop_admin_bp.route('/products')
@login_required
@role_required('admin')
def products():
    """Legacy products route - redirects to unified dashboard."""
    return redirect(url_for('shop_admin.shop_dashboard', tab='products'))


@shop_admin_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_product():
    """Legacy create product route."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price_dollars = request.form.get('price')
        price_cents = int(float(price_dollars) * 100)
        inventory = int(request.form.get('inventory'))
        is_digital = request.form.get('is_digital') == 'on'
        
        # Image Upload
        image_file = request.files.get('image')
        media_id = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            mimetype = image_file.mimetype
            data = image_file.read()
            
            media = Media(
                filename=filename,
                data=data,
                mimetype=mimetype,
                size=len(data),
                uploaded_by_id=current_user.id
            )
            db.session.add(media)
            db.session.flush()
            media_id = media.id
            
        product = Product(
            name=name,
            description=description,
            price=price_cents,
            inventory_count=inventory,
            is_digital=is_digital,
            media_id=media_id
        )
        db.session.add(product)
        db.session.commit()
        flash('Product created successfully!', 'success')
        return redirect(url_for('shop_admin.shop_dashboard', tab='products'))
        
    return render_template('admin/shop/create_product.html')


@shop_admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_product(id):
    """Legacy edit product route."""
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        price_dollars = request.form.get('price')
        product.price = int(float(price_dollars) * 100)
        product.inventory_count = int(request.form.get('inventory'))
        product.is_digital = request.form.get('is_digital') == 'on'
        
        # Image Update
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            mimetype = image_file.mimetype
            data = image_file.read()
            
            media = Media(
                filename=filename,
                data=data,
                mimetype=mimetype,
                size=len(data),
                uploaded_by_id=current_user.id
            )
            db.session.add(media)
            db.session.flush()
            product.media_id = media.id
            
        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('shop_admin.shop_dashboard', tab='products'))
        
    return render_template('admin/shop/edit_product.html', product=product)


@shop_admin_bp.route('/products/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_product(id):
    """Legacy delete product route."""
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'success')
    return redirect(url_for('shop_admin.shop_dashboard', tab='products'))

