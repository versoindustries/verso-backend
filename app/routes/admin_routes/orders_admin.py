"""
Order Management Admin Routes
Admin dashboard for viewing and managing orders.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app.models import Order, OrderItem, User, db
from app.modules.decorators import role_required
import stripe

orders_admin_bp = Blueprint('orders_admin', __name__, url_prefix='/admin/shop')


@orders_admin_bp.route('/orders')
@login_required
@role_required('admin')
def orders_list():
    """List all orders with filtering."""
    import json
    
    # Get filter params
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    
    # Location filter for non-super-admins
    if current_user.location_id and not current_user.has_role('super_admin'):
        query = query.filter_by(location_id=current_user.location_id)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get status counts
    status_counts = {
        'all': Order.query.count(),
        'pending': Order.query.filter_by(status='pending').count(),
        'paid': Order.query.filter_by(status='paid').count(),
        'shipped': Order.query.filter_by(status='shipped').count(),
        'delivered': Order.query.filter_by(status='delivered').count(),
        'cancelled': Order.query.filter_by(status='cancelled').count(),
    }
    
    # Serialize for React AdminDataTable
    def get_status_badge(order):
        status_classes = {
            'pending': 'bg-warning text-dark',
            'paid': 'bg-success',
            'processing': 'bg-info',
            'shipped': 'bg-primary',
            'delivered': 'bg-success',
            'cancelled': 'bg-danger',
            'refunded': 'bg-secondary',
        }
        css_class = status_classes.get(order.status, 'bg-secondary')
        return f'<span class="badge {css_class}">{order.status.capitalize()}</span>'
    
    def get_customer_display(order):
        if order.user_id:
            return order.email or f'User #{order.user_id}'
        return order.email or 'Guest'
    
    orders_json = json.dumps([
        {
            'id': o.id,
            'order_num': f'<a href="{url_for("orders_admin.order_detail", order_id=o.id)}">#{o.id}</a>',
            'date': o.created_at.strftime('%b %d, %Y %H:%M'),
            'customer': get_customer_display(o),
            'items': f'{len(o.items)} item(s)',
            'total': f'${o.total_amount / 100:.2f}',
            'status': get_status_badge(o),
            'actions': f'<a href="{url_for("orders_admin.order_detail", order_id=o.id)}" class="btn btn-sm btn-outline-primary">View</a>'
        }
        for o in orders.items
    ])
    
    # Bulk actions configuration
    bulk_actions = json.dumps([
        {'value': 'processing', 'label': 'Mark Processing'},
        {'value': 'shipped', 'label': 'Mark Shipped'},
        {'value': 'delivered', 'label': 'Mark Delivered'},
        {'value': 'cancelled', 'label': 'Cancel Orders', 'destructive': True, 'confirmMessage': 'Are you sure you want to cancel these orders?'}
    ])
    
    return render_template('admin/shop/orders.html', 
                         orders=orders,
                         orders_json=orders_json,
                         bulk_actions=bulk_actions,
                         current_status=status,
                         status_counts=status_counts)


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

