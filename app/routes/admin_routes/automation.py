"""
Phase 10: Automation Admin Routes

Provides both traditional Jinja2 views and JSON API endpoints for the 
React-based UnifiedAutomationDashboard component.
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

# =============================================================================
# Available Trigger Events and Action Types
# =============================================================================

TRIGGER_EVENTS = [
    {'value': 'lead.created', 'label': 'Lead Created', 'description': 'When a new lead is submitted via contact form'},
    {'value': 'lead.updated', 'label': 'Lead Updated', 'description': 'When a lead status or details change'},
    {'value': 'lead.won', 'label': 'Lead Won', 'description': 'When a lead is marked as won/converted'},
    {'value': 'order.created', 'label': 'Order Created', 'description': 'When a new order is placed'},
    {'value': 'order.updated', 'label': 'Order Updated', 'description': 'When order status changes'},
    {'value': 'order.completed', 'label': 'Order Completed', 'description': 'When an order is marked complete'},
    {'value': 'product.created', 'label': 'Product Created', 'description': 'When a new product is added'},
    {'value': 'user.registered', 'label': 'User Registered', 'description': 'When a new user signs up'},
    {'value': 'appointment.booked', 'label': 'Appointment Booked', 'description': 'When a customer books an appointment'},
    {'value': 'appointment.cancelled', 'label': 'Appointment Cancelled', 'description': 'When an appointment is cancelled'},
    {'value': 'subscription.created', 'label': 'Subscription Created', 'description': 'When a new subscription starts'},
    {'value': 'subscription.cancelled', 'label': 'Subscription Cancelled', 'description': 'When a subscription is cancelled'},
]

ACTION_TYPES = [
    {
        'value': 'send_email',
        'label': 'Send Email',
        'icon': '📧',
        'description': 'Send an email to a specified recipient',
        'fields': [
            {'name': 'recipient', 'label': 'Recipient', 'type': 'text', 'placeholder': '{{context.email}} or admin@example.com', 'required': True},
            {'name': 'subject', 'label': 'Subject', 'type': 'text', 'placeholder': 'Email subject line', 'required': True},
            {'name': 'body', 'label': 'Body', 'type': 'textarea', 'placeholder': 'Email body content...', 'required': True},
        ]
    },
    {
        'value': 'log_activity',
        'label': 'Log Activity',
        'icon': '📝',
        'description': 'Log an activity message to the system',
        'fields': [
            {'name': 'message', 'label': 'Message', 'type': 'text', 'placeholder': 'Activity message to log', 'required': True},
        ]
    },
    {
        'value': 'send_webhook',
        'label': 'Send Webhook',
        'icon': '🔗',
        'description': 'Send data to an external URL',
        'fields': [
            {'name': 'url', 'label': 'Webhook URL', 'type': 'text', 'placeholder': 'https://api.example.com/webhook', 'required': True},
            {'name': 'method', 'label': 'HTTP Method', 'type': 'select', 'options': ['POST', 'PUT', 'PATCH'], 'required': True},
            {'name': 'headers', 'label': 'Headers (JSON)', 'type': 'textarea', 'placeholder': '{"Authorization": "Bearer ..."}', 'required': False},
            {'name': 'payload', 'label': 'Payload Template', 'type': 'textarea', 'placeholder': '{"event": "{{event_name}}", "data": {{context}}}', 'required': False},
        ]
    },
    {
        'value': 'delay',
        'label': 'Delay',
        'icon': '⏱️',
        'description': 'Wait before executing the next step',
        'fields': [
            {'name': 'duration', 'label': 'Duration', 'type': 'number', 'placeholder': '5', 'required': True},
            {'name': 'unit', 'label': 'Unit', 'type': 'select', 'options': ['minutes', 'hours', 'days'], 'required': True},
        ]
    },
    {
        'value': 'create_task',
        'label': 'Create Task',
        'icon': '✅',
        'description': 'Create a task for follow-up',
        'fields': [
            {'name': 'title', 'label': 'Task Title', 'type': 'text', 'placeholder': 'Follow up with {{context.first_name}}', 'required': True},
            {'name': 'description', 'label': 'Description', 'type': 'textarea', 'placeholder': 'Task details...', 'required': False},
            {'name': 'due_in_days', 'label': 'Due In (Days)', 'type': 'number', 'placeholder': '3', 'required': False},
        ]
    },
    {
        'value': 'send_notification',
        'label': 'Send Notification',
        'icon': '🔔',
        'description': 'Send an in-app notification to a user',
        'fields': [
            {'name': 'user_id', 'label': 'User ID (or "admin")', 'type': 'text', 'placeholder': 'admin or {{context.user_id}}', 'required': True},
            {'name': 'title', 'label': 'Title', 'type': 'text', 'placeholder': 'New notification', 'required': True},
            {'name': 'message', 'label': 'Message', 'type': 'text', 'placeholder': 'Notification content...', 'required': True},
        ]
    },
]

CONTEXT_VARIABLES = [
    {'name': 'context.id', 'description': 'Entity ID (lead, order, user, etc.)'},
    {'name': 'context.email', 'description': 'Email address'},
    {'name': 'context.first_name', 'description': 'First name'},
    {'name': 'context.last_name', 'description': 'Last name'},
    {'name': 'context.phone', 'description': 'Phone number'},
    {'name': 'context.total_amount', 'description': 'Order total amount'},
    {'name': 'context.status', 'description': 'Current status'},
    {'name': 'event_name', 'description': 'The trigger event name'},
]

# =============================================================================
# Helper Functions
# =============================================================================

def serialize_workflow(workflow, include_steps=False):
    """Serialize a workflow to dict."""
    data = {
        'id': workflow.id,
        'name': workflow.name,
        'description': workflow.description,
        'trigger_event': workflow.trigger_event,
        'is_active': workflow.is_active,
        'steps_count': workflow.steps.count(),
        'created_at': workflow.created_at.isoformat() if workflow.created_at else None,
        'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else None,
    }
    if include_steps:
        data['steps'] = [serialize_step(step) for step in workflow.steps.order_by(WorkflowStep.order)]
    return data

def serialize_step(step):
    """Serialize a workflow step to dict."""
    return {
        'id': step.id,
        'workflow_id': step.workflow_id,
        'action_type': step.action_type,
        'config': step.config or {},
        'order': step.order,
        'created_at': step.created_at.isoformat() if step.created_at else None,
    }

def is_ajax_request():
    """Check if request is AJAX/JSON."""
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        request.headers.get('Accept', '').startswith('application/json') or
        request.content_type == 'application/json'
    )

# =============================================================================
# Page Routes (Jinja2 Templates)
# =============================================================================

@automation_bp.route('/')
@login_required
@admin_required
def index():
    """Render the automation dashboard (React component)."""
    return render_template('admin/automation/index.html')

@automation_bp.route('/new')
@login_required
@admin_required
def new_workflow():
    """Redirect to main page with create mode."""
    return redirect(url_for('automation.index') + '?action=new')

@automation_bp.route('/<int:workflow_id>/edit')
@login_required
@admin_required
def edit_workflow(workflow_id):
    """Redirect to main page with edit mode."""
    return redirect(url_for('automation.index') + f'?edit={workflow_id}')

# =============================================================================
# JSON API Routes
# =============================================================================

@automation_bp.route('/api/events')
@login_required
@admin_required
def api_get_events():
    """Get available trigger events."""
    return jsonify({'events': TRIGGER_EVENTS})

@automation_bp.route('/api/action-types')
@login_required
@admin_required
def api_get_action_types():
    """Get available action types with field schemas."""
    return jsonify({'action_types': ACTION_TYPES})

@automation_bp.route('/api/context-variables')
@login_required
@admin_required
def api_get_context_variables():
    """Get available context variables for templates."""
    return jsonify({'variables': CONTEXT_VARIABLES})

@automation_bp.route('/api/workflows')
@login_required
@admin_required
def api_list_workflows():
    """List all workflows."""
    workflows = Workflow.query.order_by(Workflow.created_at.desc()).all()
    return jsonify({
        'workflows': [serialize_workflow(w) for w in workflows],
        'total': len(workflows),
        'active_count': sum(1 for w in workflows if w.is_active),
        'inactive_count': sum(1 for w in workflows if not w.is_active),
        'total_steps': sum(w.steps.count() for w in workflows),
    })

@automation_bp.route('/api/workflows/<int:workflow_id>')
@login_required
@admin_required
def api_get_workflow(workflow_id):
    """Get a single workflow with steps."""
    workflow = Workflow.query.get_or_404(workflow_id)
    return jsonify({'workflow': serialize_workflow(workflow, include_steps=True)})

@automation_bp.route('/api/workflows', methods=['POST'])
@login_required
@admin_required
def api_create_workflow():
    """Create a new workflow."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    trigger_event = data.get('trigger_event', '').strip()
    if not trigger_event:
        return jsonify({'error': 'Trigger event is required'}), 400
    
    workflow = Workflow(
        name=name,
        trigger_event=trigger_event,
        description=data.get('description', '').strip(),
        is_active=data.get('is_active', True),
    )
    db.session.add(workflow)
    db.session.commit()
    
    log_audit_event(current_user.id, 'create_workflow', 'Workflow', workflow.id, {'name': name}, request.remote_addr)
    
    return jsonify({
        'success': True,
        'message': 'Workflow created successfully',
        'workflow': serialize_workflow(workflow, include_steps=True)
    }), 201

