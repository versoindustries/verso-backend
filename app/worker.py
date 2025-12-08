import time
import json
import traceback
import os
import socket
import uuid
import logging
from datetime import datetime, timedelta
from app.models import Task, CronTask, WorkerHeartbeat
from app.database import db
from flask import current_app

# Configure logging based on environment
LOG_FORMAT = os.environ.get('LOG_FORMAT', 'text')  # 'json' or 'text'

if LOG_FORMAT == 'json':
    import logging
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
            }
            if hasattr(record, 'task_id'):
                log_obj['task_id'] = record.task_id
            if record.exc_info:
                log_obj['exception'] = self.formatException(record.exc_info)
            return json.dumps(log_obj)
    
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger('worker')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
else:
    logger = logging.getLogger('worker')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TASK_HANDLERS = {}
BATCH_SIZE = 50  # For newsletter batching
BATCH_PAUSE_SECONDS = 2

def register_task_handler(name):
    def decorator(f):
        TASK_HANDLERS[name] = f
        return f
    return decorator


def get_worker_id():
    """Generate a unique worker ID combining hostname and UUID."""
    hostname = socket.gethostname()
    short_uuid = str(uuid.uuid4())[:8]
    return f"{hostname}-{short_uuid}"


def update_heartbeat(worker_id, tasks_processed=0, tasks_failed=0):
    """Update or create worker heartbeat record."""
    try:
        heartbeat = WorkerHeartbeat.query.filter_by(worker_id=worker_id).first()
        if heartbeat:
            heartbeat.last_heartbeat = datetime.utcnow()
            heartbeat.status = 'running'
            heartbeat.tasks_processed += tasks_processed
            heartbeat.tasks_failed += tasks_failed
        else:
            heartbeat = WorkerHeartbeat(
                worker_id=worker_id,
                last_heartbeat=datetime.utcnow(),
                status='running',
                tasks_processed=0,
                tasks_failed=0,
                hostname=socket.gethostname()
            )
            db.session.add(heartbeat)
        db.session.commit()
    except Exception as e:
        logger.warning(f"Failed to update heartbeat: {e}")
        db.session.rollback()


def mark_worker_stopped(worker_id):
    """Mark worker as stopped on shutdown."""
    try:
        heartbeat = WorkerHeartbeat.query.filter_by(worker_id=worker_id).first()
        if heartbeat:
            heartbeat.status = 'stopped'
            heartbeat.last_heartbeat = datetime.utcnow()
            db.session.commit()
    except Exception:
        pass  # Best effort


def process_due_cron_tasks():
    """Create Task entries for any due cron tasks."""
    try:
        from app.modules.cron_parser import parse_schedule
        
        now = datetime.utcnow()
        due_crons = CronTask.query.filter(
            CronTask.is_active == True,
            (CronTask.next_run == None) | (CronTask.next_run <= now)
        ).all()
        
        for cron in due_crons:
            # Create a Task for this cron job
            task = Task(
                name=cron.handler,
                payload=cron.payload or {},
                priority=5,  # Cron tasks get above-normal priority
            )
            db.session.add(task)
            
            # Update cron task timing
            cron.last_run = now
            cron.next_run = parse_schedule(cron.schedule, now)
            
            logger.info(f"Scheduled cron task: {cron.name} -> handler: {cron.handler}")
        
        if due_crons:
            db.session.commit()
            
    except Exception as e:
        logger.error(f"Error processing cron tasks: {e}")
        db.session.rollback()


def get_next_task():
    """
    Get the next task to process, respecting priority and retry timing.
    
    Order: priority DESC, created_at ASC
    Filter: status='pending' AND (next_retry_at IS NULL OR next_retry_at <= now)
    """
    now = datetime.utcnow()
    
    task = Task.query.filter(
        Task.status == 'pending',
        (Task.next_retry_at == None) | (Task.next_retry_at <= now)
    ).order_by(
        Task.priority.desc(),
        Task.created_at.asc()
    ).first()
    
    return task


def handle_task_failure(task, error_message):
    """
    Handle task failure with retry logic.
    
    - Increment retry_count
    - Calculate next_retry_at with exponential backoff
    - Move to dead_letter if max retries exceeded
    """
    task.retry_count += 1
    task.error = error_message
    
    if task.should_move_to_dead_letter():
        task.status = 'dead_letter'
        task.completed_at = datetime.utcnow()
        logger.warning(f"Task {task.id} moved to dead letter queue after {task.retry_count} retries")
    else:
        # Schedule for retry with exponential backoff
        task.status = 'pending'
        task.next_retry_at = task.calculate_next_retry()
        logger.info(f"Task {task.id} will retry at {task.next_retry_at} (attempt {task.retry_count + 1}/{task.max_retries})")


