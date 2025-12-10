"""
Phase 15: Email Marketing Admin Routes

Admin interface for email marketing platform:
- Template management (CRUD)
- Campaign management
- Audience/segment builder
- Drip sequence management
- Campaign analytics
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

from app.database import db
from app.models import (
    EmailTemplate, EmailCampaign, EmailSend, Audience, AudienceMember,
    DripSequence, SequenceEnrollment, User, Task, EmailSuppressionList
)
from app.modules.decorators import role_required
from app.modules.email_marketing import (
    calculate_audience_count, calculate_campaign_stats, 
    get_audience_members, generate_tracking_token
)

email_admin_bp = Blueprint('email_admin', __name__, url_prefix='/admin/email')


# ============================================================================
# Email Templates
# ============================================================================

@email_admin_bp.route('/templates')
@login_required
@role_required('admin')
def templates():
    """List all email templates."""
    from flask_wtf.csrf import generate_csrf
    
    template_type = request.args.get('type', '')
    
    query = EmailTemplate.query
    
    if template_type:
        query = query.filter_by(template_type=template_type)
    
    templates = query.order_by(EmailTemplate.updated_at.desc()).all()
    
    # Get template types for filter
    template_types = db.session.query(EmailTemplate.template_type).distinct().all()
    template_types = [t[0] for t in template_types if t[0]]
    
    # Serialize templates for EmailTemplateCards React component
    templates_json = json.dumps({
        'templates': [{
            'id': t.id,
            'name': t.name,
            'subject': t.subject or '',
            'body': (t.body or t.body_html or '')[:500],  # Truncate for preview
            'template_type': t.template_type or 'general',
            'is_active': t.is_active
        } for t in templates],
        'csrfToken': generate_csrf(),
        'deleteUrlPattern': url_for('email_admin.delete_template', id=0).replace('0', '__ID__'),
        'editUrlPattern': url_for('email_admin.edit_template', id=0).replace('0', '__ID__')
    })
    
    return render_template('admin/email/templates/index.html',
                          templates=templates,
                          templates_json=templates_json,
                          template_types=template_types,
                          current_type=template_type)


@email_admin_bp.route('/templates/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def new_template():
    """Create a new email template."""
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        body_html = request.form.get('body_html', '')
        body_text = request.form.get('body_text', '')
        body = request.form.get('body', '')  # Legacy field
        template_type = request.form.get('template_type', 'general')
        category = request.form.get('category', '')
        
        # Parse variables schema
        variables_json = request.form.get('variables_schema', '{}')
        try:
            variables_schema = json.loads(variables_json)
        except json.JSONDecodeError:
            variables_schema = {}
        
        template = EmailTemplate(
            name=name,
            subject=subject,
            body=body or body_html,  # Use body_html as body if body not provided
            body_html=body_html,
            body_text=body_text,
            template_type=template_type,
            category=category if category else None,
            variables_schema=variables_schema,
            created_by_id=current_user.id,
            is_active=True
        )
        
        db.session.add(template)
        db.session.commit()
        
        flash(f'Template "{name}" created successfully.', 'success')
        return redirect(url_for('email_admin.templates'))
    
    return render_template('admin/email/templates/form.html',
                          template=None,
                          action='Create')


@email_admin_bp.route('/templates/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_template(id):
    """Edit an email template."""
    template = EmailTemplate.query.get_or_404(id)
    
    if request.method == 'POST':
        template.name = request.form.get('name')
        template.subject = request.form.get('subject')
        template.body_html = request.form.get('body_html', '')
        template.body_text = request.form.get('body_text', '')
        template.body = request.form.get('body', template.body_html)
        template.template_type = request.form.get('template_type', 'general')
        template.category = request.form.get('category') or None
        template.is_active = request.form.get('is_active') == 'on'
        
        # Parse variables schema
        variables_json = request.form.get('variables_schema', '{}')
        try:
            template.variables_schema = json.loads(variables_json)
        except json.JSONDecodeError:
            pass
        
        db.session.commit()
        
        flash(f'Template "{template.name}" updated successfully.', 'success')
        return redirect(url_for('email_admin.templates'))
    
    return render_template('admin/email/templates/form.html',
                          template=template,
                          action='Edit')


@email_admin_bp.route('/templates/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_template(id):
    """Delete an email template."""
    template = EmailTemplate.query.get_or_404(id)
    
    # Check if template is used by any campaigns
    campaigns_using = EmailCampaign.query.filter_by(template_id=id).count()
    if campaigns_using > 0:
        flash(f'Cannot delete template: used by {campaigns_using} campaign(s).', 'error')
        return redirect(url_for('email_admin.templates'))
    
    db.session.delete(template)
    db.session.commit()
    
    flash('Template deleted successfully.', 'success')
    return redirect(url_for('email_admin.templates'))


@email_admin_bp.route('/templates/<int:id>/preview')
@login_required
@role_required('admin')
def preview_template(id):
    """Preview an email template with sample data."""
    template = EmailTemplate.query.get_or_404(id)
    
    # Sample context for preview
    sample_context = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'company_name': 'Verso Industries',
        'unsubscribe_url': '#unsubscribe'
    }
    
    # Add schema defaults
    for var_name, var_config in (template.variables_schema or {}).items():
        if var_name not in sample_context:
            sample_context[var_name] = var_config.get('default', f'[{var_name}]')
    
    subject, html, text = template.render_full(sample_context)
    
    return render_template('admin/email/templates/preview.html',
                          template=template,
                          subject=subject,
                          html_content=html,
                          text_content=text,
                          context=sample_context)


@email_admin_bp.route('/templates/<int:id>/test', methods=['POST'])
@login_required
@role_required('admin')
def test_template(id):
    """Send a test email with this template."""
    template = EmailTemplate.query.get_or_404(id)
    
    test_email = request.form.get('test_email', current_user.email)
    
    # Create a test send task
    task = Task(
        name='send_test_email',
        payload={
            'template_id': id,
            'recipient_email': test_email,
            'context': {
                'first_name': current_user.username,
                'email': test_email
            }
        }
    )
    db.session.add(task)
    db.session.commit()
    
    flash(f'Test email queued for {test_email}.', 'success')
    return redirect(url_for('email_admin.preview_template', id=id))


# ============================================================================
# Email Campaigns
# ============================================================================

@email_admin_bp.route('/campaigns')
@login_required
@role_required('admin')
def campaigns():
    """List all email campaigns."""
    from flask_wtf.csrf import generate_csrf
    
    status = request.args.get('status', '')
    
    query = EmailCampaign.query
    
    if status:
        query = query.filter_by(status=status)
    
    campaigns = query.order_by(EmailCampaign.created_at.desc()).all()
    
    csrf_token = generate_csrf()
    status_colors = {
        'draft': 'secondary',
        'scheduled': 'info', 
        'sending': 'warning',
        'sent': 'success',
        'paused': 'danger',
        'cancelled': 'dark'
    }
    
    # Serialize for AdminDataTable
    campaigns_json = json.dumps([{
        'id': c.id,
        'name': f'<a href="{url_for("email_admin.campaign_stats", id=c.id)}" class="fw-bold">{c.name}</a>',
        'template': f'<small>{c.template.name}</small>' if c.template else '<span class="text-muted">-</span>',
        'audience': f'<span class="badge bg-secondary">{c.audience.name}</span>' if c.audience else '<span class="text-muted">-</span>',
        'status': f'<span class="badge bg-{status_colors.get(c.status, "secondary")}">{c.status.title()}</span>',
        'sent': c.sent_count,
        'opens': f'{c.unique_open_count}' + (f' <small class="text-muted">({c.open_rate()}%)</small>' if c.sent_count > 0 else ''),
        'clicks': f'{c.unique_click_count}' + (f' <small class="text-muted">({c.click_rate()}%)</small>' if c.sent_count > 0 else ''),
        'created': c.created_at.strftime('%m/%d/%y') if c.created_at else '-',
        'actions': _render_campaign_actions(c, csrf_token)
    } for c in campaigns])
    
    columns_json = json.dumps([
        {'accessorKey': 'name', 'header': 'Campaign', 'html': True},
        {'accessorKey': 'template', 'header': 'Template', 'html': True},
        {'accessorKey': 'audience', 'header': 'Audience', 'html': True},
        {'accessorKey': 'status', 'header': 'Status', 'html': True},
        {'accessorKey': 'sent', 'header': 'Sent', 'sortable': True},
        {'accessorKey': 'opens', 'header': 'Opens', 'html': True},
        {'accessorKey': 'clicks', 'header': 'Clicks', 'html': True},
        {'accessorKey': 'created', 'header': 'Created'},
        {'accessorKey': 'actions', 'header': 'Actions', 'html': True, 'sortable': False}
    ])
    
    return render_template('admin/email/campaigns/index.html',
                          campaigns=campaigns,
                          campaigns_json=campaigns_json,
                          columns_json=columns_json,
                          current_status=status)


def _render_campaign_actions(campaign, csrf_token):
    """Render HTML action buttons for a campaign."""
    buttons = ['<div class="btn-group btn-group-sm">']
    
    # Send button for draft/scheduled/paused
    if campaign.status in ['draft', 'scheduled', 'paused']:
        buttons.append(f'''
            <form method="POST" action="{url_for('email_admin.send_campaign', id=campaign.id)}" 
                  class="d-inline" onsubmit="return confirm('Send this campaign now?');">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <button type="submit" class="btn btn-success" title="Send Now">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </form>
        ''')
    
    # Pause button for sending
    if campaign.status == 'sending':
        buttons.append(f'''
            <form method="POST" action="{url_for('email_admin.pause_campaign', id=campaign.id)}" class="d-inline">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <button type="submit" class="btn btn-warning" title="Pause">
                    <i class="fas fa-pause"></i>
                </button>
            </form>
        ''')
    
    # Stats button
    buttons.append(f'''
        <a href="{url_for('email_admin.campaign_stats', id=campaign.id)}" 
           class="btn btn-outline-primary" title="Stats">
            <i class="fas fa-chart-bar"></i>
        </a>
    ''')
    
    # Edit button for draft/scheduled
    if campaign.status in ['draft', 'scheduled']:
        buttons.append(f'''
            <a href="{url_for('email_admin.edit_campaign', id=campaign.id)}" 
               class="btn btn-outline-secondary" title="Edit">
                <i class="fas fa-edit"></i>
            </a>
        ''')
    
    buttons.append('</div>')
    return ''.join(buttons)


@email_admin_bp.route('/campaigns/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def new_campaign():
    """Create a new email campaign."""
    if request.method == 'POST':
        name = request.form.get('name')
        template_id = request.form.get('template_id', type=int)
        audience_id = request.form.get('audience_id', type=int) or None
        subject_line_a = request.form.get('subject_line_a', '')
        subject_line_b = request.form.get('subject_line_b', '')
        ab_test_percentage = request.form.get('ab_test_percentage', 0, type=int)
        
        # Parse scheduled time
        scheduled_str = request.form.get('scheduled_at', '')
        scheduled_at = None
        if scheduled_str:
            try:
                scheduled_at = datetime.fromisoformat(scheduled_str)
            except ValueError:
                pass
        
        campaign = EmailCampaign(
            name=name,
            template_id=template_id,
            audience_id=audience_id,
            subject_line_a=subject_line_a if subject_line_a else None,
            subject_line_b=subject_line_b if subject_line_b else None,
            ab_test_percentage=ab_test_percentage,
            scheduled_at=scheduled_at,
            status='scheduled' if scheduled_at else 'draft',
            created_by_id=current_user.id
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        flash(f'Campaign "{name}" created successfully.', 'success')
        return redirect(url_for('email_admin.campaigns'))
    
    templates = EmailTemplate.query.filter_by(is_active=True).all()
    audiences = Audience.query.all()
    
    return render_template('admin/email/campaigns/form.html',
                          campaign=None,
                          templates=templates,
                          audiences=audiences,
                          action='Create')


@email_admin_bp.route('/campaigns/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_campaign(id):
    """Edit an email campaign."""
    campaign = EmailCampaign.query.get_or_404(id)
    
    # Can only edit draft or scheduled campaigns
    if campaign.status not in ['draft', 'scheduled']:
        flash('Cannot edit a campaign that is sending or sent.', 'error')
        return redirect(url_for('email_admin.campaigns'))
    
    if request.method == 'POST':
        campaign.name = request.form.get('name')
        campaign.template_id = request.form.get('template_id', type=int)
        campaign.audience_id = request.form.get('audience_id', type=int) or None
        campaign.subject_line_a = request.form.get('subject_line_a') or None
        campaign.subject_line_b = request.form.get('subject_line_b') or None
        campaign.ab_test_percentage = request.form.get('ab_test_percentage', 0, type=int)
        
        # Parse scheduled time
        scheduled_str = request.form.get('scheduled_at', '')
        if scheduled_str:
            try:
                campaign.scheduled_at = datetime.fromisoformat(scheduled_str)
                campaign.status = 'scheduled'
            except ValueError:
                pass
        else:
            campaign.scheduled_at = None
            campaign.status = 'draft'
        
        db.session.commit()
        
        flash(f'Campaign "{campaign.name}" updated.', 'success')
        return redirect(url_for('email_admin.campaigns'))
    
    templates = EmailTemplate.query.filter_by(is_active=True).all()
    audiences = Audience.query.all()
    
    return render_template('admin/email/campaigns/form.html',
                          campaign=campaign,
                          templates=templates,
                          audiences=audiences,
                          action='Edit')


@email_admin_bp.route('/campaigns/<int:id>/send', methods=['POST'])
@login_required
@role_required('admin')
def send_campaign(id):
    """Queue a campaign for immediate sending."""
    campaign = EmailCampaign.query.get_or_404(id)
    
    if campaign.status not in ['draft', 'scheduled', 'paused']:
        flash('Campaign cannot be sent in its current state.', 'error')
        return redirect(url_for('email_admin.campaigns'))
    
    # Create task to send campaign
    task = Task(
        name='send_email_campaign',
        payload={'campaign_id': id},
        priority=5  # Higher priority for user-initiated sends
    )
    db.session.add(task)
    
    campaign.status = 'sending'
    campaign.sent_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Campaign "{campaign.name}" is now being sent.', 'success')
    return redirect(url_for('email_admin.campaign_stats', id=id))


@email_admin_bp.route('/campaigns/<int:id>/pause', methods=['POST'])
@login_required
@role_required('admin')
def pause_campaign(id):
    """Pause a sending campaign."""
    campaign = EmailCampaign.query.get_or_404(id)
    
    if campaign.status != 'sending':
        flash('Only sending campaigns can be paused.', 'error')
        return redirect(url_for('email_admin.campaigns'))
    
    campaign.status = 'paused'
    db.session.commit()
    
    flash(f'Campaign "{campaign.name}" has been paused.', 'success')
    return redirect(url_for('email_admin.campaigns'))


@email_admin_bp.route('/campaigns/<int:id>/stats')
@login_required
@role_required('admin')
def campaign_stats(id):
    """View campaign analytics."""
    campaign = EmailCampaign.query.get_or_404(id)
    
    # Calculate stats
    stats = calculate_campaign_stats(campaign)
    
    # Get recent sends for detail view
    recent_sends = EmailSend.query.filter_by(campaign_id=id)\
        .order_by(EmailSend.sent_at.desc())\
        .limit(100).all()
    
    return render_template('admin/email/campaigns/stats.html',
                          campaign=campaign,
                          stats=stats,
                          recent_sends=recent_sends)


@email_admin_bp.route('/campaigns/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_campaign(id):
    """Delete a campaign."""
    campaign = EmailCampaign.query.get_or_404(id)
    
    if campaign.status in ['sending', 'sent']:
        flash('Cannot delete a campaign that has been sent.', 'error')
        return redirect(url_for('email_admin.campaigns'))
    
    db.session.delete(campaign)
    db.session.commit()
    
    flash('Campaign deleted.', 'success')
    return redirect(url_for('email_admin.campaigns'))


# ============================================================================
# Audience Segments
# ============================================================================

@email_admin_bp.route('/segments')
@login_required
@role_required('admin')
def segments():
    """List all audience segments."""
    audiences = Audience.query.order_by(Audience.name).all()
    
    return render_template('admin/email/segments/index.html',
                          audiences=audiences)


@email_admin_bp.route('/segments/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def new_segment():
    """Create a new audience segment."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        is_dynamic = request.form.get('is_dynamic') == 'on'
        
        # Parse filter rules
        filter_rules_json = request.form.get('filter_rules', '[]')
        try:
            filter_rules = json.loads(filter_rules_json)
        except json.JSONDecodeError:
            filter_rules = []
        
        audience = Audience(
            name=name,
            description=description,
            is_dynamic=is_dynamic,
            filter_rules=filter_rules,
            created_by_id=current_user.id
        )
        
        db.session.add(audience)
        db.session.commit()
        
        # Calculate initial count
        calculate_audience_count(audience)
        
        flash(f'Segment "{name}" created with {audience.member_count} members.', 'success')
        return redirect(url_for('email_admin.segments'))
    
    # Available fields for filtering
    filter_fields = [
        {'name': 'created_at', 'label': 'Registration Date', 'type': 'date'},
        {'name': 'email', 'label': 'Email', 'type': 'string'},
        {'name': 'username', 'label': 'Username', 'type': 'string'},
        {'name': 'department', 'label': 'Department', 'type': 'string'},
        {'name': 'job_title', 'label': 'Job Title', 'type': 'string'},
    ]
    
    return render_template('admin/email/segments/form.html',
                          audience=None,
                          filter_fields=filter_fields,
                          action='Create')