@automation_bp.route('/api/workflows/<int:workflow_id>', methods=['PUT'])
@login_required
@admin_required
def api_update_workflow(workflow_id):
    """Update a workflow."""
    workflow = Workflow.query.get_or_404(workflow_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'name' in data:
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Name cannot be empty'}), 400
        workflow.name = name
    
    if 'trigger_event' in data:
        trigger_event = data['trigger_event'].strip()
        if not trigger_event:
            return jsonify({'error': 'Trigger event cannot be empty'}), 400
        workflow.trigger_event = trigger_event
    
    if 'description' in data:
        workflow.description = data['description'].strip() if data['description'] else None
    
    if 'is_active' in data:
        workflow.is_active = bool(data['is_active'])
    
    db.session.commit()
    log_audit_event(current_user.id, 'update_workflow', 'Workflow', workflow.id, {'name': workflow.name}, request.remote_addr)
    
    return jsonify({
        'success': True,
        'message': 'Workflow updated successfully',
        'workflow': serialize_workflow(workflow, include_steps=True)
    })

@automation_bp.route('/api/workflows/<int:workflow_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_workflow(workflow_id):
    """Delete a workflow."""
    workflow = Workflow.query.get_or_404(workflow_id)
    name = workflow.name
    db.session.delete(workflow)
    db.session.commit()
    
    log_audit_event(current_user.id, 'delete_workflow', 'Workflow', workflow_id, {'name': name}, request.remote_addr)
    
    return jsonify({
        'success': True,
        'message': f'Workflow "{name}" deleted successfully'
    })

@automation_bp.route('/api/workflows/<int:workflow_id>/toggle', methods=['POST'])
@login_required
@admin_required
def api_toggle_workflow(workflow_id):
    """Toggle workflow active status."""
    workflow = Workflow.query.get_or_404(workflow_id)
    workflow.is_active = not workflow.is_active
    db.session.commit()
    
    status = 'activated' if workflow.is_active else 'deactivated'
    log_audit_event(current_user.id, 'toggle_workflow', 'Workflow', workflow.id, {'is_active': workflow.is_active}, request.remote_addr)
    
    return jsonify({
        'success': True,
        'message': f'Workflow {status}',
        'is_active': workflow.is_active
    })

@automation_bp.route('/api/workflows/<int:workflow_id>/steps', methods=['POST'])
@login_required
@admin_required
def api_add_step(workflow_id):
    """Add a step to a workflow."""
    workflow = Workflow.query.get_or_404(workflow_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    action_type = data.get('action_type', '').strip()
    if not action_type:
        return jsonify({'error': 'Action type is required'}), 400
    
    # Validate action type exists
    valid_types = [at['value'] for at in ACTION_TYPES]
    if action_type not in valid_types:
        return jsonify({'error': f'Invalid action type: {action_type}'}), 400
    
    config = data.get('config', {})
    
    # Calculate order (append to end)
    max_order = db.session.query(db.func.max(WorkflowStep.order)).filter_by(workflow_id=workflow.id).scalar()
    new_order = (max_order or -1) + 1
    
    step = WorkflowStep(
        workflow_id=workflow.id,
        action_type=action_type,
        config=config,
        order=new_order,
    )
    db.session.add(step)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Step added successfully',
        'step': serialize_step(step)
    }), 201

@automation_bp.route('/api/steps/<int:step_id>', methods=['PUT'])
@login_required
@admin_required
def api_update_step(step_id):
    """Update a workflow step."""
    step = WorkflowStep.query.get_or_404(step_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'action_type' in data:
        action_type = data['action_type'].strip()
        valid_types = [at['value'] for at in ACTION_TYPES]
        if action_type not in valid_types:
            return jsonify({'error': f'Invalid action type: {action_type}'}), 400
        step.action_type = action_type
    
    if 'config' in data:
        step.config = data['config']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Step updated successfully',
        'step': serialize_step(step)
    })

