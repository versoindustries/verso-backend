"""
Workflow Executor Module

Executes WorkflowStep actions for automation workflows.
"""

from datetime import datetime
from app.database import db
from app.models import Workflow, WorkflowStep, Task, Lead, User
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Step Handlers
# =============================================================================

class StepHandlers:
    """Collection of workflow step action handlers."""
    
    @staticmethod
    def send_email(config: dict, context: dict) -> dict:
        """
        Send an email via the email module.
        
        Config:
            template_id: int - Email template ID
            to_field: str - Context field containing recipient email
            subject_override: str - Optional subject override
        """
        from app.modules.email import send_templated_email
        
        template_id = config.get('template_id')
        to_field = config.get('to_field', 'email')
        recipient = context.get(to_field)
        
        if not recipient:
            return {'success': False, 'error': f'No recipient found in context.{to_field}'}
        
        try:
            send_templated_email(
                template_id=template_id,
                recipient=recipient,
                context=context
            )
            logger.info(f'Workflow email sent to {recipient}')
            return {'success': True, 'recipient': recipient}
        except Exception as e:
            logger.error(f'Workflow email failed: {e}')
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_task(config: dict, context: dict) -> dict:
        """
        Create a task in the task system.
        
        Config:
            title: str - Task title (can contain {{variables}})
            description: str - Task description
            assigned_to_id: int - User ID to assign to
            due_days: int - Days until due
            priority: str - 'low', 'medium', 'high'
        """
        from datetime import timedelta
        
        title = config.get('title', 'Workflow Task')
        description = config.get('description', '')
        assigned_to_id = config.get('assigned_to_id')
        due_days = config.get('due_days', 7)
        priority = config.get('priority', 'medium')
        
        # Replace variables in title
        for key, value in context.items():
            title = title.replace(f'{{{{{key}}}}}', str(value))
            description = description.replace(f'{{{{{key}}}}}', str(value))
        
        task = Task(
            title=title,
            description=description,
            assigned_to_id=assigned_to_id,
            due_date=datetime.utcnow() + timedelta(days=due_days),
            priority=priority,
            status='pending'
        )
        
        db.session.add(task)
        db.session.commit()
        
        logger.info(f'Workflow created task: {task.id}')
        return {'success': True, 'task_id': task.id}
    
    @staticmethod
    def update_lead(config: dict, context: dict) -> dict:
        """
        Update a lead's status or fields.
        
        Config:
            lead_id_field: str - Context field containing lead ID
            status: str - New status
            stage: str - New pipeline stage
            custom_fields: dict - Additional fields to update
        """
        lead_id_field = config.get('lead_id_field', 'lead_id')
        lead_id = context.get(lead_id_field)
        
        if not lead_id:
            return {'success': False, 'error': 'No lead ID in context'}
        
        lead = Lead.query.get(lead_id)
        if not lead:
            return {'success': False, 'error': f'Lead {lead_id} not found'}
        
        # Update fields
        if 'status' in config:
            lead.status = config['status']
        if 'stage' in config:
            lead.stage = config['stage']
        
        # Update custom fields
        custom_fields = config.get('custom_fields', {})
        for key, value in custom_fields.items():
            if hasattr(lead, key):
                setattr(lead, key, value)
        
        db.session.commit()
        logger.info(f'Workflow updated lead: {lead_id}')
        return {'success': True, 'lead_id': lead_id}
    
    @staticmethod
    def send_sms(config: dict, context: dict) -> dict:
        """
        Send SMS using a template.
        
        Config:
            template_id: int - SMS template ID
            phone_field: str - Context field containing phone number
        """
        from app.models import SMSTemplate, SMSConsent
        
        template_id = config.get('template_id')
        phone_field = config.get('phone_field', 'phone')
        phone = context.get(phone_field)
        
        if not phone:
            return {'success': False, 'error': f'No phone in context.{phone_field}'}
        
        # Check consent
        consent = SMSConsent.query.filter_by(phone_number=phone).first()
        if not consent or not consent.is_valid():
            logger.warning(f'No valid SMS consent for {phone}')
            return {'success': False, 'error': 'No valid SMS consent'}
        
        template = SMSTemplate.query.get(template_id)
        if not template:
            return {'success': False, 'error': f'Template {template_id} not found'}
        
        message = template.render(context)
        
        # Log the message (actual SMS sending would integrate with provider)
        logger.info(f'Workflow SMS to {phone}: {message[:50]}...')
        return {'success': True, 'phone': phone, 'message_preview': message[:100]}
    
    @staticmethod
    def webhook(config: dict, context: dict) -> dict:
        """
        Send data to an external webhook.
        
        Config:
            url: str - Webhook URL
            method: str - 'GET' or 'POST'
            headers: dict - Additional headers
            payload_template: dict - Payload with {{variables}}
        """
        import requests
        import json
        
        url = config.get('url')
        method = config.get('method', 'POST').upper()
        headers = config.get('headers', {'Content-Type': 'application/json'})
        payload_template = config.get('payload_template', {})
        
        if not url:
            return {'success': False, 'error': 'No webhook URL configured'}
        
        # Build payload with variable substitution
        payload = {}
        for key, value in payload_template.items():
            if isinstance(value, str):
                for ctx_key, ctx_value in context.items():
                    value = value.replace(f'{{{{{ctx_key}}}}}', str(ctx_value))
            payload[key] = value
        
        try:
            if method == 'GET':
                response = requests.get(url, params=payload, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            logger.info(f'Workflow webhook to {url}: {response.status_code}')
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response': response.text[:200]
            }
        except Exception as e:
            logger.error(f'Workflow webhook failed: {e}')
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def wait(config: dict, context: dict) -> dict:
        """
        Wait/delay action (for async execution).
        
        Config:
            days: int - Days to wait
            hours: int - Hours to wait
        """
        days = config.get('days', 0)
        hours = config.get('hours', 0)
        
        # In real implementation, this would schedule the next step
        # For now, just return the wait duration
        return {
            'success': True,
            'action': 'wait',
            'duration': {'days': days, 'hours': hours}
        }


