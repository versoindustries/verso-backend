"""
Phase 29: Privacy & Compliance Routes

Public and admin routes for GDPR/CCPA compliance.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_required, current_user
from datetime import datetime

from app.database import db
from app.models import ConsentRecord, DataExportRequest, RetentionPolicy, DataRetentionLog, AuditLog
from app.modules.privacy import cookie_consent, data_exporter, data_anonymizer
from app.modules.retention import retention_manager


privacy_bp = Blueprint('privacy', __name__, url_prefix='/privacy')
compliance_bp = Blueprint('compliance', __name__, url_prefix='/admin/compliance')


def admin_required(f):
    """Decorator to require admin role."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# Public Privacy Routes
# ============================================================================

@privacy_bp.route('/consent')
def consent_page():
    """Cookie consent page/modal."""
    current_consent = cookie_consent.get_consent()
    return render_template('privacy/consent.html', consent=current_consent)


@privacy_bp.route('/consent', methods=['POST'])
def save_consent():
    """Save cookie consent preferences."""
    consent = {
        'necessary': True,  # Always required
        'functional': request.form.get('functional') == 'true',
        'analytics': request.form.get('analytics') == 'true',
        'marketing': request.form.get('marketing') == 'true',
    }
    
    user_id = current_user.id if current_user.is_authenticated else None
    
    response = make_response(redirect(request.referrer or url_for('main.index')))
    cookie_consent.save_consent(consent, response, user_id=user_id)
    
    flash('Cookie preferences saved.', 'success')
    return response


@privacy_bp.route('/consent/accept-all', methods=['POST'])
def accept_all_cookies():
    """Accept all cookies."""
    consent = {t: True for t in cookie_consent.CONSENT_TYPES}
    user_id = current_user.id if current_user.is_authenticated else None
    
    response = make_response(redirect(request.referrer or url_for('main.index')))
    cookie_consent.save_consent(consent, response, user_id=user_id)
    
    return response


@privacy_bp.route('/consent/reject-all', methods=['POST'])
def reject_optional_cookies():
    """Reject all optional cookies."""
    consent = {
        'necessary': True,
        'functional': False,
        'analytics': False,
        'marketing': False,
    }
    user_id = current_user.id if current_user.is_authenticated else None
    
    response = make_response(redirect(request.referrer or url_for('main.index')))
    cookie_consent.save_consent(consent, response, user_id=user_id)
    
    return response


@privacy_bp.route('/data-export')
@login_required
def data_export_page():
    """Page to request data export."""
    # Get existing requests
    requests = DataExportRequest.query.filter_by(
        user_id=current_user.id
    ).order_by(DataExportRequest.requested_at.desc()).limit(10).all()
    
    return render_template('privacy/data_export.html', export_requests=requests)


@privacy_bp.route('/data-export/request', methods=['POST'])
@login_required
def request_data_export():
    """Request a data export."""
    file_format = request.form.get('format', 'json')
    
    try:
        request_id = data_exporter.request_export(current_user.id, file_format)
        flash('Your data export request has been submitted. You will be notified when it is ready.', 'success')
    except Exception as e:
        flash(f'Error requesting export: {str(e)}', 'danger')
    
    return redirect(url_for('privacy.data_export_page'))


@privacy_bp.route('/data-export/<int:request_id>/download')
@login_required
def download_data_export(request_id):
    """Download a data export."""
    import os
    
    file_path = data_exporter.download_export(request_id, current_user.id)
    
    if not file_path or not os.path.exists(file_path):
        flash('Export not found or has expired.', 'danger')
        return redirect(url_for('privacy.data_export_page'))
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(file_path)
    )


@privacy_bp.route('/delete-account')
@login_required
def delete_account_page():
    """Page to request account deletion."""
    preview = data_anonymizer.get_deletion_preview(current_user.id)
    return render_template('privacy/delete_account.html', preview=preview)