def run_worker():
    """
    Enhanced main worker loop with:
    - Priority-based task processing
    - Retry logic with exponential backoff
    - Dead letter queue for failed tasks
    - Cron task scheduling
    - Worker heartbeat for observability
    """
    worker_id = get_worker_id()
    logger.info(f"Worker started with ID: {worker_id}")
    
    heartbeat_interval = 0  # Counter for heartbeat updates
    cron_check_interval = 0  # Counter for cron task checks
    
    try:
        while True:
            try:
                # Update heartbeat every 12 iterations (~1 minute at 5s interval)
                heartbeat_interval += 1
                if heartbeat_interval >= 12:
                    update_heartbeat(worker_id)
                    heartbeat_interval = 0
                
                # Check cron tasks every 12 iterations (~1 minute)
                cron_check_interval += 1
                if cron_check_interval >= 12:
                    process_due_cron_tasks()
                    cron_check_interval = 0
                
                # Get the next task (priority-based, respecting retry timing)
                task = get_next_task()
                
                if task:
                    logger.info(f"Processing task {task.id}: {task.name} (priority: {task.priority}, retry: {task.retry_count})")
                    task.status = 'processing'
                    task.started_at = datetime.utcnow()
                    db.session.commit()
                    
                    tasks_processed = 0
                    tasks_failed = 0
                    
                    try:
                        handler = TASK_HANDLERS.get(task.name)
                        if handler:
                            payload = task.payload or {}
                            # Run the handler
                            handler(payload)
                            task.status = 'completed'
                            task.completed_at = datetime.utcnow()
                            tasks_processed = 1
                            logger.info(f"Task {task.id} completed successfully")
                        else:
                            error_msg = f"No handler for task: {task.name}"
                            handle_task_failure(task, error_msg)
                            tasks_failed = 1
                    except Exception as e:
                        error_msg = str(e) + "\n" + traceback.format_exc()
                        logger.error(f"Error processing task {task.id}: {e}")
                        handle_task_failure(task, error_msg)
                        tasks_failed = 1
                    
                    db.session.commit()
                    
                    # Update heartbeat with task counts
                    update_heartbeat(worker_id, tasks_processed, tasks_failed)
                else:
                    # No tasks to process
                    db.session.remove()
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                if "server has gone away" in str(e).lower() or "operationalerror" in str(e).lower():
                    db.session.rollback()
                    db.session.remove()
                time.sleep(5)
                
    except KeyboardInterrupt:
        logger.info("Worker shutting down...")
        mark_worker_stopped(worker_id)

# --- Define Default Tasks Here ---

@register_task_handler('send_email')
def handle_send_email(payload):
    """
    Payload: {
        'recipient': '...',
        'subject': '...',
        'body': '...'
    }
    """
    # Logic to send email would go here (using Flask-Mail)
    # For now, just print it
    print(f"Sending email to {payload.get('recipient')}: {payload.get('subject')}")
    # simulate work
    time.sleep(1)

@register_task_handler('test_task')
def handle_test_task(payload):
    print(f"Test task executed with payload: {payload}")

@register_task_handler('new_lead_notification')
def handle_new_lead_notification(payload):
    """
    Payload: {'submission_id': int}
    """
    from app.models import ContactFormSubmission
    from flask_mail import Message
    from app import mail
    
    submission_id = payload.get('submission_id')
    submission = ContactFormSubmission.query.get(submission_id)
    if not submission:
        print(f"Submission {submission_id} not found.")
        return

    subject = f"New Lead: {submission.first_name} {submission.last_name}"
    body = f"""
    New contact form submission received.
    
    Name: {submission.first_name} {submission.last_name}
    Email: {submission.email}
    Phone: {submission.phone}
    
    Message:
    {submission.message}
    
    Login to CRM to view more details.
    """
    
    msg = Message(subject,
                  recipients=[current_app.config.get('MAIL_DEFAULT_SENDER') or 'admin@example.com'], # fallback
                  body=body)
    
    try:
        mail.send(msg)
        print(f"Notification sent for lead {submission_id}")
    except Exception as e:
        print(f"Failed to send email: {e}")

