"""
Phase 10: Automation Module

Handles system events, triggers webhooks, and executes internal workflows.
"""
from flask import current_app
from app.database import db
from app.models import Workflow, WorkflowStep, Task
from app.modules.webhooks import fire_webhook

def trigger_event(event_name, payload=None):
    """
    Trigger a system event.
    
    1. Fires outbound webhooks subscribed to this event.
    2. checks for and executes internal workflows triggered by this event.
    
    Args:
        event_name (str): The name of the event (e.g., 'lead.created').
        payload (dict): Data context for the event.
    """
    if payload is None:
        payload = {}

    try:
        # 1. Fire Webhooks (Phase 9)
        fire_webhook(event_name, payload)
    except Exception as e:
        # Don't let webhook failure stop workflow execution
        if current_app:
            current_app.logger.error(f"Error firing webhooks for {event_name}: {e}")

    try:
        # 2. Trigger Workflows (Phase 10)
        _trigger_workflows(event_name, payload)
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Error triggering workflows for {event_name}: {e}")


def _trigger_workflows(event_name, payload):
    """Find and queue active workflows for this event."""
    workflows = Workflow.query.filter_by(
        trigger_event=event_name,
        is_active=True
    ).all()
    
    if not workflows:
        return
        
    count = 0
    for wf in workflows:
        # Create a task to execute the workflow asynchronously
        task = Task(
            name='execute_workflow',
            payload={
                'workflow_id': wf.id,
                'context': payload,
                'event_name': event_name
            },
            priority=5
        )
        db.session.add(task)
        count += 1
    
    db.session.commit()
    if current_app and count > 0:
        current_app.logger.info(f"Triggered {count} workflows for event: {event_name}")


def handle_execute_workflow(payload):
    """
    Worker task handler to execute a workflow.
    """
    workflow_id = payload.get('workflow_id')
    context = payload.get('context', {})
    event_name = payload.get('event_name')

    workflow = Workflow.query.get(workflow_id)
    if not workflow:
        if current_app:
            current_app.logger.error(f"Workflow {workflow_id} not found during execution")
        return

    if current_app:
        current_app.logger.info(f"Executing workflow '{workflow.name}' (ID: {workflow.id}) caused by {event_name}")

    # Execute steps in order
    steps = workflow.steps  # Loaded via dynamic relationship
    for step in steps:
        try:
            _execute_step(step, context)
        except Exception as e:
            if current_app:
                current_app.logger.error(f"Error executing step {step.id} (Action: {step.action_type}) in workflow {workflow.id}: {e}")
            # Decide: stop workflow or continue? For robust automation, usually stop or mark failed.
            # For now, we log and continue to try subsequent steps, or we could return.
            return 

def _execute_step(step, context):
    """
    Execute a single workflow step action.
    """
    action_type = step.action_type
    config = step.config or {}
    
    if current_app:
        current_app.logger.info(f"workflow_step: {action_type} config={config}")

    if action_type == 'send_email':
        _action_send_email(config, context)
    elif action_type == 'create_task':
        _action_create_task(config, context)
    elif action_type == 'log_activity':
        _action_log_activity(config, context)
    else:
        if current_app:
            current_app.logger.warning(f"Unknown workflow action type: {action_type}")

def _action_send_email(config, context):
    """
    Action: Send an email.
    Config: recipient_email (can use placeholders), subject, body
    """
    from app.models import Task
    
    # Simple template substitution
    recipient = config.get('recipient')
    subject = config.get('subject')
    body = config.get('body')

    # Allow basic context implementation (extremely basic for now)
    # e.g., {{email}} from context
    # Real implementation would use Jinja2 string rendering
    
    task = Task(
        name='send_email',
        payload={
            'recipient': recipient, # In real app, resolve this from context if needed
            'subject': subject,
            'body': body
        }
    )
    db.session.add(task)
    db.session.commit()

def _action_create_task(config, context):
    """
    Action: Create a generic task.
    """
    # ... implementation (e.g. creating a Todo item in CRM)
    pass

def _action_log_activity(config, context):
    """
    Action: Log to audit log or console.
    """
    message = config.get('message', 'Workflow executed')
    if current_app:
        current_app.logger.info(f"WORKFLOW LOG: {message} - Context: {context.keys()}")
