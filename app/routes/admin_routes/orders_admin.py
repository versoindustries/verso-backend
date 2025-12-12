"""
Order Management Admin Routes
Admin dashboard for viewing and managing orders with JSON APIs.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app.models import Order, OrderItem, User, db
from app.modules.decorators import role_required
from datetime import datetime
import stripe
import json

orders_admin_bp = Blueprint('orders_admin', __name__, url_prefix='/admin/shop')


# =============================================================================
# JSON API Endpoints for React Dashboard
# =============================================================================

@orders_admin_bp.route('/api/orders')
@login_required
@role_required('admin')
def api_orders_list():
    """List orders with filtering and pagination for React dashboard."""
    # Query params
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Build query
    query = Order.query
    
    if status:
        query = query.filter(Order.status == status)
    
    if search:
        query = query.filter(Order.email.ilike(f'%{search}%'))
    
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from)
            query = query.filter(Order.created_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to)
            query = query.filter(Order.created_at <= to_date)
        except ValueError:
            pass
    
    # Location filter for non-super-admins
    if current_user.location_id and not current_user.has_role('super_admin'):
        query = query.filter(Order.location_id == current_user.location_id)
    
    # Paginate
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Serialize
    orders_data = []
    for o in orders.items:
        customer_name = 'Guest'
        if o.user_id:
            user = User.query.get(o.user_id)
            if user:
                customer_name = user.first_name or user.username or user.email
        
        orders_data.append({
            'id': o.id,
            'status': o.status,
            'total': o.total_amount,
            'total_display': f'${o.total_amount / 100:.2f}',
            'email': o.email or 'N/A',
            'customer_name': customer_name,
            'items_count': len(o.items),
            'shipping_address': o.shipping_address,
            'tracking_number': o.tracking_number,
            'carrier': o.carrier,
            'created_at': o.created_at.isoformat() if o.created_at else None,
            'shipped_at': o.shipped_at.isoformat() if o.shipped_at else None,
            'delivered_at': o.delivered_at.isoformat() if o.delivered_at else None,
        })
    
    # Get status counts
    status_counts = {
        'all': Order.query.count(),
        'pending': Order.query.filter_by(status='pending').count(),
        'paid': Order.query.filter_by(status='paid').count(),
        'processing': Order.query.filter_by(status='processing').count(),
        'shipped': Order.query.filter_by(status='shipped').count(),
        'delivered': Order.query.filter_by(status='delivered').count(),
        'cancelled': Order.query.filter_by(status='cancelled').count(),
        'refunded': Order.query.filter_by(status='refunded').count(),
    }
    
    return jsonify({
        'orders': orders_data,
        'status_counts': status_counts,
        'pagination': {
            'page': orders.page,
            'pages': orders.pages,
            'per_page': orders.per_page,
            'total': orders.total,
            'has_next': orders.has_next,
            'has_prev': orders.has_prev,
        }
    })


@orders_admin_bp.route('/api/orders/<int:order_id>')
@login_required
@role_required('admin')
def api_order_detail(order_id):
    """Get single order with full details."""
    order = Order.query.get_or_404(order_id)
    
    # Get customer info
    customer = None
    if order.user_id:
        user = User.query.get(order.user_id)
        if user:
            customer = {
                'id': user.id,
                'name': f'{user.first_name or ""} {user.last_name or user.username or ""}'.strip(),
                'email': user.email,
                'phone': user.phone if hasattr(user, 'phone') else None,
            }
    
    # Serialize items
    items = []
    for item in order.items:
        product = item.product
        image_url = None
        if product and product.media_id:
            image_url = url_for('media_bp.serve_media', media_id=product.media_id)
        
        items.append({
            'id': item.id,
            'product_id': item.product_id,
            'product_name': product.name if product else 'Unknown Product',
            'quantity': item.quantity,
            'price': item.price_at_purchase,
            'price_display': f'${item.price_at_purchase / 100:.2f}',
            'total': item.price_at_purchase * item.quantity,
            'total_display': f'${(item.price_at_purchase * item.quantity) / 100:.2f}',
            'is_digital': product.is_digital if product else False,
            'image_url': image_url,
        })
    
    return jsonify({
        'id': order.id,
        'status': order.status,
        'total': order.total_amount,
        'total_display': f'${order.total_amount / 100:.2f}',
        'currency': order.currency,
        'email': order.email,
        'customer': customer,
        'items': items,
        'shipping_address': order.shipping_address,
        'stripe_payment_intent_id': order.stripe_payment_intent_id,
        'tracking_number': order.tracking_number,
        'carrier': order.carrier,
        'fulfillment_status': order.fulfillment_status,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'shipped_at': order.shipped_at.isoformat() if order.shipped_at else None,
        'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
    })


@orders_admin_bp.route('/api/orders/<int:order_id>/status', methods=['POST'])
@login_required
@role_required('admin')
def api_update_order_status(order_id):
    """Update order status via JSON API."""
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    new_status = data.get('status')
    valid_statuses = ['pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled']
    
    if new_status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400
    
    old_status = order.status
    order.status = new_status
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Order status updated from {old_status} to {new_status}',
        'old_status': old_status,
        'new_status': new_status,
    })


@orders_admin_bp.route('/api/orders/<int:order_id>/ship', methods=['POST'])
@login_required
@role_required('admin')
def api_ship_order(order_id):
    """Mark order as shipped with tracking info via JSON API."""
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    if order.status not in ['paid', 'processing']:
        return jsonify({'error': 'Order must be paid or processing to ship'}), 400
    
    tracking_number = data.get('tracking_number', '').strip() if data else ''
    carrier = data.get('carrier', '').strip() if data else ''
    
    order.status = 'shipped'
    order.tracking_number = tracking_number or None
    order.carrier = carrier or None
    order.shipped_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Order marked as shipped',
        'tracking_number': order.tracking_number,
        'carrier': order.carrier,
    })


@orders_admin_bp.route('/api/orders/<int:order_id>/refund', methods=['POST'])
@login_required
@role_required('admin')
def api_refund_order(order_id):
    """Process refund via Stripe JSON API."""
    order = Order.query.get_or_404(order_id)
    data = request.get_json() or {}
    
    if not order.stripe_payment_intent_id:
        return jsonify({'error': 'No payment intent found for this order'}), 400
    
    if order.status in ['cancelled', 'refunded']:
        return jsonify({'error': 'Order has already been cancelled or refunded'}), 400
    
    try:
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        
        refund = stripe.Refund.create(
            payment_intent=order.stripe_payment_intent_id,
            reason=data.get('reason', 'requested_by_customer')
        )
        
        order.status = 'refunded'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Refund processed successfully',
            'refund_id': refund.id,
        })
        
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe refund error: {e}")
        return jsonify({'error': f'Refund failed: {str(e)}'}), 400


@orders_admin_bp.route('/api/orders/bulk-status', methods=['POST'])
@login_required
@role_required('admin')
def api_bulk_update_status():
    """Bulk update order statuses via JSON API."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    order_ids = data.get('order_ids', [])
    new_status = data.get('status')
    
    valid_statuses = ['pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400
    
    updated = 0
    for order_id in order_ids:
        order = Order.query.get(order_id)
        if order:
            order.status = new_status
            updated += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{updated} orders updated to {new_status}',
        'updated_count': updated,
    })