@register_task_handler('send_newsletter_broadcast')
def handle_send_newsletter_broadcast(payload):
    """
    Payload: {'newsletter_id': int}
    """
    from app.models import Newsletter, ContactFormSubmission, UnsubscribedEmail, User
    from flask_mail import Message
    from app import mail
    from flask import url_for
    
    newsletter_id = payload.get('newsletter_id')
    newsletter = Newsletter.query.get(newsletter_id)
    if not newsletter:
        print(f"Newsletter {newsletter_id} not found.")
        return

    # Gather recipients
    recipients = set()
    
    # 1. Contacts
    contacts = ContactFormSubmission.query.all()
    for c in contacts:
        recipients.add(c.email)
        
    # 2. Users (if desired, maybe filter by role or opt-in?)
    users = User.query.all()
    for u in users:
        recipients.add(u.email)
        
    # Filter unsubscribed
    unsub_list = {u.email for u in UnsubscribedEmail.query.all()}
    final_recipients = recipients - unsub_list
    
    print(f"Broadcasting newsletter {newsletter_id} to {len(final_recipients)} recipients.")
    
    # Send loop (batching might be needed for large lists, but simple loop for now)
    success_count = 0
    with current_app.app_context(): # Ensure we are in context
        for email in final_recipients:
            try:
                # Add unsubscribe link to body (simple append)
                unsub_link = url_for('main_routes.unsubscribe', email=email, _external=True)
                footer = f"\n\n---\nTo unsubscribe, visit: {unsub_link}"
                
                msg = Message(newsletter.subject,
                              recipients=[email],
                              body=newsletter.content + footer,
                              html=(newsletter.full_html or newsletter.content) + f"<br><br><small><a href='{unsub_link}'>Unsubscribe</a></small>")
                mail.send(msg)
                success_count += 1
            except Exception as e:
                print(f"Failed to send to {email}: {e}")
                
    print(f"Broadcast complete. Sent {success_count} emails.")
    newsletter.status = 'sent'
    newsletter.sent_at = datetime.utcnow()
    db.session.commit()


# ============================================================================
# Phase 3: Blog Platform Enhancement Tasks
# ============================================================================

@register_task_handler('publish_scheduled_posts')
def handle_publish_scheduled_posts(payload):
    """
    Publishes posts that are due (publish_at <= now and is_published == False).
    Should be called periodically by a scheduler/cron.
    """
    from app.models import Post
    
    now = datetime.utcnow()
    scheduled_posts = Post.query.filter(
        Post.publish_at != None,
        Post.publish_at <= now,
        Post.is_published == False
    ).all()
    
    published_count = 0
    for post in scheduled_posts:
        try:
            post.is_published = True
            db.session.commit()
            published_count += 1
            print(f"Published scheduled post: {post.title} (ID: {post.id})")
        except Exception as e:
            db.session.rollback()
            print(f"Failed to publish post {post.id}: {e}")
    
    print(f"Scheduled post publishing complete. Published {published_count} posts.")


@register_task_handler('comment_notification')
def handle_comment_notification(payload):
    """
    Sends notification to post author when a new comment is submitted.
    Payload: {'comment_id': int}
    """
    from app.models import Comment
    from flask_mail import Message
    from app import mail
    
    comment_id = payload.get('comment_id')
    comment = Comment.query.get(comment_id)
    if not comment:
        print(f"Comment {comment_id} not found.")
        return
    
    post = comment.post
    author = post.author
    
    if not author or not author.email:
        print(f"Post author has no email for post {post.id}")
        return
    
    subject = f"New comment on: {post.title}"
    body = f"""
    A new comment has been submitted on your blog post "{post.title}".
    
    From: {comment.get_display_name()}
    Status: {comment.status}
    
    Comment:
    {comment.content}
    
    ---
    You can moderate this comment in your dashboard.
    """
    
    msg = Message(subject,
                  recipients=[author.email],
                  body=body)
    
    try:
        mail.send(msg)
        print(f"Comment notification sent to {author.email}")
    except Exception as e:
        print(f"Failed to send comment notification: {e}")


# ============================================================================
# Phase 4: CRM & Lead Management Tasks
# ============================================================================

@register_task_handler('create_user_on_won')
def handle_create_user_on_won(payload):
    """
    Creates a user account when a lead is marked as Won.
    Payload: {
        'lead_type': 'contact' or 'appointment',
        'lead_id': int,
        'email': str,
        'first_name': str,
        'last_name': str,
        'phone': str (optional)
    }
    """
    from app.models import User, Role, LeadActivity
    import secrets
    
    email = payload.get('email')
    if not email:
        print("No email provided for user creation")
        return
    
    # Check if user already exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        print(f"User already exists with email {email}")
        return
    
    # Generate a random password
    temp_password = secrets.token_urlsafe(12)
    
    # Create username from email
    username = email.split('@')[0]
    # Ensure unique username
    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1
    
    try:
        user = User(username=username, email=email, password=temp_password)
        user.first_name = payload.get('first_name', '')
        user.last_name = payload.get('last_name', '')
        user.phone = payload.get('phone', '')
        user.tos_accepted = False  # Will need to accept on first login
        
        # Assign customer role if exists
        customer_role = Role.query.filter_by(name='customer').first()
        if customer_role:
            user.roles.append(customer_role)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"Created user {username} for won lead")
        
        # Log activity
        activity = LeadActivity(
            lead_type=payload.get('lead_type', 'contact'),
            lead_id=payload.get('lead_id'),
            activity_type='user_created',
            description=f"User account created: {username}",
            extra_data={'user_id': user.id, 'temp_password_set': True}
        )
        db.session.add(activity)
        db.session.commit()
        
        # Queue password reset email so user can set their own password
        reset_task = Task(
            name='send_password_reset',
            payload={
                'user_id': user.id,
                'email': email,
                'is_new_account': True
            }
        )
        db.session.add(reset_task)
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Failed to create user for won lead: {e}")