@email_admin_bp.route('/segments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_segment(id):
    """Edit an audience segment."""
    audience = Audience.query.get_or_404(id)
    
    if request.method == 'POST':
        audience.name = request.form.get('name')
        audience.description = request.form.get('description', '')
        audience.is_dynamic = request.form.get('is_dynamic') == 'on'
        
        # Parse filter rules
        filter_rules_json = request.form.get('filter_rules', '[]')
        try:
            audience.filter_rules = json.loads(filter_rules_json)
        except json.JSONDecodeError:
            pass
        
        db.session.commit()
        
        # Recalculate count
        calculate_audience_count(audience)
        
        flash(f'Segment "{audience.name}" updated.', 'success')
        return redirect(url_for('email_admin.segments'))
    
    filter_fields = [
        {'name': 'created_at', 'label': 'Registration Date', 'type': 'date'},
        {'name': 'email', 'label': 'Email', 'type': 'string'},
        {'name': 'username', 'label': 'Username', 'type': 'string'},
        {'name': 'department', 'label': 'Department', 'type': 'string'},
        {'name': 'job_title', 'label': 'Job Title', 'type': 'string'},
    ]
    
    return render_template('admin/email/segments/form.html',
                          audience=audience,
                          filter_fields=filter_fields,
                          action='Edit')


@email_admin_bp.route('/segments/<int:id>/preview')
@login_required
@role_required('admin')
def preview_segment(id):
    """Preview members matching a segment."""
    audience = Audience.query.get_or_404(id)
    
    # Get members (limit to 100 for preview)
    members = get_audience_members(audience)[:100]
    
    return render_template('admin/email/segments/preview.html',
                          audience=audience,
                          members=members,
                          total_count=audience.member_count)


@email_admin_bp.route('/segments/<int:id>/refresh', methods=['POST'])
@login_required
@role_required('admin')
def refresh_segment(id):
    """Refresh audience count."""
    audience = Audience.query.get_or_404(id)
    
    count = calculate_audience_count(audience)
    
    flash(f'Segment refreshed: {count} members.', 'success')
    return redirect(url_for('email_admin.segments'))


@email_admin_bp.route('/segments/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_segment(id):
    """Delete an audience segment."""
    audience = Audience.query.get_or_404(id)
    
    # Check if used by campaigns
    campaigns_using = EmailCampaign.query.filter_by(audience_id=id).count()
    if campaigns_using > 0:
        flash(f'Cannot delete: used by {campaigns_using} campaign(s).', 'error')
        return redirect(url_for('email_admin.segments'))
    
    db.session.delete(audience)
    db.session.commit()
    
    flash('Segment deleted.', 'success')
    return redirect(url_for('email_admin.segments'))


# ============================================================================
# Drip Sequences
# ============================================================================

@email_admin_bp.route('/sequences')
@login_required
@role_required('admin')
def sequences():
    """List all drip sequences."""
    from app.forms import CSRFTokenForm
    sequences = DripSequence.query.order_by(DripSequence.name).all()
    form = CSRFTokenForm()
    
    # Serialize for AdminDataTable
    sequences_json = json.dumps([{
        'id': s.id,
        'name': f'<strong>{s.name}</strong>' + (f'<br><small class="text-muted">{s.description[:50]}...</small>' if s.description else ''),
        'trigger': f'<span class="badge bg-info">{s.trigger_event.replace("_", " ").title()}</span>',
        'steps': f'{len(s.steps_config) if s.steps_config else 0} steps',
        'status': '<span class="badge bg-success">Active</span>' if s.is_active else '<span class="badge bg-secondary">Inactive</span>',
        'actions': f'''<div class="btn-group btn-group-sm"><form method="POST" action="{url_for('email_admin.toggle_sequence', id=s.id)}" class="d-inline"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}"><button type="submit" class="btn btn-{'warning' if s.is_active else 'success'}" title="{'Deactivate' if s.is_active else 'Activate'}"><i class="fas fa-{'pause' if s.is_active else 'play'}"></i></button></form><a href="{url_for('email_admin.edit_sequence', id=s.id)}" class="btn btn-outline-secondary" title="Edit"><i class="fas fa-edit"></i></a><form method="POST" action="{url_for('email_admin.delete_sequence', id=s.id)}" onsubmit="return confirm('Delete this sequence?');" class="d-inline"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}"><button type="submit" class="btn btn-outline-danger"><i class="fas fa-trash"></i></button></form></div>'''
    } for s in sequences])
    
    return render_template('admin/email/sequences/index.html',
                          sequences=sequences,
                          sequences_json=sequences_json)


@email_admin_bp.route('/sequences/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def new_sequence():
    """Create a new drip sequence."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        trigger_event = request.form.get('trigger_event', 'manual')
        
        # Parse steps
        steps_json = request.form.get('steps_config', '[]')
        try:
            steps_config = json.loads(steps_json)
        except json.JSONDecodeError:
            steps_config = []
        
        sequence = DripSequence(
            name=name,
            description=description,
            trigger_event=trigger_event,
            steps_config=steps_config,
            is_active=False,  # Start inactive
            created_by_id=current_user.id
        )
        
        db.session.add(sequence)
        db.session.commit()
        
        flash(f'Sequence "{name}" created.', 'success')
        return redirect(url_for('email_admin.sequences'))
    
    templates = EmailTemplate.query.filter_by(is_active=True).all()
    
    trigger_events = [
        {'value': 'manual', 'label': 'Manual Enrollment'},
        {'value': 'user_signup', 'label': 'User Registration'},
        {'value': 'order_placed', 'label': 'Order Placed'},
        {'value': 'form_submit', 'label': 'Form Submission'},
    ]
    
    return render_template('admin/email/sequences/form.html',
                          sequence=None,
                          templates=templates,
                          trigger_events=trigger_events,
                          action='Create')


@email_admin_bp.route('/sequences/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_sequence(id):
    """Edit a drip sequence."""
    sequence = DripSequence.query.get_or_404(id)
    
    if request.method == 'POST':
        sequence.name = request.form.get('name')
        sequence.description = request.form.get('description', '')
        sequence.trigger_event = request.form.get('trigger_event', 'manual')
        
        # Parse steps
        steps_json = request.form.get('steps_config', '[]')
        try:
            sequence.steps_config = json.loads(steps_json)
        except json.JSONDecodeError:
            pass
        
        db.session.commit()
        
        flash(f'Sequence "{sequence.name}" updated.', 'success')
        return redirect(url_for('email_admin.sequences'))
    
    templates = EmailTemplate.query.filter_by(is_active=True).all()
    
    trigger_events = [
        {'value': 'manual', 'label': 'Manual Enrollment'},
        {'value': 'user_signup', 'label': 'User Registration'},
        {'value': 'order_placed', 'label': 'Order Placed'},
        {'value': 'form_submit', 'label': 'Form Submission'},
    ]
    
    return render_template('admin/email/sequences/form.html',
                          sequence=sequence,
                          templates=templates,
                          trigger_events=trigger_events,
                          action='Edit')


@email_admin_bp.route('/sequences/<int:id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_sequence(id):
    """Activate or deactivate a sequence."""
    sequence = DripSequence.query.get_or_404(id)
    
    sequence.is_active = not sequence.is_active
    db.session.commit()
    
    status = 'activated' if sequence.is_active else 'deactivated'
    flash(f'Sequence "{sequence.name}" {status}.', 'success')
    return redirect(url_for('email_admin.sequences'))


@email_admin_bp.route('/sequences/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_sequence(id):
    """Delete a drip sequence."""
    sequence = DripSequence.query.get_or_404(id)
    
    # Check for active enrollments
    active_enrollments = SequenceEnrollment.query.filter_by(
        sequence_id=id,
        status='active'
    ).count()
    
    if active_enrollments > 0:
        flash(f'Cannot delete: {active_enrollments} active enrollment(s).', 'error')
        return redirect(url_for('email_admin.sequences'))
    
    db.session.delete(sequence)
    db.session.commit()
    
    flash('Sequence deleted.', 'success')
    return redirect(url_for('email_admin.sequences'))


# ============================================================================
# Suppression List
# ============================================================================

@email_admin_bp.route('/suppression')
@login_required
@role_required('admin')
def suppression_list():
    """View and manage email suppression list."""
    from flask_wtf.csrf import generate_csrf
    
    reason = request.args.get('reason', '')
    search = request.args.get('search', '')
    
    query = EmailSuppressionList.query
    
    if reason:
        query = query.filter_by(reason=reason)
    
    if search:
        query = query.filter(EmailSuppressionList.email.ilike(f'%{search}%'))
    
    suppressions = query.order_by(EmailSuppressionList.added_at.desc()).all()
    
    csrf_token = generate_csrf()
    reason_colors = {
        'hard_bounce': 'danger',
        'soft_bounce': 'warning', 
        'unsubscribe': 'info',
        'complaint': 'dark',
        'manual': 'secondary'
    }
    
    # Serialize for AdminDataTable
    suppressions_json = json.dumps([{
        'id': s.id,
        'email': s.email,
        'reason': f'<span class="badge bg-{reason_colors.get(s.reason, "secondary")}">{s.reason.replace("_", " ").title()}</span>',
        'source': f'<small class="text-muted">{s.source or "-"}</small>',
        'added': s.added_at.strftime('%Y-%m-%d %H:%M') if s.added_at else '-',
        'actions': f'''
            <form method="POST" action="{url_for('email_admin.remove_suppression', id=s.id)}"
                  onsubmit="return confirm('Remove this email from suppression list? They will be able to receive emails again.');">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <button type="submit" class="btn btn-sm btn-outline-success" title="Remove from list">
                    <i class="fas fa-check"></i>
                </button>
            </form>
        '''
    } for s in suppressions])
    
    columns_json = json.dumps([
        {'accessorKey': 'email', 'header': 'Email'},
        {'accessorKey': 'reason', 'header': 'Reason', 'html': True},
        {'accessorKey': 'source', 'header': 'Source', 'html': True},
        {'accessorKey': 'added', 'header': 'Added'},
        {'accessorKey': 'actions', 'header': 'Actions', 'html': True, 'sortable': False}
    ])
    
    return render_template('admin/email/suppression/index.html',
                          suppressions_json=suppressions_json,
                          columns_json=columns_json,
                          current_reason=reason,
                          search=search)


@email_admin_bp.route('/suppression/add', methods=['POST'])
@login_required
@role_required('admin')
def add_suppression():
    """Manually add email to suppression list."""
    email = request.form.get('email', '').lower().strip()
    reason = request.form.get('reason', 'manual')
    
    if not email:
        flash('Email is required.', 'error')
        return redirect(url_for('email_admin.suppression_list'))
    
    existing = EmailSuppressionList.query.filter_by(email=email).first()
    if existing:
        flash('Email is already on the suppression list.', 'warning')
        return redirect(url_for('email_admin.suppression_list'))
    
    suppression = EmailSuppressionList(
        email=email,
        reason=reason,
        source='manual'
    )
    db.session.add(suppression)
    db.session.commit()
    
    flash(f'{email} added to suppression list.', 'success')
    return redirect(url_for('email_admin.suppression_list'))


@email_admin_bp.route('/suppression/<int:id>/remove', methods=['POST'])
@login_required
@role_required('admin')
def remove_suppression(id):
    """Remove email from suppression list."""
    suppression = EmailSuppressionList.query.get_or_404(id)
    
    email = suppression.email
    db.session.delete(suppression)
    db.session.commit()
    
    flash(f'{email} removed from suppression list.', 'success')
    return redirect(url_for('email_admin.suppression_list'))
