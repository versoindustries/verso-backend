"""
Phase 9: Enhanced REST API with write endpoints, pagination, filtering, and webhook support.
"""
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, g
from app.models import ApiKey, ContactFormSubmission, Order, Product, User, Webhook
from app.database import db
import hashlib
from datetime import datetime
from sqlalchemy import desc, asc

api = Blueprint('api', __name__, url_prefix='/api/v1')


# ============================================================================
# Authentication Decorator
# ============================================================================

def require_api_key(scope=None):
    """Decorator to require API key authentication with optional scope check."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid API key'}), 401
            
            key = auth_header.split(' ')[1]
            key_hash = hashlib.sha256(key.encode('utf-8')).hexdigest()
            
            api_key = ApiKey.query.filter_by(key_hash=key_hash).first()
            
            if not api_key or not api_key.is_active:
                return jsonify({'error': 'Invalid or inactive API key'}), 401
                
            # Update last used
            try:
                api_key.last_used_at = datetime.utcnow()
                db.session.commit()
            except:
                pass  # Don't fail request if stats update fails
            
            # Check scope
            if scope:
                if scope not in api_key.scopes:
                    return jsonify({'error': f'Insufficient permissions. Required scope: {scope}'}), 403

            g.api_key = api_key
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# Pagination Helper
# ============================================================================

def paginate_query(query, default_per_page=25, max_per_page=100):
    """Apply pagination to SQLAlchemy query and return data with metadata."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', default_per_page, type=int)
    
    # Enforce limits
    page = max(1, page)
    per_page = min(max(1, per_page), max_per_page)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page  # Ceiling division
        }
    }


def apply_sorting(query, model, default_sort='created_at', default_order='desc'):
    """Apply sorting based on query parameters."""
    sort_field = request.args.get('sort', default_sort)
    order = request.args.get('order', default_order).lower()
    
    # Get the column if it exists on the model
    column = getattr(model, sort_field, None)
    if column is not None:
        if order == 'asc':
            query = query.order_by(asc(column))
        else:
            query = query.order_by(desc(column))
    
    return query


def fire_webhook_event(event_name, payload):
    """Trigger system event (Webhooks + Workflows)."""
    try:
        from app.modules.automation import trigger_event
        trigger_event(event_name, payload)
    except ImportError:
        current_app.logger.warning("Automation module not available")
    except Exception as e:
        current_app.logger.error(f"Error triggering event: {e}")


# ============================================================================
# Leads Endpoints
# ============================================================================

@api.route('/leads', methods=['GET'])
@require_api_key(scope='read:leads')
def get_leads():
    """
    Get all leads with optional filtering, sorting, and pagination.
    
    Query params:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 25, max: 100)
    - sort: Field to sort by (default: submitted_at)
    - order: Sort order 'asc' or 'desc' (default: desc)
    - status: Filter by status
    - created_after: Filter leads created after this date (ISO format)
    - created_before: Filter leads created before this date (ISO format)
    """
    query = ContactFormSubmission.query
    
    # Apply filters
    status = request.args.get('status')
    if status:
        query = query.filter(ContactFormSubmission.status == status)
    
    created_after = request.args.get('created_after')
    if created_after:
        try:
            after_date = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
            query = query.filter(ContactFormSubmission.submitted_at >= after_date)
        except ValueError:
            return jsonify({'error': 'Invalid created_after date format. Use ISO format.'}), 400
    
    created_before = request.args.get('created_before')
    if created_before:
        try:
            before_date = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
            query = query.filter(ContactFormSubmission.submitted_at <= before_date)
        except ValueError:
            return jsonify({'error': 'Invalid created_before date format. Use ISO format.'}), 400
    
    # Apply sorting
    query = apply_sorting(query, ContactFormSubmission, default_sort='submitted_at')
    
    # Apply pagination
    result = paginate_query(query)
    
    leads_data = [{
        'id': l.id,
        'first_name': l.first_name,
        'last_name': l.last_name,
        'email': l.email,
        'phone': l.phone,
        'message': l.message,
        'status': l.status,
        'source': l.source,
        'submitted_at': l.submitted_at.isoformat() if l.submitted_at else None
    } for l in result['items']]
    
    return jsonify({
        'data': leads_data,
        'pagination': result['pagination']
    })


@api.route('/leads/<int:lead_id>', methods=['GET'])
@require_api_key(scope='read:leads')
def get_lead(lead_id):
    """Get a single lead by ID."""
    lead = ContactFormSubmission.query.get_or_404(lead_id)
    return jsonify({
        'id': lead.id,
        'first_name': lead.first_name,
        'last_name': lead.last_name,
        'email': lead.email,
        'phone': lead.phone,
        'message': lead.message,
        'status': lead.status,
        'source': lead.source,
        'notes': lead.notes,
        'tags': lead.tags,
        'submitted_at': lead.submitted_at.isoformat() if lead.submitted_at else None
    })