@register_task_handler('send_welcome_email')
def handle_send_welcome_email(payload):
    """
    Sends a welcome email when lead is won.
    Payload: {
        'lead_type': str,
        'lead_id': int,
        'email': str,
        'first_name': str
    }
    """
    from app.models import EmailTemplate
    from flask_mail import Message
    from app import mail
    
    email = payload.get('email')
    first_name = payload.get('first_name', 'Customer')
    
    if not email:
        print("No email provided for welcome message")
        return
    
    # Try to get welcome template
    template = EmailTemplate.query.filter_by(
        template_type='welcome',
        is_active=True
    ).first()
    
    if template:
        context = {
            'first_name': first_name,
            'email': email,
            'company': current_app.config.get('COMPANY_NAME', 'Our Company')
        }
        subject, body = template.render(context)
    else:
        # Default welcome message
        subject = f"Welcome, {first_name}!"
        body = f"""
Dear {first_name},

Thank you for choosing us! We're excited to have you as a customer.

Your account has been created and you'll receive a separate email to set your password.

If you have any questions, don't hesitate to reach out.

Best regards,
The Team
        """
    
    msg = Message(subject,
                  recipients=[email],
                  body=body)
    
    try:
        mail.send(msg)
        print(f"Welcome email sent to {email}")
    except Exception as e:
        print(f"Failed to send welcome email: {e}")


@register_task_handler('stale_lead_reminder')
def handle_stale_lead_reminder(payload):
    """
    Checks for leads with no activity for X days and creates follow-up reminders.
    Should be triggered by a scheduled task.
    Payload: {'days_threshold': int (default 7)}
    """
    from app.models import ContactFormSubmission, LeadActivity, FollowUpReminder
    
    days_threshold = payload.get('days_threshold', 7)
    cutoff = datetime.utcnow() - timedelta(days=days_threshold)
    
    # Get all non-closed leads
    leads = ContactFormSubmission.query.filter(
        ContactFormSubmission.status.notin_(['Won', 'Lost'])
    ).all()
    
    reminder_count = 0
    for lead in leads:
        # Check if there's recent activity
        recent_activity = LeadActivity.query.filter(
            LeadActivity.lead_type == 'contact',
            LeadActivity.lead_id == lead.id,
            LeadActivity.created_at > cutoff
        ).first()
        
        if recent_activity:
            continue  # Lead has recent activity
        
        # Check if reminder already exists
        existing = FollowUpReminder.query.filter_by(
            lead_type='contact',
            lead_id=lead.id,
            status='pending'
        ).first()
        
        if existing:
            continue  # Already has pending reminder
        
        # Create reminder
        reminder = FollowUpReminder(
            lead_type='contact',
            lead_id=lead.id,
            due_date=datetime.utcnow() + timedelta(days=1),
            note=f"Lead has been stale for {days_threshold}+ days. Follow up recommended.",
            assigned_to_id=lead.assigned_to_id
        )
        db.session.add(reminder)
        reminder_count += 1
    
    db.session.commit()
    print(f"Created {reminder_count} stale lead reminders")


@register_task_handler('calculate_lead_scores')
def handle_calculate_lead_scores(payload):
    """
    Batch calculates lead scores based on scoring rules.
    Payload: {'lead_type': 'contact' (optional, defaults to all)}
    """
    from app.models import ContactFormSubmission, LeadScore, LeadScoreRule
    
    lead_type = payload.get('lead_type', 'contact')
    
    if lead_type == 'contact':
        leads = ContactFormSubmission.query.all()
    else:
        # Could extend to appointments
        leads = ContactFormSubmission.query.all()
    
    rules = LeadScoreRule.query.filter_by(is_active=True).all()
    
    for lead in leads:
        total_score = 0
        breakdown = {}
        
        for rule in rules:
            points = 0
            
            # Evaluate rule conditions
            if rule.condition_type == 'source_equals':
                if getattr(lead, 'source', '') == rule.condition_value:
                    points = rule.points
            elif rule.condition_type == 'has_phone':
                if lead.phone and len(lead.phone) > 5:
                    points = rule.points
            elif rule.condition_type == 'message_length_gt':
                try:
                    threshold = int(rule.condition_value or 0)
                    if len(lead.message or '') > threshold:
                        points = rule.points
                except ValueError:
                    pass
            elif rule.condition_type == 'email_domain_equals':
                email_domain = lead.email.split('@')[-1] if '@' in lead.email else ''
                if email_domain == rule.condition_value:
                    points = rule.points
            elif rule.condition_type == 'status_equals':
                if lead.status == rule.condition_value:
                    points = rule.points
            
            if points != 0:
                total_score += points
                breakdown[rule.name] = points
        
        # Upsert lead score
        score_record = LeadScore.query.filter_by(
            lead_type='contact',
            lead_id=lead.id
        ).first()
        
        if score_record:
            score_record.score = total_score
            score_record.score_breakdown = breakdown
            score_record.last_calculated_at = datetime.utcnow()
        else:
            score_record = LeadScore(
                lead_type='contact',
                lead_id=lead.id,
                score=total_score,
                score_breakdown=breakdown
            )
            db.session.add(score_record)
    
    db.session.commit()
    print(f"Calculated scores for {len(leads)} leads")


