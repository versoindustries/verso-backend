"""
Phase 14: Reports Blueprint

Provides financial reporting, custom report builder, and multi-format exports.
"""

from flask import (
    Blueprint, render_template, jsonify, request, flash, 
    redirect, url_for, send_file, Response
)
from flask_login import login_required, current_user
from app.models import SavedReport, ReportExport, Order, Product, User, db
from app.modules.decorators import role_required
from app.modules.reporting import (
    calculate_revenue_metrics, calculate_daily_revenue,
    calculate_product_performance, calculate_customer_clv,
    calculate_tax_report, export_to_csv, export_to_excel,
    execute_saved_report, get_date_range_presets
)
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import os
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/admin/reports')


@reports_bp.route('/')
@login_required
@role_required('admin')
def index():
    """Reports overview page."""
    return redirect(url_for('reports.revenue'))


@reports_bp.route('/revenue')
@login_required
@role_required('admin')
def revenue():
    """Revenue dashboard with date picker."""
    # Parse date range
    preset = request.args.get('preset', 'last_30_days')
    presets = get_date_range_presets()
    
    if preset in presets:
        start_date, end_date = presets[preset]
    else:
        # Custom date range
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d') if start_str else datetime.utcnow() - timedelta(days=30)
            end_date = datetime.strptime(end_str, '%Y-%m-%d') if end_str else datetime.utcnow()
        except ValueError:
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
    
    # Get metrics
    metrics = calculate_revenue_metrics(start_date, end_date)
    daily_data = calculate_daily_revenue(start_date, end_date)
    
    # Payment method breakdown
    payment_methods = db.session.query(
        func.coalesce(Order.currency, 'usd').label('currency'),
        func.count(Order.id).label('count'),
        func.sum(Order.total_amount).label('total')
    ).filter(
        Order.status == 'paid',
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).group_by(Order.currency).all()
    
    return render_template('admin/reports/revenue.html',
        metrics=metrics,
        daily_data=daily_data,
        payment_methods=payment_methods,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        presets=presets
    )


@reports_bp.route('/products')
@login_required
@role_required('admin')
def products():
    """Product performance matrix."""
    # Parse date range
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 50, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get product performance
    products_data = calculate_product_performance(start_date, end_date, limit=limit)
    
    # Category breakdown
    from app.models import Category
    category_revenue = db.session.query(
        Category.name,
        func.sum(Order.total_amount).label('revenue')
    ).select_from(Order).join(
        Order.items
    ).join(
        Product, Product.id == db.literal_column('order_item.product_id')
    ).outerjoin(
        Category, Category.id == Product.category_id
    ).filter(
        Order.status == 'paid',
        Order.created_at >= start_date
    ).group_by(Category.name).order_by(desc('revenue')).all()
    
    return render_template('admin/reports/products.html',
        products=products_data,
        category_revenue=category_revenue,
        days=days,
        limit=limit,
        start_date=start_date,
        end_date=end_date
    )


@reports_bp.route('/customers')
@login_required
@role_required('admin')
def customers():
    """Customer CLV analysis."""
    limit = request.args.get('limit', 100, type=int)
    
    # Get customer data
    customers_data = calculate_customer_clv(limit=limit)
    
    # Summary stats
    total_customers = User.query.count()
    customers_with_orders = db.session.query(
        func.count(func.distinct(Order.user_id))
    ).filter(Order.status == 'paid').scalar() or 0
    
    avg_clv = 0
    if customers_data:
        avg_clv = sum(c['total_spent'] for c in customers_data) / len(customers_data)
    
    # Repeat purchase rate
    repeat_customers = db.session.query(
        func.count(func.distinct(Order.user_id))
    ).filter(
        Order.status == 'paid'
    ).having(
        func.count(Order.id) > 1
    ).scalar() or 0
    
    repeat_rate = (repeat_customers / customers_with_orders * 100) if customers_with_orders > 0 else 0
    
    return render_template('admin/reports/customers.html',
        customers=customers_data,
        total_customers=total_customers,
        customers_with_orders=customers_with_orders,
        avg_clv=round(avg_clv, 2),
        repeat_rate=round(repeat_rate, 1),
        limit=limit
    )