@privacy_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account."""
    confirm = request.form.get('confirm')
    hard_delete = request.form.get('hard_delete') == 'true'
    
    if confirm != current_user.email:
        flash('Please type your email to confirm deletion.', 'danger')
        return redirect(url_for('privacy.delete_account_page'))
    
    try:
        # Log the deletion request before deleting
        from flask_login import logout_user
        
        results = data_anonymizer.anonymize_user(current_user.id, hard_delete=hard_delete)
        logout_user()
        
        flash('Your account has been deleted.', 'success')
        return redirect(url_for('main.index'))
        
    except Exception as e:
        flash(f'Error deleting account: {str(e)}', 'danger')
        return redirect(url_for('privacy.delete_account_page'))


@privacy_bp.route('/policy')
def privacy_policy():
    """Privacy policy page."""
    return render_template('privacy/policy.html')


@privacy_bp.route('/consent-history')
@login_required
def consent_history():
    """View consent history."""
    history = cookie_consent.get_consent_history(current_user.id)
    return render_template('privacy/consent_history.html', history=history)


# ============================================================================
# Admin Compliance Routes
# ============================================================================

@compliance_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Compliance dashboard."""
    # Get compliance statistics
    total_consent_records = ConsentRecord.query.count()
    pending_exports = DataExportRequest.query.filter_by(status='pending').count()
    active_policies = RetentionPolicy.query.filter_by(is_active=True).count()
    
    # Recent consent activity
    recent_consents = ConsentRecord.query.order_by(
        ConsentRecord.created_at.desc()
    ).limit(10).all()
    
    # Recent audit logs
    recent_audits = AuditLog.query.order_by(
        AuditLog.timestamp.desc()
    ).limit(10).all()
    
    return render_template('admin/compliance/dashboard.html',
                          total_consents=total_consent_records,
                          pending_exports=pending_exports,
                          active_policies=active_policies,
                          recent_consents=recent_consents,
                          recent_audits=recent_audits)


@compliance_bp.route('/consents')
@login_required
@admin_required
def consent_list():
    """List all consent records."""
    page = request.args.get('page', 1, type=int)
    consent_type = request.args.get('type')
    
    query = ConsentRecord.query.order_by(ConsentRecord.created_at.desc())
    
    if consent_type:
        query = query.filter_by(consent_type=consent_type)
    
    consents = query.paginate(page=page, per_page=50)
    
    return render_template('admin/compliance/consents.html',
                          consents=consents,
                          current_type=consent_type)