@register_task_handler('send_password_reset')
def handle_send_password_reset(payload):
    """
    Sends password reset email for new accounts created from won leads.
    Payload: {
        'user_id': int,
        'email': str,
        'is_new_account': bool
    }
    """
    from app.models import User
    from flask_mail import Message
    from app import mail
    from flask import url_for
    
    user_id = payload.get('user_id')
    email = payload.get('email')
    is_new = payload.get('is_new_account', False)
    
    user = User.query.get(user_id)
    if not user:
        print(f"User {user_id} not found for password reset")
        return
    
    # Generate reset token
    token = user.generate_reset_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    if is_new:
        subject = "Set Your Password - Account Created"
        body = f"""
Hello {user.first_name or user.username},

An account has been created for you. Please click the link below to set your password:

{reset_url}

This link will expire in 1 hour.

Best regards,
The Team
        """
    else:
        subject = "Password Reset Request"
        body = f"""
Hello {user.first_name or user.username},

You requested a password reset. Click the link below:

{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.
        """
    
    msg = Message(subject, recipients=[email], body=body)
    
    try:
        mail.send(msg)
        print(f"Password reset email sent to {email}")
    except Exception as e:
        print(f"Failed to send password reset email: {e}")


# ============================================================================
# Phase 5: Employee Portal & HR Tasks
# (Add handlers here if needed)

# ============================================================================
# Phase 10: Automation
# ============================================================================
@register_task_handler('execute_workflow')
def task_execute_workflow(payload):
    from app.modules.automation import handle_execute_workflow
    handle_execute_workflow(payload)

# ============================================================================

@register_task_handler('leave_decision_notification')
def handle_leave_decision_notification(payload):
    """
    Sends email notification when a leave request is approved or rejected.
    Payload: {
        'leave_request_id': int,
        'decision': 'approved' or 'rejected',
        'admin_notes': str (optional)
    }
    """
    from app.models import LeaveRequest
    from flask_mail import Message
    from app import mail
    
    leave_request_id = payload.get('leave_request_id')
    decision = payload.get('decision', 'approved')
    admin_notes = payload.get('admin_notes', '')
    
    leave = LeaveRequest.query.get(leave_request_id)
    if not leave:
        print(f"LeaveRequest {leave_request_id} not found")
        return
    
    user = leave.user
    if not user or not user.email:
        print(f"No email for user on leave request {leave_request_id}")
        return
    
    if decision == 'approved':
        subject = "Leave Request Approved"
        status_text = "Your leave request has been approved."
    else:
        subject = "Leave Request Denied"
        status_text = "Unfortunately, your leave request has been denied."
    
    body = f"""
Hello {user.first_name or user.username},

{status_text}

Leave Details:
- Type: {leave.leave_type.capitalize()}
- Dates: {leave.start_date.strftime('%B %d, %Y')} to {leave.end_date.strftime('%B %d, %Y')}
- Days Requested: {leave.days_requested()}
"""
    
    if admin_notes:
        body += f"""
Manager Notes:
{admin_notes}
"""
    
    body += """
If you have any questions, please contact HR.

Best regards,
The HR Team
"""
    
    msg = Message(subject, recipients=[user.email], body=body)
    
    try:
        mail.send(msg)
        print(f"Leave decision notification sent to {user.email}")
    except Exception as e:
        print(f"Failed to send leave decision notification: {e}")