@api.route('/leads', methods=['POST'])
@require_api_key(scope='write:leads')
def create_lead():
    """
    Create a new lead.
    
    Required fields: first_name, last_name, email, phone, message
    Optional fields: status, source, notes, tags
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    # Validate required fields
    required_fields = ['first_name', 'last_name', 'email', 'phone', 'message']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
    
    # Create lead
    lead = ContactFormSubmission(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data['phone'],
        message=data['message'],
        status=data.get('status', 'New'),
        source=data.get('source', 'api'),
        notes=data.get('notes'),
        tags=data.get('tags', [])
    )
    
    db.session.add(lead)
    db.session.commit()
    
    # Fire webhook
    fire_webhook_event('lead.created', {
        'id': lead.id,
        'first_name': lead.first_name,
        'last_name': lead.last_name,
        'email': lead.email,
        'source': lead.source
    })
    
    return jsonify({
        'id': lead.id,
        'message': 'Lead created successfully'
    }), 201


@api.route('/leads/<int:lead_id>', methods=['PATCH'])
@require_api_key(scope='write:leads')
def update_lead(lead_id):
    """
    Update an existing lead.
    
    All fields are optional. Only provided fields will be updated.
    """
    lead = ContactFormSubmission.query.get_or_404(lead_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    # Update allowed fields
    updatable_fields = ['first_name', 'last_name', 'email', 'phone', 'message', 
                        'status', 'source', 'notes', 'tags']
    
    for field in updatable_fields:
        if field in data:
            setattr(lead, field, data[field])
    
    db.session.commit()
    
    # Fire webhook for status changes
    if 'status' in data:
        fire_webhook_event('lead.updated', {
            'id': lead.id,
            'status': lead.status
        })
    
    return jsonify({
        'id': lead.id,
        'message': 'Lead updated successfully'
    })


# ============================================================================
# Orders Endpoints
# ============================================================================

@api.route('/orders', methods=['GET'])
@require_api_key(scope='read:orders')
def get_orders():
    """
    Get all orders with optional filtering, sorting, and pagination.
    
    Query params:
    - page, per_page, sort, order: Standard pagination/sorting
    - status: Filter by order status
    - created_after, created_before: Date range filters
    """
    query = Order.query
    
    # Apply filters
    status = request.args.get('status')
    if status:
        query = query.filter(Order.status == status)
    
    created_after = request.args.get('created_after')
    if created_after:
        try:
            after_date = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
            query = query.filter(Order.created_at >= after_date)
        except ValueError:
            return jsonify({'error': 'Invalid created_after date format'}), 400
    
    created_before = request.args.get('created_before')
    if created_before:
        try:
            before_date = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
            query = query.filter(Order.created_at <= before_date)
        except ValueError:
            return jsonify({'error': 'Invalid created_before date format'}), 400
    
    # Apply sorting
    query = apply_sorting(query, Order, default_sort='created_at')
    
    # Apply pagination
    result = paginate_query(query)
    
    orders_data = [{
        'id': o.id,
        'status': o.status,
        'total_amount': o.total_amount,
        'currency': o.currency,
        'tracking_number': o.tracking_number,
        'created_at': o.created_at.isoformat() if o.created_at else None,
        'items_count': len(o.items) if o.items else 0
    } for o in result['items']]
    
    return jsonify({
        'data': orders_data,
        'pagination': result['pagination']
    })


@api.route('/orders/<int:order_id>', methods=['GET'])
@require_api_key(scope='read:orders')
def get_order(order_id):
    """Get a single order with full details including items."""
    order = Order.query.get_or_404(order_id)
    
    items_data = [{
        'id': item.id,
        'product_id': item.product_id,
        'product_name': item.product.name if item.product else None,
        'quantity': item.quantity,
        'unit_price': item.unit_price
    } for item in order.items] if order.items else []
    
    return jsonify({
        'id': order.id,
        'status': order.status,
        'total_amount': order.total_amount,
        'currency': order.currency,
        'tracking_number': order.tracking_number,
        'email': order.email,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'items': items_data
    })


@api.route('/orders/<int:order_id>', methods=['PATCH'])
@require_api_key(scope='write:orders')
def update_order(order_id):
    """
    Update an order's status or fulfillment details.
    
    Updatable fields: status, fulfillment_status, tracking_number
    """
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    old_status = order.status
    
    # Update allowed fields
    if 'status' in data:
        valid_statuses = ['pending', 'paid', 'shipped', 'delivered', 'cancelled', 'refunded']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Valid: {", ".join(valid_statuses)}'}), 400
        order.status = data['status']
    
    if 'tracking_number' in data:
        order.tracking_number = data['tracking_number']
        
    if 'fulfillment_status' in data:
        order.fulfillment_status = data['fulfillment_status']
    
    db.session.commit()
    
    # Fire webhook
    fire_webhook_event('order.updated', {
        'id': order.id,
        'old_status': old_status,
        'new_status': order.status,
        'fulfillment_status': order.fulfillment_status
    })
    
    return jsonify({
        'id': order.id,
        'message': 'Order updated successfully'
    })


# ============================================================================
# Products Endpoints
# ============================================================================

@api.route('/products', methods=['GET'])
@require_api_key(scope='read:products')
def get_products():
    """
    Get all products with optional filtering, sorting, and pagination.
    
    Query params:
    - is_digital: Filter by digital/physical
    - in_stock: Filter products with inventory > 0
    """
    query = Product.query
    
    # Apply filters
    is_digital = request.args.get('is_digital')
    if is_digital is not None:
        is_digital_bool = is_digital.lower() in ('true', '1', 'yes')
        query = query.filter(Product.is_digital == is_digital_bool)
    
    in_stock = request.args.get('in_stock')
    if in_stock is not None and in_stock.lower() in ('true', '1', 'yes'):
        query = query.filter(Product.inventory_count > 0)
    
    # Apply sorting
    query = apply_sorting(query, Product, default_sort='name', default_order='asc')
    
    # Apply pagination
    result = paginate_query(query)
    
    products_data = [{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price,  # Price in cents
        'inventory_count': p.inventory_count,
        'is_digital': p.is_digital
    } for p in result['items']]
    
    return jsonify({
        'data': products_data,
        'pagination': result['pagination']
    })


@api.route('/products/<int:product_id>', methods=['GET'])
@require_api_key(scope='read:products')
def get_product(product_id):
    """Get a single product by ID."""
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,  # Price in cents
        'inventory_count': product.inventory_count,
        'is_digital': product.is_digital
    })


@api.route('/products', methods=['POST'])
@require_api_key(scope='write:products')
def create_product():
    """
    Create a new product.
    
    Required fields: name, price
    Optional fields: description, inventory_count, is_digital, is_active
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Missing required field: name'}), 400
    if 'price' not in data:
        return jsonify({'error': 'Missing required field: price'}), 400
    
    try:
        price = int(data['price'])  # Price in cents
        if price < 0:
            return jsonify({'error': 'Price must be non-negative'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid price format'}), 400
    
    # Create product
    product = Product(
        name=data['name'],
        description=data.get('description', ''),
        price=price,  # Price in cents
        inventory_count=data.get('inventory_count', 0),
        is_digital=data.get('is_digital', False)
    )
    
    db.session.add(product)
    db.session.commit()
    
    # Fire webhook
    fire_webhook_event('product.created', {
        'id': product.id,
        'name': product.name,
        'price': product.price
    })
    
    return jsonify({
        'id': product.id,
        'message': 'Product created successfully'
    }), 201


@api.route('/products/<int:product_id>', methods=['PATCH'])
@require_api_key(scope='write:products')
def update_product(product_id):
    """
    Update an existing product.
    
    All fields are optional. Only provided fields will be updated.
    """
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    # Update allowed fields
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        try:
            price = int(data['price'])  # Price in cents
            if price < 0:
                return jsonify({'error': 'Price must be non-negative'}), 400
            product.price = price
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid price format'}), 400
    if 'inventory_count' in data:
        product.inventory_count = int(data['inventory_count'])
    if 'is_digital' in data:
        product.is_digital = bool(data['is_digital'])
    
    db.session.commit()
    
    return jsonify({
        'id': product.id,
        'message': 'Product updated successfully'
    })


# ============================================================================
# Webhooks Endpoints (for managing outbound webhooks via API)
# ============================================================================

@api.route('/webhooks', methods=['GET'])
@require_api_key(scope='admin:webhooks')
def get_webhooks():
    """Get all configured webhooks."""
    webhooks = Webhook.query.all()
    return jsonify({
        'data': [w.to_dict() for w in webhooks]
    })


@api.route('/webhooks', methods=['POST'])
@require_api_key(scope='admin:webhooks')
def create_webhook():
    """
    Create a new outbound webhook.
    
    Required: name, url, events
    Optional: secret (for HMAC signing)
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    if not data.get('name') or not data.get('url') or not data.get('events'):
        return jsonify({'error': 'Missing required fields: name, url, events'}), 400
    
    # Validate events
    valid_events = ['lead.created', 'lead.updated', 'order.created', 'order.updated', 'product.created']
    invalid = [e for e in data['events'] if e not in valid_events]
    if invalid:
        return jsonify({'error': f'Invalid events: {", ".join(invalid)}. Valid: {", ".join(valid_events)}'}), 400
    
    import secrets
    webhook = Webhook(
        name=data['name'],
        url=data['url'],
        events=data['events'],
        secret=data.get('secret') or secrets.token_hex(32),
        is_active=data.get('is_active', True),
        created_by_id=g.api_key.user_id
    )
    
    db.session.add(webhook)
    db.session.commit()
    
    return jsonify({
        'id': webhook.id,
        'secret': webhook.secret,  # Return secret once on creation
        'message': 'Webhook created successfully'
    }), 201


@api.route('/webhooks/<int:webhook_id>', methods=['DELETE'])
@require_api_key(scope='admin:webhooks')
def delete_webhook(webhook_id):
    """Delete a webhook."""
    webhook = Webhook.query.get_or_404(webhook_id)
    db.session.delete(webhook)
    db.session.commit()
    
    return jsonify({'message': 'Webhook deleted successfully'})