@reports_bp.route('/tax')
@login_required
@role_required('admin')
def tax():
    """Tax liability report."""
    # Parse date range
    preset = request.args.get('preset', 'this_month')
    presets = get_date_range_presets()
    
    if preset in presets:
        start_date, end_date = presets[preset]
    else:
        start_str = request.args.get('start_date')
        end_str = request.args.get('end_date')
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d') if start_str else datetime.utcnow().replace(day=1)
            end_date = datetime.strptime(end_str, '%Y-%m-%d') if end_str else datetime.utcnow()
        except ValueError:
            start_date = datetime.utcnow().replace(day=1)
            end_date = datetime.utcnow()
    
    # Get tax report
    tax_data = calculate_tax_report(start_date, end_date)
    
    return render_template('admin/reports/tax.html',
        tax_data=tax_data,
        preset=preset,
        start_date=start_date,
        end_date=end_date,
        presets=presets
    )


# ============================================================================
# Saved Reports
# ============================================================================

@reports_bp.route('/saved')
@login_required
@role_required('admin')
def saved():
    """Saved reports library."""
    reports = SavedReport.query.filter(
        db.or_(
            SavedReport.created_by_id == current_user.id,
            SavedReport.is_public == True
        ),
        SavedReport.is_archived == False
    ).order_by(desc(SavedReport.created_at)).all()
    
    return render_template('admin/reports/saved/index.html', reports=reports)


@reports_bp.route('/saved/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_saved():
    """Create a new saved report."""
    if request.method == 'POST':
        config = {
            'days': int(request.form.get('days', 30)),
            'limit': int(request.form.get('limit', 100)),
            'filters': {}
        }
        
        report = SavedReport(
            name=request.form.get('name'),
            description=request.form.get('description'),
            report_type=request.form.get('report_type'),
            config_json=config,
            is_public=request.form.get('is_public') == 'on',
            created_by_id=current_user.id
        )
        db.session.add(report)
        db.session.commit()
        flash('Report saved successfully.', 'success')
        return redirect(url_for('reports.saved'))
    
    return render_template('admin/reports/saved/create.html')


@reports_bp.route('/saved/<int:report_id>')
@login_required
@role_required('admin')
def view_saved(report_id):
    """View/run a saved report."""
    report = SavedReport.query.get_or_404(report_id)
    
    # Check permissions
    if not report.is_public and report.created_by_id != current_user.id:
        flash('You do not have permission to view this report.', 'danger')
        return redirect(url_for('reports.saved'))
    
    # Execute report
    data = execute_saved_report(report)
    
    # Update last run
    report.last_run_at = datetime.utcnow()
    db.session.commit()
    
    return render_template('admin/reports/saved/view.html',
        report=report,
        data=data
    )


@reports_bp.route('/saved/<int:report_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_saved(report_id):
    """Delete a saved report."""
    report = SavedReport.query.get_or_404(report_id)
    
    if report.created_by_id != current_user.id:
        flash('You can only delete your own reports.', 'danger')
        return redirect(url_for('reports.saved'))
    
    db.session.delete(report)
    db.session.commit()
    flash('Report deleted.', 'success')
    return redirect(url_for('reports.saved'))


# ============================================================================
# Export Endpoints
# ============================================================================

@reports_bp.route('/export/<report_type>/<format>')
@login_required
@role_required('admin')
def export(report_type, format):
    """Export a report to the specified format."""
    # Parse date range
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Generate data based on report type
    if report_type == 'revenue':
        data = calculate_daily_revenue(start_date, end_date)
        headers = ['date', 'revenue']
        filename_base = f'revenue_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}'
    elif report_type == 'products':
        limit = request.args.get('limit', 50, type=int)
        data = calculate_product_performance(start_date, end_date, limit=limit)
        headers = ['product_name', 'units_sold', 'total_revenue', 'order_count', 'avg_order_value']
        filename_base = f'products_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}'
    elif report_type == 'customers':
        limit = request.args.get('limit', 100, type=int)
        data = calculate_customer_clv(limit=limit)
        headers = ['email', 'username', 'order_count', 'total_spent', 'avg_order_value', 'tenure_days']
        filename_base = 'customers_clv_report'
    elif report_type == 'tax':
        tax_data = calculate_tax_report(start_date, end_date)
        # Flatten tax data for export
        data = []
        for state, stats in tax_data.get('by_state', {}).items():
            data.append({
                'state': state,
                'orders': stats['orders'],
                'revenue': stats['revenue'],
                'tax': stats['tax']
            })
        headers = ['state', 'orders', 'revenue', 'tax']
        filename_base = f'tax_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}'
    else:
        flash('Unknown report type.', 'danger')
        return redirect(url_for('reports.index'))
    
    # Generate export
    if format == 'csv':
        output = export_to_csv(data, headers)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename_base}.csv'}
        )
    elif format == 'xlsx':
        file_path = export_to_excel(data, headers, f'{filename_base}.xlsx')
        if file_path and os.path.exists(file_path):
            return send_file(
                file_path,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'{filename_base}.xlsx'
            )
        else:
            flash('Excel export failed. openpyxl may not be installed.', 'warning')
            return redirect(request.referrer or url_for('reports.index'))
    else:
        flash('Unsupported export format.', 'danger')
        return redirect(url_for('reports.index'))