@register_task_handler('leave_carryover')
def handle_leave_carryover(payload):
    """
    Year-end leave carryover processing.
    Rolls over unused leave balance from previous year based on policy.
    Should be run annually (e.g., Jan 1).
    
    Payload: {
        'year': int (the NEW year to create balances for),
        'max_carryover_days': float (default 5.0),
        'leave_types': list of str (optional, defaults to all)
    }
    """
    from app.models import LeaveBalance, User
    from datetime import datetime
    
    new_year = payload.get('year', datetime.utcnow().year)
    previous_year = new_year - 1
    max_carryover = payload.get('max_carryover_days', 5.0)
    allowed_types = payload.get('leave_types', ['vacation', 'personal'])  # Typically only vacation/personal carry over
    
    # Default allocations for new year
    default_allocations = {
        'vacation': 15.0,
        'sick': 10.0,
        'personal': 3.0,
        'unpaid': 0.0
    }
    
    users = User.query.all()
    processed = 0
    
    for user in users:
        for leave_type in default_allocations.keys():
            # Check if new year balance already exists
            existing = LeaveBalance.query.filter_by(
                user_id=user.id,
                leave_type=leave_type,
                year=new_year
            ).first()
            
            if existing:
                continue  # Already processed
            
            carryover = 0.0
            
            # Get previous year balance for carryover calculation
            if leave_type in allowed_types:
                prev_balance = LeaveBalance.query.filter_by(
                    user_id=user.id,
                    leave_type=leave_type,
                    year=previous_year
                ).first()
                
                if prev_balance:
                    remaining = prev_balance.remaining_days()
                    carryover = min(remaining, max_carryover) if remaining > 0 else 0.0
            
            # Create new year balance
            new_balance = LeaveBalance(
                user_id=user.id,
                leave_type=leave_type,
                year=new_year,
                balance_days=default_allocations[leave_type],
                used_days=0.0,
                carryover_days=carryover
            )
            db.session.add(new_balance)
            processed += 1
    
    db.session.commit()
    print(f"Leave carryover complete. Created {processed} balance entries for year {new_year}.")


@register_task_handler('document_expiry_check')
def handle_document_expiry_check(payload):
    """
    Checks for documents expiring soon and notifies owners/admins.
    Should be run daily.
    
    Payload: {
        'days_ahead': int (default 30, notify if expiring within N days)
    }
    """
    from app.models import EncryptedDocument, User
    from flask_mail import Message
    from app import mail
    from datetime import timedelta
    
    days_ahead = payload.get('days_ahead', 30)
    cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
    
    # Find documents expiring soon
    expiring_docs = EncryptedDocument.query.filter(
        EncryptedDocument.expires_at != None,
        EncryptedDocument.expires_at <= cutoff_date,
        EncryptedDocument.expires_at > datetime.utcnow()
    ).all()
    
    if not expiring_docs:
        print("No expiring documents found.")
        return
    
    # Group by owner
    docs_by_owner = {}
    for doc in expiring_docs:
        if doc.user_id not in docs_by_owner:
            docs_by_owner[doc.user_id] = []
        docs_by_owner[doc.user_id].append(doc)
    
    notifications_sent = 0
    for user_id, docs in docs_by_owner.items():
        user = User.query.get(user_id)
        if not user or not user.email:
            continue
        
        doc_list = "\n".join([
            f"- {doc.title} (expires: {doc.expires_at.strftime('%Y-%m-%d')})"
            for doc in docs
        ])
        
        subject = f"Document Expiration Notice - {len(docs)} document(s) expiring soon"
        body = f"""
Hello {user.first_name or user.username},

The following documents are expiring within the next {days_ahead} days:

{doc_list}

Please review and renew these documents as needed.

Best regards,
The HR Team
"""
        
        msg = Message(subject, recipients=[user.email], body=body)
        
        try:
            mail.send(msg)
            notifications_sent += 1
        except Exception as e:
            print(f"Failed to send expiry notification to {user.email}: {e}")
    
    print(f"Document expiry check complete. Sent {notifications_sent} notifications for {len(expiring_docs)} documents.")


@register_task_handler('leave_balance_accrual')
def handle_leave_balance_accrual(payload):
    """
    Periodic leave balance accrual (for monthly/quarterly accrual policies).
    Should be run monthly.
    
    Payload: {
        'accrual_type': 'monthly' or 'quarterly',
        'leave_type': str (which leave type to accrue, default 'vacation'),
        'days_per_period': float (default 1.25 for monthly = 15/year)
    }
    """
    from app.models import LeaveBalance, User
    
    accrual_type = payload.get('accrual_type', 'monthly')
    leave_type = payload.get('leave_type', 'vacation')
    days_per_period = payload.get('days_per_period', 1.25)
    
    current_year = datetime.utcnow().year
    
    # Get all users with leave balances for this type
    balances = LeaveBalance.query.filter_by(
        leave_type=leave_type,
        year=current_year
    ).all()
    
    accrued_count = 0
    for balance in balances:
        balance.balance_days += days_per_period
        accrued_count += 1
    
    db.session.commit()
    print(f"Leave accrual complete. Added {days_per_period} days to {accrued_count} {leave_type} balances.")


# ============================================================================
# Phase 6: Messaging & Notifications Tasks
# ============================================================================

