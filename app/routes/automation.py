"""
Phase 10: Automation Admin Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.modules.auth_manager import admin_required
from app.models import Workflow, WorkflowStep
from app.database import db
from app.modules.audit import log_audit_event
from app.forms import CSRFTokenForm
import json

automation_bp = Blueprint('automation', __name__, url_prefix='/admin/automation', template_folder='templates')

@automation_bp.route('/')
@login_required
@admin_required
def index():
    """List all workflows."""
    workflows = Workflow.query.all()
    form = CSRFTokenForm()
    
    # Serialize for AdminDataTable
    workflows_json = json.dumps([{
        'id': w.id,
        'name': f'<strong>{w.name}</strong>' + (f'<br><small class="text-muted">{w.description}</small>' if w.description else ''),
        'trigger_event': f'<code>{w.trigger_event}</code>',
        'steps': w.steps.count(),
        'status': '<span class="badge bg-success">Active</span>' if w.is_active else '<span class="badge bg-secondary">Inactive</span>',
        'actions': f'<a href="{url_for("automation.edit_workflow", workflow_id=w.id)}" class="btn btn-sm btn-outline-primary">Edit</a> <form action="{url_for("automation.delete_workflow", workflow_id=w.id)}" method="POST" class="d-inline" onsubmit="return confirm(\'Delete this workflow?\');"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}" /><button type="submit" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button></form>'
    } for w in workflows])
    
    return render_template('admin/automation/index.html', workflows=workflows, workflows_json=workflows_json)

@automation_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_workflow():
    """Create a new workflow."""
    if request.method == 'POST':
        name = request.form.get('name')
        trigger_event = request.form.get('trigger_event')
        description = request.form.get('description')
        
        workflow = Workflow(
            name=name,
            trigger_event=trigger_event,
            description=description,
            is_active=True
        )
        db.session.add(workflow)
        db.session.commit()
        
        log_audit_event(current_user.id, 'create_workflow', 'Workflow', workflow.id, {'name': name}, request.remote_addr)
        flash('Workflow created. Now add steps.', 'success')
        return redirect(url_for('automation.edit_workflow', workflow_id=workflow.id))
        
    return render_template('admin/automation/new.html')

@automation_bp.route('/<int:workflow_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_workflow(workflow_id):
    """Edit workflow and its steps."""
    workflow = Workflow.query.get_or_404(workflow_id)
    
    if request.method == 'POST':
        workflow.name = request.form.get('name')
        workflow.trigger_event = request.form.get('trigger_event')
        workflow.description = request.form.get('description')
        workflow.is_active = 'is_active' in request.form
        
        db.session.commit()
        log_audit_event(current_user.id, 'update_workflow', 'Workflow', workflow.id, {'name': workflow.name}, request.remote_addr)
        flash('Workflow updated.', 'success')
        
    return render_template('admin/automation/edit.html', workflow=workflow)

@automation_bp.route('/<int:workflow_id>/steps/new', methods=['POST'])
@login_required
@admin_required
def add_step(workflow_id):
    """Add a step to a workflow."""
    workflow = Workflow.query.get_or_404(workflow_id)
    
    action_type = request.form.get('action_type')
    
    # Build config from form data based on action type
    config = {}
    if action_type == 'send_email':
        config['recipient'] = request.form.get('recipient')
        config['subject'] = request.form.get('subject')
        config['body'] = request.form.get('body')
    elif action_type == 'log_activity':
        config['message'] = request.form.get('message')
    
    step = WorkflowStep(
        workflow_id=workflow.id,
        action_type=action_type,
        config=config,
        order=workflow.steps.count() # Append to end
    )
    db.session.add(step)
    db.session.commit()
    
    flash('Step added.', 'success')
    return redirect(url_for('automation.edit_workflow', workflow_id=workflow.id))

@automation_bp.route('/steps/<int:step_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_step(step_id):
    """Delete a workflow step."""
    step = WorkflowStep.query.get_or_404(step_id)
    workflow_id = step.workflow_id
    db.session.delete(step)
    db.session.commit()
    
    flash('Step removed.', 'success')
    return redirect(url_for('automation.edit_workflow', workflow_id=workflow_id))

@automation_bp.route('/<int:workflow_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_workflow(workflow_id):
    """Delete a workflow."""
    workflow = Workflow.query.get_or_404(workflow_id)
    db.session.delete(workflow)
    db.session.commit()
    
    log_audit_event(current_user.id, 'delete_workflow', 'Workflow', workflow_id, {'name': workflow.name}, request.remote_addr)
    flash('Workflow deleted.', 'success')
    return redirect(url_for('automation.index'))