# ============================================================================
# Report Builder (Simplified)
# ============================================================================

@reports_bp.route('/builder')
@login_required
@role_required('admin')
def builder():
    """Report builder interface."""
    report_types = [
        {'value': 'revenue', 'label': 'Revenue Report'},
        {'value': 'products', 'label': 'Product Performance'},
        {'value': 'customers', 'label': 'Customer Analysis'},
        {'value': 'traffic', 'label': 'Traffic Report'},
        {'value': 'tax', 'label': 'Tax Report'}
    ]
    
    return render_template('admin/reports/builder/index.html',
        report_types=report_types,
        presets=get_date_range_presets()
    )


@reports_bp.route('/builder/preview', methods=['POST'])
@login_required
@role_required('admin')
def builder_preview():
    """Preview report with current configuration."""
    report_type = request.form.get('report_type')
    days = int(request.form.get('days', 30))
    limit = int(request.form.get('limit', 100))
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    if report_type == 'revenue':
        data = calculate_revenue_metrics(start_date, end_date)
    elif report_type == 'products':
        data = {'products': calculate_product_performance(start_date, end_date, limit=limit)}
    elif report_type == 'customers':
        data = {'customers': calculate_customer_clv(limit=limit)}
    elif report_type == 'tax':
        data = calculate_tax_report(start_date, end_date)
    else:
        data = {'error': 'Unknown report type'}
    
    return jsonify(data)


# ============================================================================
# API Endpoints
# ============================================================================

@reports_bp.route('/api/revenue')
@login_required
@role_required('admin')
def api_revenue():
    """API: Revenue data for charts."""
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    daily_data = calculate_daily_revenue(start_date, end_date)
    
    return jsonify({
        'labels': [d['date'] for d in daily_data],
        'values': [d['revenue'] for d in daily_data]
    })


@reports_bp.route('/api/products')
@login_required
@role_required('admin')
def api_products():
    """API: Product performance data."""
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 10, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    products_data = calculate_product_performance(start_date, end_date, limit=limit)
    
    return jsonify({
        'labels': [p['product_name'] for p in products_data],
        'revenue': [p['total_revenue'] for p in products_data],
        'units': [p['units_sold'] for p in products_data]
    })