@automation_bp.route('/api/steps/<int:step_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_step(step_id):
    """Delete a workflow step."""
    step = WorkflowStep.query.get_or_404(step_id)
    workflow_id = step.workflow_id
    order = step.order
    
    db.session.delete(step)
    
    # Reorder remaining steps
    WorkflowStep.query.filter(
        WorkflowStep.workflow_id == workflow_id,
        WorkflowStep.order > order
    ).update({WorkflowStep.order: WorkflowStep.order - 1})
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Step deleted successfully'
    })

@automation_bp.route('/api/workflows/<int:workflow_id>/reorder-steps', methods=['POST'])
@login_required
@admin_required
def api_reorder_steps(workflow_id):
    """Reorder workflow steps."""
    workflow = Workflow.query.get_or_404(workflow_id)
    data = request.get_json()
    if not data or 'step_ids' not in data:
        return jsonify({'error': 'step_ids array is required'}), 400
    
    step_ids = data['step_ids']
    if not isinstance(step_ids, list):
        return jsonify({'error': 'step_ids must be an array'}), 400
    
    # Verify all step IDs belong to this workflow
    existing_steps = {s.id for s in workflow.steps}
    for step_id in step_ids:
        if step_id not in existing_steps:
            return jsonify({'error': f'Step {step_id} does not belong to this workflow'}), 400
    
    # Update order
    for new_order, step_id in enumerate(step_ids):
        WorkflowStep.query.filter_by(id=step_id).update({'order': new_order})
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Steps reordered successfully',
        'workflow': serialize_workflow(workflow, include_steps=True)
    })

