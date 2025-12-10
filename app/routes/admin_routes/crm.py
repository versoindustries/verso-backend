"""
Phase 4: CRM & Lead Management Routes

This module provides comprehensive CRM functionality including:
- Dynamic pipeline stages (replacing hardcoded statuses)
- Lead detail views with timeline
- Notes and activity logging
- Pipeline configuration
- Analytics and reporting
- Email template management
- Automation triggers
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import (
    ContactFormSubmission, Appointment, db, User, Role, Task,
    PipelineStage, LeadNote, LeadActivity, EmailTemplate, 
    LeadScore, LeadScoreRule, FollowUpReminder
)
from app.modules.decorators import role_required
from app.forms import (
    LeadNoteForm, PipelineStageForm, EmailTemplateForm,
    LeadAssignForm, FollowUpReminderForm, SendEmailForm
)
from sqlalchemy import func
from datetime import datetime, timedelta

crm_bp = Blueprint('crm', __name__, url_prefix='/admin/crm')


# =============================================================================
# Helper Functions
# =============================================================================

def get_lead(lead_type, lead_id):
    """Retrieve a lead by type and ID."""
    if lead_type == 'contact':
        return ContactFormSubmission.query.get(lead_id)
    elif lead_type == 'appointment':
        return Appointment.query.get(lead_id)
    return None


def log_activity(lead_type, lead_id, activity_type, description, user_id=None, old_value=None, new_value=None, extra_data=None):
    """Log an activity for a lead."""
    activity = LeadActivity(
        lead_type=lead_type,
        lead_id=lead_id,
        activity_type=activity_type,
        description=description,
        user_id=user_id,
        old_value=old_value,
        new_value=new_value,
        extra_data=extra_data or {}
    )
    db.session.add(activity)
    return activity


def get_pipeline_stages(pipeline_name='default'):
    """Get ordered pipeline stages."""
    stages = PipelineStage.query.filter_by(
        pipeline_name=pipeline_name, 
        is_active=True
    ).order_by(PipelineStage.order).all()
    
    # If no stages exist, create defaults
    if not stages:
        default_stages = [
            {'name': 'New', 'order': 0, 'color': '#17a2b8', 'probability': 10},
            {'name': 'Contacted', 'order': 1, 'color': '#6c757d', 'probability': 25},
            {'name': 'Qualified', 'order': 2, 'color': '#ffc107', 'probability': 50},
            {'name': 'Won', 'order': 3, 'color': '#28a745', 'probability': 100, 'is_won_stage': True},
            {'name': 'Lost', 'order': 4, 'color': '#dc3545', 'probability': 0, 'is_lost_stage': True},
        ]
        for s in default_stages:
            stage = PipelineStage(pipeline_name=pipeline_name, **s)
            db.session.add(stage)
        db.session.commit()
        stages = PipelineStage.query.filter_by(pipeline_name=pipeline_name, is_active=True).order_by(PipelineStage.order).all()
    
    return stages


def format_lead_item(item, lead_type):
    """Format a lead item for display."""
    # Get lead score if exists
    score = LeadScore.query.filter_by(lead_type=lead_type, lead_id=item.id).first()
    
    return {
        'id': item.id,
        'type': lead_type,
        'name': f"{item.first_name} {item.last_name}",
        'email': item.email,
        'phone': item.phone,
        'status': item.status or 'New',
        'notes': item.notes,
        'date': item.submitted_at if lead_type == 'contact' else item.created_at,
        'source': getattr(item, 'source', 'unknown'),
        'score': score.score if score else 0,
        'assigned_to': getattr(item, 'assigned_to', None)
    }


# =============================================================================
# Kanban Board
# =============================================================================

@crm_bp.route('/')
@login_required
@role_required('admin')
def index():
    """Redirect to unified CRM dashboard."""
    return redirect(url_for('crm.dashboard'))


@crm_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    """Unified CRM dashboard with Kanban, Analytics, Settings, and Templates."""
    import json
    from flask_wtf.csrf import generate_csrf
    
    pipeline_name = request.args.get('pipeline', 'default')
    stages = get_pipeline_stages(pipeline_name)
    
    # Fetch all leads for Kanban
    contacts = ContactFormSubmission.query.all()
    appointments = Appointment.query.all()
    
    # Create columns dict from stages
    columns = {stage.name: {'stage': stage, 'leads': []} for stage in stages}
    
    # Place leads in columns
    for c in contacts:
        status = c.status or 'New'
        if status in columns:
            columns[status]['leads'].append(format_lead_item(c, 'contact'))
        else:
            first_stage = stages[0].name if stages else 'New'
            if first_stage in columns:
                columns[first_stage]['leads'].append(format_lead_item(c, 'contact'))
    
    for a in appointments:
        status = a.status or 'New'
        if status in columns:
            columns[status]['leads'].append(format_lead_item(a, 'appointment'))
        else:
            first_stage = stages[0].name if stages else 'New'
            if first_stage in columns:
                columns[first_stage]['leads'].append(format_lead_item(a, 'appointment'))
    
    # Sort items by date desc
    for col in columns.values():
        col['leads'].sort(key=lambda x: x['date'] or datetime.min, reverse=True)
    
    # Serialize Kanban columns for React
    columns_json = {
        stage_name: {
            'stage': {
                'name': col['stage'].name,
                'color': col['stage'].color
            },
            'leads': [
                {
                    'id': lead['id'],
                    'type': lead['type'],
                    'name': lead['name'],
                    'email': lead['email'],
                    'phone': lead['phone'],
                    'date': lead['date'].isoformat() if lead['date'] else None,
                    'source': lead['source'],
                    'score': lead['score']
                }
                for lead in col['leads']
            ]
        }
        for stage_name, col in columns.items()
    }
    
    # Analytics data: Funnel
    funnel_data = []
    for stage in stages:
        contact_count = ContactFormSubmission.query.filter_by(status=stage.name).count()
        appt_count = Appointment.query.filter_by(status=stage.name).count()
        funnel_data.append({
            'stage': stage.name,
            'color': stage.color,
            'count': contact_count + appt_count,
            'probability': stage.probability
        })
    
    # Analytics data: Sources
    source_query = db.session.query(
        ContactFormSubmission.source,
        func.count(ContactFormSubmission.id)
    ).group_by(ContactFormSubmission.source).all()
    
    total_sources = sum(c for _, c in source_query)
    source_data = [
        {
            'source': s or 'Unknown',
            'count': c,
            'percentage': (c / total_sources * 100) if total_sources > 0 else 0
        }
        for s, c in source_query
    ]
    
    # KPI data
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    total_leads = ContactFormSubmission.query.count() + Appointment.query.count()
    new_this_week = ContactFormSubmission.query.filter(
        ContactFormSubmission.submitted_at >= week_ago
    ).count() + Appointment.query.filter(
        Appointment.created_at >= week_ago
    ).count()
    won_this_month = ContactFormSubmission.query.filter(
        ContactFormSubmission.status == 'Won',
        ContactFormSubmission.submitted_at >= month_ago
    ).count() + Appointment.query.filter(
        Appointment.status == 'Won',
        Appointment.created_at >= month_ago
    ).count()
    
    won_total = ContactFormSubmission.query.filter_by(status='Won').count() + \
                Appointment.query.filter_by(status='Won').count()
    conversion_rate = round((won_total / total_leads) * 100, 1) if total_leads > 0 else 0
    
    kpi_data = {
        'totalLeads': total_leads,
        'newThisWeek': new_this_week,
        'wonThisMonth': won_this_month,
        'conversionRate': conversion_rate,
        'trends': {
            'totalLeads': 0,  # TODO: Calculate actual trend
            'newThisWeek': 0,
            'wonThisMonth': 0,
            'conversionRate': 0
        }
    }
    
    # Pipeline stages for settings
    stages_data = [
        {
            'id': s.id,
            'name': s.name,
            'color': s.color,
            'order': s.order,
            'probability': s.probability,
            'isWonStage': s.is_won_stage,
            'isLostStage': s.is_lost_stage,
            'pipelineName': s.pipeline_name
        }
        for s in stages
    ]
    
    # Email templates
    templates = EmailTemplate.query.order_by(EmailTemplate.template_type, EmailTemplate.name).all()
    templates_data = [
        {
            'id': t.id,
            'name': t.name,
            'type': t.template_type,
            'subject': t.subject,
            'body': t.body or '',
            'isActive': t.is_active
        }
        for t in templates
    ]
    
    # Combine all props for React component
    dashboard_props = json.dumps({
        'columns': columns_json,
        'updateStatusUrl': url_for('crm.update_status'),
        'leadDetailUrl': url_for('crm.lead_detail', lead_type='__TYPE__', lead_id=0).replace('/0', '/__ID__'),
        'stages': stages_data,
        'pipelineName': pipeline_name,
        'kpiData': kpi_data,
        'funnelData': funnel_data,
        'sourceData': source_data,
        'templates': templates_data,
        'csrfToken': generate_csrf()
    })
    
    return render_template('admin/crm/dashboard.html', dashboard_props=dashboard_props)

@crm_bp.route('/board')
@login_required
@role_required('admin')
def board():
    """Dynamic Kanban board with pipeline stages from database."""
    import json
    pipeline_name = request.args.get('pipeline', 'default')
    stages = get_pipeline_stages(pipeline_name)
    
    # Fetch all leads
    contacts = ContactFormSubmission.query.all()
    appointments = Appointment.query.all()
    
    # Create columns dict from stages
    columns = {stage.name: {'stage': stage, 'leads': []} for stage in stages}
    
    # Place leads in columns
    for c in contacts:
        status = c.status or 'New'
        if status in columns:
            columns[status]['leads'].append(format_lead_item(c, 'contact'))
        else:
            # If status doesn't match a stage, put in first column
            first_stage = stages[0].name if stages else 'New'
            if first_stage in columns:
                columns[first_stage]['leads'].append(format_lead_item(c, 'contact'))
    
    for a in appointments:
        status = a.status or 'New'
        if status in columns:
            columns[status]['leads'].append(format_lead_item(a, 'appointment'))
        else:
            first_stage = stages[0].name if stages else 'New'
            if first_stage in columns:
                columns[first_stage]['leads'].append(format_lead_item(a, 'appointment'))
    
    # Sort items by date desc
    for col in columns.values():
        col['leads'].sort(key=lambda x: x['date'] or datetime.min, reverse=True)
    
    # Serialize for React component
    columns_json = json.dumps({
        stage_name: {
            'stage': {
                'name': col['stage'].name,
                'color': col['stage'].color
            },
            'leads': [
                {
                    'id': lead['id'],
                    'type': lead['type'],
                    'name': lead['name'],
                    'email': lead['email'],
                    'phone': lead['phone'],
                    'date': lead['date'].isoformat() if lead['date'] else None,
                    'source': lead['source'],
                    'score': lead['score']
                }
                for lead in col['leads']
            ]
        }
        for stage_name, col in columns.items()
    })
    
    return render_template('admin/crm/kanban.html', 
                          columns=columns, 
                          columns_json=columns_json,
                          stages=stages,
                          pipeline_name=pipeline_name,
                          update_status_url=url_for('crm.update_status'),
                          lead_detail_url=url_for('crm.lead_detail', lead_type='__TYPE__', lead_id=0).replace('/0', '/__ID__'))


@crm_bp.route('/update_status', methods=['POST'])
@login_required
@role_required('admin')
def update_status():
    """Update lead status with activity logging and automation triggers."""
    data = request.json
    item_id = data.get('id')
    item_type = data.get('type')
    new_status = data.get('status')
    
    if not all([item_id, item_type, new_status]):
        return jsonify({'error': 'Missing data'}), 400
    
    try:
        item = get_lead(item_type, item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        old_status = item.status
        item.status = new_status
        
        # Log activity
        log_activity(
            lead_type=item_type,
            lead_id=item_id,
            activity_type='status_change',
            description=f"Status changed from {old_status} to {new_status}",
            user_id=current_user.id,
            old_value=old_status,
            new_value=new_status
        )
        
        # Check for automation triggers
        stage = PipelineStage.query.filter_by(name=new_status, is_active=True).first()
        if stage:
            if stage.is_won_stage:
                # Trigger won automation
                trigger_won_automation(item_type, item_id, item)
            elif stage.is_lost_stage:
                # Log lost event
                log_activity(
                    lead_type=item_type,
                    lead_id=item_id,
                    activity_type='lead_lost',
                    description=f"Lead marked as lost",
                    user_id=current_user.id
                )
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


def trigger_won_automation(lead_type, lead_id, item):
    """Trigger automated actions when a lead is won."""
    # Log won event
    log_activity(
        lead_type=lead_type,
        lead_id=lead_id,
        activity_type='lead_won',
        description=f"Lead won! Automation triggered.",
        user_id=current_user.id
    )
    
    # Check if email already exists as user
    existing_user = User.query.filter_by(email=item.email).first()
    if not existing_user:
        # Queue task to create user account
        task = Task(
            name='create_user_on_won',
            payload={
                'lead_type': lead_type,
                'lead_id': lead_id,
                'email': item.email,
                'first_name': item.first_name,
                'last_name': item.last_name,
                'phone': getattr(item, 'phone', None)
            }
        )
        db.session.add(task)
    
    # Queue welcome email task
    task = Task(
        name='send_welcome_email',
        payload={
            'lead_type': lead_type,
            'lead_id': lead_id,
            'email': item.email,
            'first_name': item.first_name
        }
    )
    db.session.add(task)


# =============================================================================
# Lead Detail View
# =============================================================================

@crm_bp.route('/lead/<lead_type>/<int:lead_id>')
@login_required
@role_required('admin')
def lead_detail(lead_type, lead_id):
    """Detailed view of a single lead with timeline."""
    item = get_lead(lead_type, lead_id)
    if not item:
        flash('Lead not found', 'error')
        return redirect(url_for('crm.dashboard'))
    
    # Get notes
    notes = LeadNote.query.filter_by(
        lead_type=lead_type, 
        lead_id=lead_id
    ).order_by(LeadNote.is_pinned.desc(), LeadNote.created_at.desc()).all()
    
    # Get activities
    activities = LeadActivity.query.filter_by(
        lead_type=lead_type, 
        lead_id=lead_id
    ).order_by(LeadActivity.created_at.desc()).limit(50).all()
    
    # Get lead score
    lead_score = LeadScore.query.filter_by(
        lead_type=lead_type, 
        lead_id=lead_id
    ).first()
    
    # Get follow-up reminders
    reminders = FollowUpReminder.query.filter_by(
        lead_type=lead_type,
        lead_id=lead_id,
        status='pending'
    ).order_by(FollowUpReminder.due_date).all()
    
    # Forms
    note_form = LeadNoteForm()
    assign_form = LeadAssignForm()
    reminder_form = FollowUpReminderForm()
    send_email_form = SendEmailForm()
    
    # Get pipeline stages for status change dropdown
    stages = get_pipeline_stages()
    
    return render_template('admin/crm/lead_detail.html',
                          item=item,
                          lead_type=lead_type,
                          notes=notes,
                          activities=activities,
                          lead_score=lead_score,
                          reminders=reminders,
                          note_form=note_form,
                          assign_form=assign_form,
                          reminder_form=reminder_form,
                          send_email_form=send_email_form,
                          stages=stages)


@crm_bp.route('/lead/<lead_type>/<int:lead_id>/note', methods=['POST'])
@login_required
@role_required('admin')
def add_note(lead_type, lead_id):
    """Add a note to a lead."""
    item = get_lead(lead_type, lead_id)
    if not item:
        return jsonify({'error': 'Lead not found'}), 404
    
    form = LeadNoteForm()
    if form.validate_on_submit():
        note = LeadNote(
            lead_type=lead_type,
            lead_id=lead_id,
            user_id=current_user.id,
            content=form.content.data,
            is_pinned=form.is_pinned.data
        )
        db.session.add(note)
        
        # Log activity
        log_activity(
            lead_type=lead_type,
            lead_id=lead_id,
            activity_type='note_added',
            description=f"Note added by {current_user.username}",
            user_id=current_user.id
        )
        
        db.session.commit()
        flash('Note added successfully', 'success')
    else:
        flash('Error adding note', 'error')
    
    return redirect(url_for('crm.lead_detail', lead_type=lead_type, lead_id=lead_id))


@crm_bp.route('/lead/<lead_type>/<int:lead_id>/assign', methods=['POST'])
@login_required
@role_required('admin')
def assign_lead(lead_type, lead_id):
    """Assign a lead to a team member."""
    if lead_type != 'contact':
        flash('Only contact form leads can be assigned', 'error')
        return redirect(url_for('crm.lead_detail', lead_type=lead_type, lead_id=lead_id))
    
    item = ContactFormSubmission.query.get(lead_id)
    if not item:
        flash('Lead not found', 'error')
        return redirect(url_for('crm.dashboard'))
    
    form = LeadAssignForm()
    if form.validate_on_submit():
        old_assigned = item.assigned_to.email if item.assigned_to else 'Unassigned'
        new_assigned_id = form.assigned_to_id.data if form.assigned_to_id.data != 0 else None
        
        item.assigned_to_id = new_assigned_id
        
        new_assigned_user = User.query.get(new_assigned_id) if new_assigned_id else None
        new_assigned = new_assigned_user.email if new_assigned_user else 'Unassigned'
        
        log_activity(
            lead_type=lead_type,
            lead_id=lead_id,
            activity_type='assigned',
            description=f"Lead assigned to {new_assigned}",
            user_id=current_user.id,
            old_value=old_assigned,
            new_value=new_assigned
        )
        
        db.session.commit()
        flash(f'Lead assigned to {new_assigned}', 'success')
    
    return redirect(url_for('crm.lead_detail', lead_type=lead_type, lead_id=lead_id))


@crm_bp.route('/lead/<lead_type>/<int:lead_id>/reminder', methods=['POST'])
@login_required
@role_required('admin')
def create_reminder(lead_type, lead_id):
    """Create a follow-up reminder for a lead."""
    item = get_lead(lead_type, lead_id)
    if not item:
        flash('Lead not found', 'error')
        return redirect(url_for('crm.dashboard'))
    
    form = FollowUpReminderForm()
    if form.validate_on_submit():
        assigned_to_id = form.assigned_to_id.data if form.assigned_to_id.data != 0 else current_user.id
        
        reminder = FollowUpReminder(
            lead_type=lead_type,
            lead_id=lead_id,
            assigned_to_id=assigned_to_id,
            due_date=form.due_date.data,
            note=form.note.data
        )
        db.session.add(reminder)
        
        log_activity(
            lead_type=lead_type,
            lead_id=lead_id,
            activity_type='reminder_created',
            description=f"Follow-up reminder created for {form.due_date.data.strftime('%Y-%m-%d %H:%M')}",
            user_id=current_user.id
        )
        
        db.session.commit()
        flash('Reminder created successfully', 'success')
    
    return redirect(url_for('crm.lead_detail', lead_type=lead_type, lead_id=lead_id))


# =============================================================================
# Pipeline Settings
# =============================================================================

@crm_bp.route('/pipeline/settings')
@login_required
@role_required('admin')
def pipeline_settings():
    """Admin page for pipeline configuration."""
    pipeline_name = request.args.get('pipeline', 'default')
    stages = PipelineStage.query.filter_by(pipeline_name=pipeline_name).order_by(PipelineStage.order).all()
    form = PipelineStageForm()
    
    return render_template('admin/crm/pipeline_settings.html',
                          stages=stages,
                          form=form,
                          pipeline_name=pipeline_name)


@crm_bp.route('/pipeline/stage', methods=['POST'])
@login_required
@role_required('admin')
def create_stage():
    """Create or update a pipeline stage."""
    form = PipelineStageForm()
    if form.validate_on_submit():
        stage_id = request.form.get('stage_id')
        
        if stage_id:
            # Update existing
            stage = PipelineStage.query.get(int(stage_id))
            if stage:
                stage.name = form.name.data
                stage.pipeline_name = form.pipeline_name.data
                stage.order = form.order.data
                stage.color = form.color.data
                stage.probability = form.probability.data
                stage.is_won_stage = form.is_won_stage.data
                stage.is_lost_stage = form.is_lost_stage.data
                flash('Stage updated successfully', 'success')
        else:
            # Create new
            stage = PipelineStage(
                name=form.name.data,
                pipeline_name=form.pipeline_name.data,
                order=form.order.data,
                color=form.color.data,
                probability=form.probability.data,
                is_won_stage=form.is_won_stage.data,
                is_lost_stage=form.is_lost_stage.data
            )
            db.session.add(stage)
            flash('Stage created successfully', 'success')
        
        db.session.commit()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('crm.pipeline_settings', pipeline=form.pipeline_name.data))


@crm_bp.route('/pipeline/stage/<int:stage_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_stage(stage_id):
    """Delete a pipeline stage."""
    stage = PipelineStage.query.get_or_404(stage_id)
    pipeline_name = stage.pipeline_name
    db.session.delete(stage)
    db.session.commit()
    flash('Stage deleted successfully', 'success')
    return redirect(url_for('crm.pipeline_settings', pipeline=pipeline_name))


@crm_bp.route('/pipeline/reorder', methods=['POST'])
@login_required
@role_required('admin')
def reorder_stages():
    """Reorder pipeline stages via AJAX."""
    data = request.json
    stage_order = data.get('order', [])  # List of stage IDs in new order
    
    for idx, stage_id in enumerate(stage_order):
        stage = PipelineStage.query.get(int(stage_id))
        if stage:
            stage.order = idx
    
    db.session.commit()
    return jsonify({'success': True})


# =============================================================================
# Email Templates
# =============================================================================

@crm_bp.route('/templates')
@login_required
@role_required('admin')
def email_templates():
    """List email templates."""
    import json
    from flask_wtf.csrf import generate_csrf
    
    templates = EmailTemplate.query.order_by(EmailTemplate.template_type, EmailTemplate.name).all()
    form = EmailTemplateForm()
    csrf_token = generate_csrf()
    
    # Serialize for AdminDataTable
    templates_json = json.dumps([{
        'id': t.id,
        'name': f'<strong>{t.name}</strong>',
        'type': f'<span class="badge bg-info">{t.template_type}</span>',
        'subject': (t.subject[:40] + '...') if len(t.subject) > 40 else t.subject,
        'status': '<span class="badge bg-success">Active</span>' if t.is_active else '<span class="badge bg-secondary">Inactive</span>',
        'actions': f'''<button type="button" class="btn btn-sm btn-outline-primary" onclick="editTemplate({t.id}, '{t.name}', '{t.subject.replace("'", "\\'")}', `{(t.body or '').replace('`', '\\`')}`, '{t.template_type}', {'true' if t.is_active else 'false'})"><i class="fas fa-edit"></i></button>
            <form method="POST" action="{url_for('crm.delete_template', template_id=t.id)}" class="d-inline" onsubmit="return confirm('Delete this template?');">
                <input type="hidden" name="csrf_token" value="{csrf_token}">
                <button type="submit" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button>
            </form>'''
    } for t in templates])
    
    return render_template('admin/crm/templates.html', templates=templates, form=form, templates_json=templates_json)


@crm_bp.route('/templates', methods=['POST'])
@login_required
@role_required('admin')
def create_template():
    """Create or update an email template."""
    form = EmailTemplateForm()
    if form.validate_on_submit():
        template_id = request.form.get('template_id')
        
        if template_id:
            template = EmailTemplate.query.get(int(template_id))
            if template:
                template.name = form.name.data
                template.subject = form.subject.data
                template.body = form.body.data
                template.template_type = form.template_type.data
                template.is_active = form.is_active.data
                flash('Template updated', 'success')
        else:
            template = EmailTemplate(
                name=form.name.data,
                subject=form.subject.data,
                body=form.body.data,
                template_type=form.template_type.data,
                is_active=form.is_active.data,
                created_by_id=current_user.id
            )
            db.session.add(template)
            flash('Template created', 'success')
        
        db.session.commit()
    
    return redirect(url_for('crm.email_templates'))


@crm_bp.route('/templates/<int:template_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_template(template_id):
    """Delete an email template."""
    template = EmailTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    flash('Template deleted', 'success')
    return redirect(url_for('crm.email_templates'))


# =============================================================================
# Analytics
# =============================================================================

@crm_bp.route('/analytics')
@login_required
@role_required('admin')
def analytics():
    """CRM analytics dashboard."""
    # Get pipeline stages for funnel
    stages = get_pipeline_stages()
    
    # Count leads per stage
    funnel_data = []
    for stage in stages:
        contact_count = ContactFormSubmission.query.filter_by(status=stage.name).count()
        appt_count = Appointment.query.filter_by(status=stage.name).count()
        funnel_data.append({
            'stage': stage.name,
            'color': stage.color,
            'count': contact_count + appt_count,
            'probability': stage.probability
        })
    
    # Source attribution
    source_data = db.session.query(
        ContactFormSubmission.source,
        func.count(ContactFormSubmission.id)
    ).group_by(ContactFormSubmission.source).all()
    
    # Time period stats
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'total_leads': ContactFormSubmission.query.count() + Appointment.query.count(),
        'new_this_week': ContactFormSubmission.query.filter(
            ContactFormSubmission.submitted_at >= week_ago
        ).count() + Appointment.query.filter(
            Appointment.created_at >= week_ago
        ).count(),
        'won_this_month': ContactFormSubmission.query.filter(
            ContactFormSubmission.status == 'Won',
            ContactFormSubmission.submitted_at >= month_ago
        ).count() + Appointment.query.filter(
            Appointment.status == 'Won',
            Appointment.created_at >= month_ago
        ).count(),
        'conversion_rate': 0
    }
    
    # Calculate conversion rate
    if stats['total_leads'] > 0:
        won_total = ContactFormSubmission.query.filter_by(status='Won').count() + \
                   Appointment.query.filter_by(status='Won').count()
        stats['conversion_rate'] = round((won_total / stats['total_leads']) * 100, 1)
    
    return render_template('admin/crm/analytics.html',
                          funnel_data=funnel_data,
                          source_data=source_data,
                          stats=stats,
                          stages=stages)


@crm_bp.route('/analytics/api/funnel')
@login_required
@role_required('admin')
def api_funnel():
    """API endpoint for funnel chart data."""
    stages = get_pipeline_stages()
    
    data = []
    for stage in stages:
        contact_count = ContactFormSubmission.query.filter_by(status=stage.name).count()
        appt_count = Appointment.query.filter_by(status=stage.name).count()
        data.append({
            'stage': stage.name,
            'count': contact_count + appt_count,
            'color': stage.color
        })
    
    return jsonify(data)


@crm_bp.route('/analytics/api/sources')
@login_required
@role_required('admin')
def api_sources():
    """API endpoint for source attribution data."""
    source_data = db.session.query(
        ContactFormSubmission.source,
        func.count(ContactFormSubmission.id)
    ).group_by(ContactFormSubmission.source).all()
    
    return jsonify([{'source': s or 'unknown', 'count': c} for s, c in source_data])


@crm_bp.route('/analytics/api/time-to-close')
@login_required
@role_required('admin')
def api_time_to_close():
    """API endpoint for time-to-close analysis."""
    # Calculate average days from creation to Won status
    won_leads = ContactFormSubmission.query.filter_by(status='Won').all()
    
    if not won_leads:
        return jsonify({'average_days': 0, 'data': []})
    
    stage_times = {}
    for lead in won_leads:
        # Get activities for this lead
        activities = LeadActivity.query.filter_by(
            lead_type='contact',
            lead_id=lead.id,
            activity_type='status_change'
        ).order_by(LeadActivity.created_at).all()
        
        for activity in activities:
            stage = activity.new_value
            if stage not in stage_times:
                stage_times[stage] = []
            # Time spent would need first entry in stage - this is simplified
    
    # Simplified: just return time from creation to now for won leads
    total_days = sum([(datetime.utcnow() - lead.submitted_at).days for lead in won_leads])
    avg_days = total_days / len(won_leads) if won_leads else 0
    
    return jsonify({
        'average_days': round(avg_days, 1),
        'won_count': len(won_leads)
    })


# =============================================================================
# Duplicates (kept from original)
# =============================================================================

@crm_bp.route('/duplicates')
@login_required
@role_required('admin')
def duplicates():
    """Find duplicate leads by email."""
    import json
    
    # Get all emails with count > 1 in Contacts
    contact_dups = db.session.query(
        ContactFormSubmission.email, 
        func.count(ContactFormSubmission.email)
    ).group_by(ContactFormSubmission.email).having(
        func.count(ContactFormSubmission.email) > 1
    ).all()
    
    # Get all emails with count > 1 in Appointments
    appt_dups = db.session.query(
        Appointment.email, 
        func.count(Appointment.email)
    ).group_by(Appointment.email).having(
        func.count(Appointment.email) > 1
    ).all()
    
    # Find emails present in BOTH tables
    c_emails = set(c.email for c in ContactFormSubmission.query.with_entities(
        ContactFormSubmission.email
    ).all())
    a_emails = set(a.email for a in Appointment.query.with_entities(
        Appointment.email
    ).all())
    cross_dups = c_emails.intersection(a_emails)
    
    duplicates_data = []
    
    # Process Contact duplicates
    for email, count in contact_dups:
        items = ContactFormSubmission.query.filter_by(email=email).all()
        duplicates_data.append({
            'email': email,
            'type': 'Contact Duplicates',
            'count': count,
            'records': items
        })
    
    # Process Appointment duplicates
    for email, count in appt_dups:
        items = Appointment.query.filter_by(email=email).all()
        duplicates_data.append({
            'email': email,
            'type': 'Appointment Duplicates',
            'count': count,
            'records': items
        })
    
    # Process Cross duplicates
    for email in cross_dups:
        c_items = ContactFormSubmission.query.filter_by(email=email).all()
        a_items = Appointment.query.filter_by(email=email).all()
        duplicates_data.append({
            'email': email,
            'type': 'Cross-Table Match',
            'count': len(c_items) + len(a_items),
            'records': c_items + a_items
        })
    
    # Flatten for AdminDataTable - each record becomes a row
    flattened_data = []
    type_colors = {
        'Contact Duplicates': 'warning',
        'Appointment Duplicates': 'info',
        'Cross-Table Match': 'danger'
    }
    
    for group in duplicates_data:
        for record in group['records']:
            record_type = 'Appt' if hasattr(record, '__tablename__') and record.__tablename__ == 'appointment' else 'Contact'
            record_date = record.submitted_at if hasattr(record, 'submitted_at') and record.submitted_at else record.created_at
            
            flattened_data.append({
                'email': f'<strong>{group["email"]}</strong>',
                'group_type': f'<span class="badge bg-{type_colors.get(group["type"], "secondary")}">{group["type"]}</span> <small class="text-muted">({group["count"]} items)</small>',
                'record_type': f'<span class="badge bg-{"info" if record_type == "Appt" else "warning"}">{record_type}</span>',
                'name': f'{record.first_name} {record.last_name}',
                'date': record_date.strftime('%Y-%m-%d %H:%M') if record_date else '-',
                'notes': f'<small>{(record.notes or "No notes")[:50]}{"..." if record.notes and len(record.notes) > 50 else ""}</small>',
                'status': f'<span class="badge bg-secondary">{record.status or "New"}</span>'
            })
    
    duplicates_json = json.dumps(flattened_data)
    
    columns_json = json.dumps([
        {'accessorKey': 'email', 'header': 'Email', 'html': True},
        {'accessorKey': 'group_type', 'header': 'Duplicate Type', 'html': True},
        {'accessorKey': 'record_type', 'header': 'Record', 'html': True},
        {'accessorKey': 'name', 'header': 'Name'},
        {'accessorKey': 'date', 'header': 'Date'},
        {'accessorKey': 'notes', 'header': 'Notes', 'html': True},
        {'accessorKey': 'status', 'header': 'Status', 'html': True}
    ])
    
    return render_template('admin/crm/duplicates.html', 
                          duplicates=duplicates_data,
                          duplicates_json=duplicates_json,
                          columns_json=columns_json,
                          has_duplicates=len(duplicates_data) > 0)