@compliance_bp.route('/exports')
@login_required
@admin_required
def export_list():
    """List all data export requests."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    
    query = DataExportRequest.query.order_by(DataExportRequest.requested_at.desc())
    
    if status:
        query = query.filter_by(status=status)
    
    exports = query.paginate(page=page, per_page=50)
    
    return render_template('admin/compliance/exports.html',
                          exports=exports,
                          current_status=status)


@compliance_bp.route('/exports/<int:export_id>/process', methods=['POST'])
@login_required
@admin_required
def process_export(export_id):
    """Manually process a data export request."""
    try:
        data_exporter.process_export(export_id)
        flash('Export processed successfully.', 'success')
    except Exception as e:
        flash(f'Error processing export: {str(e)}', 'danger')
    
    return redirect(url_for('compliance.export_list'))


@compliance_bp.route('/retention')
@login_required
@admin_required
def retention_policies():
    """List retention policies."""
    policies = retention_manager.get_policies(active_only=False)
    return render_template('admin/compliance/retention.html', policies=policies)


@compliance_bp.route('/retention/seed', methods=['POST'])
@login_required
@admin_required
def seed_retention_policies():
    """Seed default retention policies."""
    count = retention_manager.seed_default_policies()
    flash(f'Created {count} retention policies.', 'success')
    return redirect(url_for('compliance.retention_policies'))


@compliance_bp.route('/retention/<int:policy_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_retention_policy(policy_id):
    """Toggle a retention policy on/off."""
    policy = RetentionPolicy.query.get_or_404(policy_id)
    policy.is_active = not policy.is_active
    db.session.commit()
    
    status = 'activated' if policy.is_active else 'deactivated'
    flash(f'Retention policy "{policy.name}" {status}.', 'success')
    return redirect(url_for('compliance.retention_policies'))


@compliance_bp.route('/retention/<int:policy_id>/execute', methods=['POST'])
@login_required
@admin_required
def execute_retention_policy(policy_id):
    """Execute a retention policy manually."""
    try:
        results = retention_manager.execute_policy(policy_id)
        flash(f'Policy executed: {results["records_deleted"]} records deleted, '
              f'{results["records_anonymized"]} anonymized, '
              f'{results["records_archived"]} archived.', 'success')
    except Exception as e:
        flash(f'Error executing policy: {str(e)}', 'danger')
    
    return redirect(url_for('compliance.retention_policies'))


@compliance_bp.route('/retention/run-all', methods=['POST'])
@login_required
@admin_required
def run_all_retention():
    """Run all due retention policies."""
    results = retention_manager.run_all_due_policies()
    
    flash(f'Executed {results["policies_executed"]} policies, '
          f'deleted {results["total_records_deleted"]} records.', 'success')
    
    if results['errors']:
        for error in results['errors']:
            flash(f'Error in {error["policy"]}: {error["error"]}', 'warning')
    
    return redirect(url_for('compliance.retention_policies'))


@compliance_bp.route('/retention/history')
@login_required
@admin_required
def retention_history():
    """View retention execution history."""
    policy_id = request.args.get('policy_id', type=int)
    
    history = retention_manager.get_execution_history(policy_id=policy_id, limit=100)
    policies = RetentionPolicy.query.all()
    
    return render_template('admin/compliance/retention_history.html',
                          history=history,
                          policies=policies,
                          current_policy_id=policy_id)


@compliance_bp.route('/audit')
@login_required
@admin_required
def audit_log():
    """View audit log."""
    page = request.args.get('page', 1, type=int)
    action = request.args.get('action')
    entity_type = request.args.get('entity_type')
    
    query = AuditLog.query.order_by(AuditLog.timestamp.desc())
    
    if action:
        query = query.filter_by(action=action)
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    
    logs = query.paginate(page=page, per_page=100)
    
    # Get filter options
    actions = db.session.query(AuditLog.action).distinct().all()
    entity_types = db.session.query(AuditLog.entity_type).distinct().all()
    
    return render_template('admin/compliance/audit.html',
                          logs=logs,
                          actions=[a[0] for a in actions],
                          entity_types=[e[0] for e in entity_types],
                          current_action=action,
                          current_entity_type=entity_type)


@compliance_bp.route('/audit/export', methods=['POST'])
@login_required
@admin_required
def export_audit_log():
    """Export audit logs."""
    import csv
    from io import StringIO
    from flask import Response
    
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    query = AuditLog.query.order_by(AuditLog.timestamp.desc())
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(AuditLog.timestamp <= datetime.fromisoformat(end_date))
    
    logs = query.all()
    
    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'User', 'Action', 'Entity Type', 'Entity ID', 'Details'])
    
    for log in logs:
        writer.writerow([
            log.timestamp.isoformat() if log.timestamp else '',
            log.user.username if log.user else '',
            log.action,
            log.entity_type,
            log.entity_id,
            log.details,
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=audit_log_{datetime.utcnow().strftime("%Y%m%d")}.csv'}
    )


# ============================================================================
# API Endpoints
# ============================================================================

@privacy_bp.route('/api/consent')
def api_get_consent():
    """Get current consent status (for JavaScript)."""
    return jsonify(cookie_consent.get_consent())


@privacy_bp.route('/api/consent', methods=['POST'])
def api_save_consent():
    """Save consent via API."""
    data = request.get_json()
    
    consent = {
        'necessary': True,
        'functional': data.get('functional', False),
        'analytics': data.get('analytics', False),
        'marketing': data.get('marketing', False),
    }
    
    user_id = current_user.id if current_user.is_authenticated else None
    
    response = make_response(jsonify({'status': 'ok', 'consent': consent}))
    cookie_consent.save_consent(consent, response, user_id=user_id)
    
    return response