@register_task_handler('create_notification')
def handle_create_notification(payload):
    """
    Creates an in-app notification for a user.
    Payload: {
        'user_id': int,
        'type': str (message, leave_approved, appointment_reminder, order_placed, etc.),
        'title': str,
        'body': str (optional),
        'link': str (optional),
        'related_type': str (optional),
        'related_id': int (optional)
    }
    """
    from app.models import Notification, NotificationPreference
    
    user_id = payload.get('user_id')
    notification_type = payload.get('type')
    title = payload.get('title')
    
    if not user_id or not notification_type or not title:
        print("create_notification: Missing required fields (user_id, type, title)")
        return
    
    # Check user preferences
    prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
    if prefs and notification_type in (prefs.muted_types or []):
        print(f"Notification type '{notification_type}' is muted for user {user_id}")
        return
    
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=payload.get('body'),
        link=payload.get('link'),
        related_type=payload.get('related_type'),
        related_id=payload.get('related_id')
    )
    db.session.add(notification)
    db.session.commit()
    
    print(f"Created notification for user {user_id}: {title}")


@register_task_handler('send_notification_digest')
def handle_send_notification_digest(payload):
    """
    Sends email digest of unread notifications to users.
    Should be run daily or weekly based on user preferences.
    
    Payload: {
        'frequency': 'daily' or 'weekly'
    }
    """
    from app.models import Notification, NotificationPreference, User
    from flask_mail import Message
    from app import mail
    
    frequency = payload.get('frequency', 'daily')
    
    # Find users with matching digest preferences
    prefs = NotificationPreference.query.filter(
        NotificationPreference.email_digest_enabled == True,
        NotificationPreference.email_digest_frequency == frequency
    ).all()
    
    sent_count = 0
    for pref in prefs:
        user = pref.user
        if not user or not user.email:
            continue
        
        # Get unread notifications that haven't been emailed yet
        notifications = Notification.query.filter(
            Notification.user_id == user.id,
            Notification.is_read == False,
            Notification.email_sent == False
        ).order_by(Notification.created_at.desc()).limit(20).all()
        
        if not notifications:
            continue
        
        # Build digest email
        subject = f"You have {len(notifications)} unread notifications"
        
        body = f"""Hello {user.first_name or user.username},

Here's your {frequency} notification digest:

"""
        for n in notifications:
            body += f"• {n.title}"
            if n.body:
                body += f"\n  {n.body[:100]}..."
            body += "\n\n"
        
        body += """
Log in to view and manage your notifications.

Best regards,
The Verso Team
"""
        
        msg = Message(subject, recipients=[user.email], body=body)
        
        try:
            mail.send(msg)
            sent_count += 1
            
            # Mark notifications as emailed
            for n in notifications:
                n.email_sent = True
            db.session.commit()
            
        except Exception as e:
            print(f"Failed to send digest to {user.email}: {e}")
    
    print(f"Notification digest complete. Sent {sent_count} digest emails ({frequency}).")


@register_task_handler('appointment_reminder_notifications')
def handle_appointment_reminder_notifications(payload):
    """
    Creates reminder notifications for upcoming appointments.
    Should be run hourly or daily.
    
    Payload: {
        'hours_ahead': int (default 24, notify about appointments in next N hours)
    }
    """
    from app.models import Appointment, Notification
    from datetime import timedelta
    
    hours_ahead = payload.get('hours_ahead', 24)
    now = datetime.utcnow()
    cutoff = now + timedelta(hours=hours_ahead)
    
    # Find upcoming appointments
    upcoming = Appointment.query.filter(
        Appointment.date_time >= now,
        Appointment.date_time <= cutoff,
        Appointment.status.in_(['scheduled', 'confirmed'])
    ).all()
    
    notifications_created = 0
    for appt in upcoming:
        # Check if notification already exists for this appointment
        existing = Notification.query.filter_by(
            related_type='appointment',
            related_id=appt.id
        ).first()
        
        if existing:
            continue
        
        # Notify the client
        if appt.client_email:
            from app.models import User
            user = User.query.filter_by(email=appt.client_email).first()
            if user:
                notification = Notification(
                    user_id=user.id,
                    type='appointment_reminder',
                    title=f"Upcoming appointment: {appt.service_type or 'Appointment'}",
                    body=f"Scheduled for {appt.date_time.strftime('%B %d at %I:%M %p')}",
                    link='/user/appointments',
                    related_type='appointment',
                    related_id=appt.id
                )
                db.session.add(notification)
                notifications_created += 1
        
        # Notify assigned estimator
        if appt.estimator_id:
            notification = Notification(
                user_id=appt.estimator_id,
                type='appointment_reminder',
                title=f"Upcoming appointment with {appt.client_name or 'Client'}",
                body=f"Scheduled for {appt.date_time.strftime('%B %d at %I:%M %p')}",
                link='/employee/appointments',
                related_type='appointment',
                related_id=appt.id
            )
            db.session.add(notification)
            notifications_created += 1
    
    db.session.commit()
    print(f"Appointment reminder check complete. Created {notifications_created} notifications.")


