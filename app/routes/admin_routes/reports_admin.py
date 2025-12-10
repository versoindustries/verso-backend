"""
Reports Admin Routes

Admin interface for generating and exporting reports.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from app.database import db
from app.models import ReportExport, Order, User, Appointment
from app.modules.decorators import role_required
from datetime import datetime, timedelta
import csv
from io import StringIO

reports_admin_bp = Blueprint('reports_admin', __name__, url_prefix='/admin/reports')


# =============================================================================
# Report Types Configuration
# =============================================================================

REPORT_TYPES = {
    'sales': {
        'name': 'Sales Report',
        'description': 'Revenue, orders, and product performance',
        'model': 'Order',
        'fields': ['id', 'user_id', 'total_amount', 'status', 'created_at']
    },
    'appointments': {
        'name': 'Appointments Report',
        'description': 'Booking and appointment data',
        'model': 'Appointment',
        'fields': ['id', 'user_id', 'service_id', 'scheduled_time', 'status', 'created_at']
    },
    'users': {
        'name': 'Users Report',
        'description': 'User registration and activity',
        'model': 'User',
        'fields': ['id', 'email', 'first_name', 'last_name', 'is_active', 'created_at', 'last_login']
    }
}


# =============================================================================
# Report List and Generation
# =============================================================================

@reports_admin_bp.route('/')
@login_required
@role_required('admin')
def list_reports():
    """List saved reports and available report types."""
    saved_reports = ReportExport.query.order_by(ReportExport.created_at.desc()).limit(20).all()
    return render_template('admin/reports/index.html', 
                          saved_reports=saved_reports,
                          report_types=REPORT_TYPES)


@reports_admin_bp.route('/generate', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def generate_report():
    """Generate a new report."""
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        output_format = request.form.get('format', 'csv')
        
        if report_type not in REPORT_TYPES:
            flash('Invalid report type.', 'danger')
            return redirect(url_for('reports_admin.list_reports'))
        
        # Parse dates
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.now() - timedelta(days=30)
            end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('reports_admin.generate_report'))
        
        # Generate report data
        data = generate_report_data(report_type, start, end)
        
        # Create ReportExport record
        config = REPORT_TYPES[report_type]
        report = ReportExport(
            name=f"{config['name']} - {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            report_type=report_type,
            parameters={'start_date': start.isoformat(), 'end_date': end.isoformat()},
            row_count=len(data),
            created_by_id=current_user.id
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Return as download or redirect
        if output_format == 'csv':
            return create_csv_response(data, config['fields'], report.name)
        else:
            flash(f'Report generated with {len(data)} rows.', 'success')
            return redirect(url_for('reports_admin.view_report', id=report.id))
    
    return render_template('admin/reports/generate.html', report_types=REPORT_TYPES)


@reports_admin_bp.route('/<int:id>')
@login_required
@role_required('admin')
def view_report(id):
    """View a saved report."""
    report = ReportExport.query.get_or_404(id)
    
    # Regenerate data for display
    params = report.parameters or {}
    start = datetime.fromisoformat(params.get('start_date', (datetime.now() - timedelta(days=30)).isoformat()))
    end = datetime.fromisoformat(params.get('end_date', datetime.now().isoformat()))
    
    data = generate_report_data(report.report_type, start, end)
    config = REPORT_TYPES.get(report.report_type, {})
    
    return render_template('admin/reports/view.html', 
                          report=report, 
                          data=data[:100],  # Limit preview
                          fields=config.get('fields', []),
                          total_rows=len(data))


@reports_admin_bp.route('/<int:id>/download')
@login_required
@role_required('admin')
def download_report(id):
    """Download a report as CSV."""
    report = ReportExport.query.get_or_404(id)
    
    params = report.parameters or {}
    start = datetime.fromisoformat(params.get('start_date', (datetime.now() - timedelta(days=30)).isoformat()))
    end = datetime.fromisoformat(params.get('end_date', datetime.now().isoformat()))
    
    data = generate_report_data(report.report_type, start, end)
    config = REPORT_TYPES.get(report.report_type, {})
    
    return create_csv_response(data, config.get('fields', []), report.name)


@reports_admin_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_report(id):
    """Delete a saved report."""
    report = ReportExport.query.get_or_404(id)
    name = report.name
    db.session.delete(report)
    db.session.commit()
    flash(f'Report "{name}" deleted.', 'success')
    return redirect(url_for('reports_admin.list_reports'))


# =============================================================================
# Helper Functions
# =============================================================================

def generate_report_data(report_type: str, start: datetime, end: datetime) -> list:
    """Generate report data based on type and date range."""
    data = []
    
    if report_type == 'sales':
        orders = Order.query.filter(
            Order.created_at >= start,
            Order.created_at <= end
        ).order_by(Order.created_at.desc()).all()
        
        for order in orders:
            data.append({
                'id': order.id,
                'user_id': order.user_id,
                'total_amount': order.total_amount / 100 if order.total_amount else 0,
                'status': order.status,
                'created_at': order.created_at.isoformat() if order.created_at else ''
            })
    
    elif report_type == 'appointments':
        appointments = Appointment.query.filter(
            Appointment.created_at >= start,
            Appointment.created_at <= end
        ).order_by(Appointment.created_at.desc()).all()
        
        for apt in appointments:
            data.append({
                'id': apt.id,
                'user_id': apt.user_id,
                'service_id': apt.service_id,
                'scheduled_time': apt.scheduled_time.isoformat() if apt.scheduled_time else '',
                'status': apt.status,
                'created_at': apt.created_at.isoformat() if apt.created_at else ''
            })
    
    elif report_type == 'users':
        users = User.query.filter(
            User.created_at >= start,
            User.created_at <= end
        ).order_by(User.created_at.desc()).all()
        
        for user in users:
            data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else '',
                'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else ''
            })
    
    return data


def create_csv_response(data: list, fields: list, filename: str) -> Response:
    """Create a CSV download response."""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(data)
    
    output.seek(0)
    safe_filename = filename.replace(' ', '_').replace('/', '-') + '.csv'
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={safe_filename}'}
    )