# =============================================================================
# Legacy Routes (redirect to unified dashboard)
# =============================================================================

@orders_admin_bp.route('/orders')
@login_required
@role_required('admin')
def orders_list():
    """Legacy orders list - redirects to unified shop dashboard."""
    return redirect(url_for('shop_admin.shop_dashboard', tab='orders'))




@orders_admin_bp.route('/orders/<int:order_id>')
@login_required
@role_required('admin')
def order_detail(order_id):
    """View order details."""
    order = Order.query.get_or_404(order_id)
    
    # Get customer info
    customer = None
    if order.user_id:
        customer = User.query.get(order.user_id)
    
    return render_template('admin/shop/order_detail.html', 
                         order=order, 
                         customer=customer)


@orders_admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@role_required('admin')
def update_order_status(order_id):
    """Update order status."""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    valid_statuses = ['pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        flash('Invalid status.', 'danger')
        return redirect(url_for('orders_admin.order_detail', order_id=order_id))
    
    old_status = order.status
    order.status = new_status
    db.session.commit()
    
    flash(f'Order status updated from {old_status} to {new_status}.', 'success')
    return redirect(url_for('orders_admin.order_detail', order_id=order_id))


@orders_admin_bp.route('/orders/<int:order_id>/refund', methods=['POST'])
@login_required
@role_required('admin')
def refund_order(order_id):
    """Process refund via Stripe."""
    order = Order.query.get_or_404(order_id)
    
    if not order.stripe_payment_intent_id:
        flash('No payment intent found for this order.', 'danger')
        return redirect(url_for('orders_admin.order_detail', order_id=order_id))
    
    if order.status in ['cancelled', 'refunded']:
        flash('Order has already been cancelled or refunded.', 'warning')
        return redirect(url_for('orders_admin.order_detail', order_id=order_id))
    
    try:
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        
        # Create refund
        refund = stripe.Refund.create(
            payment_intent=order.stripe_payment_intent_id,
            reason=request.form.get('reason', 'requested_by_customer')
        )
        
        order.status = 'refunded'
        db.session.commit()
        
        flash(f'Refund processed successfully. Refund ID: {refund.id}', 'success')
        
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe refund error: {e}")
        flash(f'Refund failed: {str(e)}', 'danger')
    
    return redirect(url_for('orders_admin.order_detail', order_id=order_id))


@orders_admin_bp.route('/orders/bulk-status', methods=['POST'])
@login_required
@role_required('admin')
def bulk_update_status():
    """Bulk update order statuses."""
    order_ids = request.form.getlist('order_ids')
    new_status = request.form.get('status')
    
    valid_statuses = ['pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        flash('Invalid status.', 'danger')
        return redirect(url_for('orders_admin.orders_list'))
    
    updated = 0
    for order_id in order_ids:
        order = Order.query.get(order_id)
        if order:
            order.status = new_status
            updated += 1
    
    db.session.commit()
    flash(f'{updated} orders updated to {new_status}.', 'success')
    return redirect(url_for('orders_admin.orders_list'))


@orders_admin_bp.route('/orders/<int:order_id>/ship', methods=['POST'])
@login_required
@role_required('admin')
def ship_order(order_id):
    """Mark order as shipped with tracking information."""
    from datetime import datetime
    
    order = Order.query.get_or_404(order_id)
    
    if order.status not in ['paid', 'processing']:
        flash('Order must be paid or processing to ship.', 'warning')
        return redirect(url_for('orders_admin.order_detail', order_id=order_id))
    
    tracking_number = request.form.get('tracking_number', '').strip()
    carrier = request.form.get('carrier', '').strip()
    
    order.status = 'shipped'
    order.tracking_number = tracking_number or None
    order.carrier = carrier or None
    order.shipped_at = datetime.utcnow()
    
    db.session.commit()
    
    # TODO: Send shipment notification email to customer
    
    flash(f'Order marked as shipped.{" Tracking: " + tracking_number if tracking_number else ""}', 'success')
    return redirect(url_for('orders_admin.order_detail', order_id=order_id))


@orders_admin_bp.route('/orders/<int:order_id>/deliver', methods=['POST'])
@login_required
@role_required('admin')
def deliver_order(order_id):
    """Mark order as delivered."""
    from datetime import datetime
    from app.routes.cart import release_inventory_locks
    
    order = Order.query.get_or_404(order_id)
    
    if order.status != 'shipped':
        flash('Order must be shipped before marking as delivered.', 'warning')
        return redirect(url_for('orders_admin.order_detail', order_id=order_id))
    
    order.status = 'delivered'
    order.delivered_at = datetime.utcnow()
    
    # Release any remaining inventory locks for this order
    release_inventory_locks(order_id)
    
    db.session.commit()
    
    flash('Order marked as delivered.', 'success')
    return redirect(url_for('orders_admin.order_detail', order_id=order_id))