@register_task_handler('order_placed_notification')
def handle_order_placed_notification(payload):
    """
    Creates notification when an order is placed.
    Payload: {
        'order_id': int,
        'user_id': int
    }
    """
    from app.models import Order, Notification
    
    order_id = payload.get('order_id')
    user_id = payload.get('user_id')
    
    if not order_id or not user_id:
        print("order_placed_notification: Missing order_id or user_id")
        return
    
    order = Order.query.get(order_id)
    if not order:
        print(f"Order {order_id} not found")
        return
    
    notification = Notification(
        user_id=user_id,
        type='order_placed',
        title=f"Order #{order_id} confirmed",
        body=f"Your order has been placed successfully.",
        link=f'/shop/order/{order_id}',
        related_type='order',
        related_id=order_id
    )
    db.session.add(notification)
    db.session.commit()
    
    print(f"Created order notification for user {user_id}, order {order_id}")


@register_task_handler('leave_decision_notification_in_app')
def handle_leave_decision_notification_in_app(payload):
    """
    Creates in-app notification when leave request is approved/rejected.
    Complements the email notification.
    
    Payload: {
        'leave_request_id': int,
        'decision': 'approved' or 'rejected'
    }
    """
    from app.models import LeaveRequest, Notification
    
    leave_request_id = payload.get('leave_request_id')
    decision = payload.get('decision', 'approved')
    
    leave = LeaveRequest.query.get(leave_request_id)
    if not leave:
        print(f"LeaveRequest {leave_request_id} not found")
        return
    
    notification_type = f'leave_{decision}'
    title = f"Leave request {decision}"
    body = f"Your {leave.leave_type} leave from {leave.start_date.strftime('%b %d')} to {leave.end_date.strftime('%b %d')} has been {decision}."
    
    notification = Notification(
        user_id=leave.user_id,
        type=notification_type,
        title=title,
        body=body,
        link='/employee/leave',
        related_type='leave_request',
        related_id=leave_request_id
    )
    db.session.add(notification)
    db.session.commit()
    
    print(f"Created leave decision notification for user {leave.user_id}")


# ============================================================================
# Phase 9: API & Integrations Tasks
# ============================================================================

@register_task_handler('send_webhook')
def handle_send_webhook(payload):
    """
    Sends an outbound webhook to a configured URL.
    Payload: {
        'webhook_id': int,
        'event': str,
        'data': dict,
        'url': str,
        'secret': str (optional)
    }
    """
    import requests
    import hmac
    import hashlib
    from app.models import Webhook
    
    webhook_id = payload.get('webhook_id')
    event = payload.get('event')
    data = payload.get('data')
    url = payload.get('url')
    secret = payload.get('secret')
    
    if not url:
        print(f"Webhook task missing URL")
        return
    
    # Build the webhook payload
    webhook_payload = {
        'event': event,
        'timestamp': datetime.utcnow().isoformat(),
        'data': data
    }
    payload_json = json.dumps(webhook_payload, default=str)
    payload_bytes = payload_json.encode('utf-8')
    
    # Generate HMAC signature
    signature = None
    if secret:
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
    
    # Prepare headers
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Verso-Webhook/1.0',
        'X-Webhook-Event': event,
        'X-Webhook-Timestamp': datetime.utcnow().isoformat()
    }
    
    if signature:
        headers['X-Webhook-Signature'] = f'sha256={signature}'
    
    try:
        response = requests.post(
            url,
            data=payload_bytes,
            headers=headers,
            timeout=30
        )
        
        # Update webhook record
        if webhook_id:
            webhook = Webhook.query.get(webhook_id)
            if webhook:
                webhook.last_triggered_at = datetime.utcnow()
                webhook.last_status_code = response.status_code
                
                if response.status_code >= 200 and response.status_code < 300:
                    webhook.failure_count = 0
                    print(f"Webhook delivered: {event} to {url} ({response.status_code})")
                else:
                    webhook.failure_count += 1
                    print(f"Webhook failed: {event} to {url} ({response.status_code})")
                    # Disable after 10 consecutive failures
                    if webhook.failure_count >= 10:
                        webhook.is_active = False
                        print(f"Webhook {webhook.name} disabled after 10 failures")
                
                db.session.commit()
        
        if response.status_code < 200 or response.status_code >= 300:
            raise Exception(f"HTTP {response.status_code}")
    
    except requests.exceptions.Timeout:
        print(f"Webhook timeout: {url}")
        if webhook_id:
            webhook = Webhook.query.get(webhook_id)
            if webhook:
                webhook.failure_count += 1
                webhook.last_triggered_at = datetime.utcnow()
                if webhook.failure_count >= 10:
                    webhook.is_active = False
                db.session.commit()
        raise Exception("Webhook request timed out")
    
    except requests.exceptions.RequestException as e:
        print(f"Webhook request error: {url} - {e}")
        if webhook_id:
            webhook = Webhook.query.get(webhook_id)
            if webhook:
                webhook.failure_count += 1
                webhook.last_triggered_at = datetime.utcnow()
                if webhook.failure_count >= 10:
                    webhook.is_active = False
                db.session.commit()
        raise Exception(f"Webhook request failed: {e}")