# =============================================================================
# Legacy Form Routes (kept for backward compatibility)
# =============================================================================

@automation_bp.route('/legacy/new', methods=['POST'])
@login_required
@admin_required
def legacy_create_workflow():
    """Legacy form handler for creating workflow."""
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
    return redirect(url_for('automation.index') + f'?edit={workflow.id}')

@automation_bp.route('/legacy/<int:workflow_id>/update', methods=['POST'])
@login_required
@admin_required
def legacy_update_workflow(workflow_id):
    """Legacy form handler for updating workflow."""
    workflow = Workflow.query.get_or_404(workflow_id)
    
    workflow.name = request.form.get('name')
    workflow.trigger_event = request.form.get('trigger_event')
    workflow.description = request.form.get('description')
    workflow.is_active = 'is_active' in request.form
    
    db.session.commit()
    log_audit_event(current_user.id, 'update_workflow', 'Workflow', workflow.id, {'name': workflow.name}, request.remote_addr)
    flash('Workflow updated.', 'success')
    
    return redirect(url_for('automation.index') + f'?edit={workflow.id}')

@automation_bp.route('/legacy/<int:workflow_id>/steps/new', methods=['POST'])
@login_required
@admin_required
def legacy_add_step(workflow_id):
    """Legacy form handler for adding step."""
    workflow = Workflow.query.get_or_404(workflow_id)
    
    action_type = request.form.get('action_type')
    
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
        order=workflow.steps.count()
    )
    db.session.add(step)
    db.session.commit()
    
    flash('Step added.', 'success')
    return redirect(url_for('automation.index') + f'?edit={workflow.id}')

@automation_bp.route('/legacy/steps/<int:step_id>/delete', methods=['POST'])
@login_required
@admin_required
def legacy_delete_step(step_id):
    """Legacy form handler for deleting step."""
    step = WorkflowStep.query.get_or_404(step_id)
    workflow_id = step.workflow_id
    db.session.delete(step)
    db.session.commit()
    
    flash('Step removed.', 'success')
    return redirect(url_for('automation.index') + f'?edit={workflow_id}')

@automation_bp.route('/legacy/<int:workflow_id>/delete', methods=['POST'])
@login_required
@admin_required
def legacy_delete_workflow(workflow_id):
    """Legacy form handler for deleting workflow."""
    workflow = Workflow.query.get_or_404(workflow_id)
    db.session.delete(workflow)
    db.session.commit()
    
    log_audit_event(current_user.id, 'delete_workflow', 'Workflow', workflow_id, {'name': workflow.name}, request.remote_addr)
    flash('Workflow deleted.', 'success')
    return redirect(url_for('automation.index'))
