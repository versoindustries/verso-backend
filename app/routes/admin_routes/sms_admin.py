"""
SMS Admin Routes

Admin interface for managing SMS templates and consent tracking.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.database import db
from app.models import SMSTemplate, SMSConsent, User
from app.modules.decorators import role_required
from datetime import datetime

sms_admin_bp = Blueprint('sms_admin', __name__, url_prefix='/admin/sms')


# =============================================================================
# SMS Templates
# =============================================================================

@sms_admin_bp.route('/templates')
@login_required
@role_required('admin')
def list_templates():
    """List all SMS templates."""
    templates = SMSTemplate.query.order_by(SMSTemplate.created_at.desc()).all()
    return render_template('admin/sms/templates/index.html', templates=templates)


@sms_admin_bp.route('/templates/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_template():
    """Create a new SMS template."""
    if request.method == 'POST':
        name = request.form.get('name')
        body = request.form.get('body')
        
        # Parse variables from body ({{variable_name}} format)
        import re
        variables = re.findall(r'\{\{(\w+)\}\}', body)
        variables_schema = {v: {'type': 'string', 'default': ''} for v in variables}
        
        template = SMSTemplate(
            name=name,
            body=body,
            variables_schema=variables_schema,
            is_active=request.form.get('is_active') == 'on',
            created_by_id=current_user.id
        )
        
        # Calculate segment count
        template.calculate_segments()
        
        db.session.add(template)
        db.session.commit()
        
        flash(f'Template "{name}" created ({template.segment_count} segment(s)).', 'success')
        return redirect(url_for('sms_admin.list_templates'))
    
    return render_template('admin/sms/templates/form.html', template=None)


@sms_admin_bp.route('/templates/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_template(id):
    """Edit an SMS template."""
    template = SMSTemplate.query.get_or_404(id)
    
    if request.method == 'POST':
        template.name = request.form.get('name')
        template.body = request.form.get('body')
        template.is_active = request.form.get('is_active') == 'on'
        
        # Re-parse variables
        import re
        variables = re.findall(r'\{\{(\w+)\}\}', template.body)
        template.variables_schema = {v: {'type': 'string', 'default': ''} for v in variables}
        
        # Recalculate segments
        template.calculate_segments()
        
        db.session.commit()
        flash('Template updated.', 'success')
        return redirect(url_for('sms_admin.list_templates'))
    
    return render_template('admin/sms/templates/form.html', template=template)


@sms_admin_bp.route('/templates/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_template(id):
    """Delete an SMS template."""
    template = SMSTemplate.query.get_or_404(id)
    name = template.name
    db.session.delete(template)
    db.session.commit()
    flash(f'Template "{name}" deleted.', 'success')
    return redirect(url_for('sms_admin.list_templates'))


@sms_admin_bp.route('/templates/<int:id>/preview', methods=['POST'])
@login_required
@role_required('admin')
def preview_template(id):
    """Preview rendered template with test data."""
    template = SMSTemplate.query.get_or_404(id)
    
    data = request.get_json() or {}
    rendered = template.render(data)
    
    return jsonify({
        'rendered': rendered,
        'character_count': len(rendered),
        'segment_count': (len(rendered) + 152) // 153 if len(rendered) > 160 else 1
    })


# =============================================================================
# SMS Consent Management
# =============================================================================

@sms_admin_bp.route('/consents')
@login_required
@role_required('admin')
def list_consents():
    """List all SMS consents with filtering."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = SMSConsent.query
    
    # Filter by status
    if status == 'active':
        query = query.filter(SMSConsent.consented == True, SMSConsent.revoked_at == None)
    elif status == 'revoked':
        query = query.filter(SMSConsent.revoked_at != None)
    
    # Search by phone number
    if search:
        query = query.filter(SMSConsent.phone_number.ilike(f'%{search}%'))
    
    # Order by newest first
    query = query.order_by(SMSConsent.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=50, error_out=False)
    
    # Stats
    total_active = SMSConsent.query.filter(SMSConsent.consented == True, SMSConsent.revoked_at == None).count()
    total_revoked = SMSConsent.query.filter(SMSConsent.revoked_at != None).count()
    
    return render_template('admin/sms/consents/index.html',
                          consents=pagination.items,
                          pagination=pagination,
                          status=status,
                          search=search,
                          total_active=total_active,
                          total_revoked=total_revoked)


@sms_admin_bp.route('/consents/<int:id>')
@login_required
@role_required('admin')
def consent_detail(id):
    """View consent details."""
    consent = SMSConsent.query.get_or_404(id)
    return render_template('admin/sms/consents/detail.html', consent=consent)


@sms_admin_bp.route('/consents/<int:id>/revoke', methods=['POST'])
@login_required
@role_required('admin')
def revoke_consent(id):
    """Revoke SMS consent."""
    consent = SMSConsent.query.get_or_404(id)
    consent.revoke()
    db.session.commit()
    
    flash(f'Consent for {consent.phone_number} revoked.', 'success')
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'success': True})
    
    return redirect(url_for('sms_admin.list_consents'))


@sms_admin_bp.route('/consents/export')
@login_required
@role_required('admin')
def export_consents():
    """Export active consents as CSV for compliance."""
    import csv
    from io import StringIO
    from flask import Response
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Phone Number', 'Consented At', 'Source', 'Categories', 'Status'])
    
    consents = SMSConsent.query.filter(SMSConsent.consented == True).all()
    for consent in consents:
        status = 'Active' if consent.is_valid() else 'Revoked'
        categories = ', '.join(consent.categories or [])
        writer.writerow([
            consent.phone_number,
            consent.consented_at.isoformat() if consent.consented_at else '',
            consent.consent_source or '',
            categories,
            status
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=sms_consents.csv'}
    )