# Handler registry
STEP_HANDLERS = {
    'send_email': StepHandlers.send_email,
    'create_task': StepHandlers.create_task,
    'update_lead': StepHandlers.update_lead,
    'send_sms': StepHandlers.send_sms,
    'webhook': StepHandlers.webhook,
    'wait': StepHandlers.wait,
}


# =============================================================================
# Executor Functions
# =============================================================================

def execute_step(step: WorkflowStep, context: dict) -> dict:
    """
    Execute a single workflow step.
    
    Args:
        step: WorkflowStep model instance
        context: Dict of data available to the step
    
    Returns:
        Dict with 'success' bool and additional result data
    """
    action_type = step.action_type
    config = step.config or {}
    
    handler = STEP_HANDLERS.get(action_type)
    if not handler:
        logger.warning(f'Unknown step type: {action_type}')
        return {'success': False, 'error': f'Unknown action type: {action_type}'}
    
    try:
        result = handler(config, context)
        return result
    except Exception as e:
        logger.exception(f'Step execution failed: {step.id}')
        return {'success': False, 'error': str(e)}


def run_workflow(workflow: Workflow, context: dict, stop_on_error: bool = True) -> dict:
    """
    Execute all steps in a workflow.
    
    Args:
        workflow: Workflow model instance
        context: Initial context data
        stop_on_error: Stop execution if a step fails
    
    Returns:
        Dict with overall success, steps executed, and results
    """
    steps = WorkflowStep.query.filter_by(workflow_id=workflow.id)\
        .order_by(WorkflowStep.order).all()
    
    results = []
    current_context = dict(context)
    all_success = True
    
    for step in steps:
        result = execute_step(step, current_context)
        results.append({
            'step_id': step.id,
            'action_type': step.action_type,
            'order': step.order,
            'result': result
        })
        
        if not result.get('success'):
            all_success = False
            if stop_on_error:
                break
        
        # Merge result into context for next step
        current_context.update(result)
    
    logger.info(f'Workflow {workflow.id} completed: {len(results)} steps, success={all_success}')
    
    return {
        'success': all_success,
        'workflow_id': workflow.id,
        'steps_executed': len(results),
        'results': results
    }


def trigger_workflow(workflow_id: int, context: dict) -> dict:
    """
    Trigger a workflow by ID.
    
    Args:
        workflow_id: Workflow ID
        context: Context data for the workflow
    
    Returns:
        Workflow execution result
    """
    workflow = Workflow.query.get(workflow_id)
    if not workflow:
        return {'success': False, 'error': 'Workflow not found'}
    
    if not workflow.is_active:
        return {'success': False, 'error': 'Workflow is not active'}
    
    return run_workflow(workflow, context)
