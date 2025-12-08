"""
Phase 15: Email Marketing Module

Core business logic for email marketing platform including:
- Template rendering with variable substitution
- Audience segmentation engine
- Email tracking (pixels, links)
- Email validation
- Bounce classification
- Campaign statistics
"""

import re
import uuid
import hashlib
import base64
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote
from flask import current_app, url_for
from app.database import db


def generate_tracking_token():
    """Generate a unique tracking token for email sends."""
    return uuid.uuid4().hex


def generate_tracking_pixel_url(tracking_token):
    """Generate URL for open tracking pixel."""
    try:
        return url_for('email_tracking.track_open', token=tracking_token, _external=True)
    except RuntimeError:
        # Running outside app context
        return f"/t/o/{tracking_token}"


def generate_click_tracking_url(tracking_token, original_url, link_index=0):
    """Generate URL for click tracking redirect."""
    # Encode the original URL
    encoded_url = base64.urlsafe_b64encode(original_url.encode()).decode()
    try:
        return url_for('email_tracking.track_click', 
                      token=tracking_token, 
                      idx=link_index,
                      url=encoded_url,
                      _external=True)
    except RuntimeError:
        return f"/t/c/{tracking_token}/{link_index}?url={quote(encoded_url)}"


def generate_unsubscribe_url(tracking_token):
    """Generate one-click unsubscribe URL."""
    try:
        return url_for('email_tracking.unsubscribe', token=tracking_token, _external=True)
    except RuntimeError:
        return f"/t/u/{tracking_token}"


def wrap_links_for_tracking(html_content, tracking_token):
    """Replace all links in HTML with tracked redirects.
    
    Args:
        html_content: HTML email content
        tracking_token: Unique token for this email send
        
    Returns:
        Modified HTML with wrapped links
    """
    if not html_content:
        return html_content
    
    # Pattern to match href attributes
    href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
    
    link_index = 0
    
    def replace_link(match):
        nonlocal link_index
        original_url = match.group(1)
        
        # Skip mailto, tel, anchor links, and unsubscribe links
        if original_url.startswith(('mailto:', 'tel:', '#', '{{')) or 'unsubscribe' in original_url.lower():
            return match.group(0)
        
        tracked_url = generate_click_tracking_url(tracking_token, original_url, link_index)
        link_index += 1
        
        return f'href="{tracked_url}"'
    
    return href_pattern.sub(replace_link, html_content)


def inject_tracking_pixel(html_content, tracking_token):
    """Inject tracking pixel into HTML email.
    
    Args:
        html_content: HTML email content
        tracking_token: Unique token for this email send
        
    Returns:
        Modified HTML with tracking pixel
    """
    if not html_content:
        return html_content
    
    pixel_url = generate_tracking_pixel_url(tracking_token)
    pixel_html = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" alt="" />'
    
    # Try to inject before </body> tag
    if '</body>' in html_content.lower():
        return re.sub(r'</body>', f'{pixel_html}</body>', html_content, flags=re.IGNORECASE)
    
    # Otherwise append to end
    return html_content + pixel_html


def prepare_email_for_tracking(html_content, tracking_token):
    """Prepare email HTML with tracking pixel and link wrapping.
    
    Args:
        html_content: Original HTML content
        tracking_token: Unique tracking token
        
    Returns:
        Modified HTML ready for sending
    """
    html = wrap_links_for_tracking(html_content, tracking_token)
    html = inject_tracking_pixel(html, tracking_token)
    
    # Add unsubscribe link if not present
    unsubscribe_url = generate_unsubscribe_url(tracking_token)
    if '{{unsubscribe_url}}' in html:
        html = html.replace('{{unsubscribe_url}}', unsubscribe_url)
    
    return html


# ============================================================================
# Email Validation
# ============================================================================

def validate_email_syntax(email):
    """Validate email address syntax.
    
    Returns: (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    email = email.strip().lower()
    
    # Basic pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    # Check for common issues
    if '..' in email:
        return False, "Invalid email format (consecutive dots)"
    
    if email.startswith('.') or email.endswith('.'):
        return False, "Invalid email format (leading/trailing dot)"
    
    return True, None


def is_disposable_email(email):
    """Check if email is from a known disposable email provider."""
    disposable_domains = {
        'tempmail.com', 'throwaway.email', 'guerrillamail.com', 
        'mailinator.com', '10minutemail.com', 'yopmail.com',
        'temp-mail.org', 'fakeinbox.com', 'getnada.com',
        'discard.email', 'sharklasers.com', 'trashmail.com'
    }
    
    if not email or '@' not in email:
        return False
    
    domain = email.split('@')[1].lower()
    return domain in disposable_domains


def validate_email(email):
    """Full email validation.
    
    Returns: dict with is_valid, syntax_valid, is_disposable, error
    """
    result = {
        'is_valid': False,
        'syntax_valid': False,
        'is_disposable': False,
        'error': None
    }
    
    syntax_valid, error = validate_email_syntax(email)
    result['syntax_valid'] = syntax_valid
    
    if not syntax_valid:
        result['error'] = error
        return result
    
    result['is_disposable'] = is_disposable_email(email)
    
    if result['is_disposable']:
        result['error'] = "Disposable email addresses are not allowed"
        return result
    
    result['is_valid'] = True
    return result


# ============================================================================
# Bounce Classification
# ============================================================================

def classify_bounce(error_message, smtp_code=None):
    """Classify bounce type from error message or SMTP code.
    
    Returns: 'hard', 'soft', or None
    """
    if not error_message and not smtp_code:
        return None
    
    error_lower = (error_message or '').lower()
    
    # Hard bounce indicators
    hard_bounce_patterns = [
        'user unknown', 'mailbox not found', 'recipient rejected',
        'no such user', 'invalid recipient', 'unknown user',
        'does not exist', 'undeliverable', 'mailbox unavailable',
        'address rejected', 'user disabled', 'account disabled'
    ]
    
    # SMTP codes for hard bounces (5xx permanent failures)
    hard_bounce_codes = [550, 551, 552, 553, 554]
    
    if smtp_code and smtp_code in hard_bounce_codes:
        return 'hard'
    
    for pattern in hard_bounce_patterns:
        if pattern in error_lower:
            return 'hard'
    
    # Soft bounce indicators
    soft_bounce_patterns = [
        'mailbox full', 'over quota', 'try again later',
        'temporarily rejected', 'too many connections',
        'service unavailable', 'connection timeout',
        'rate limit', 'temporarily deferred'
    ]
    
    # SMTP codes for soft bounces (4xx temporary failures)
    soft_bounce_codes = [421, 450, 451, 452]
    
    if smtp_code and smtp_code in soft_bounce_codes:
        return 'soft'
    
    for pattern in soft_bounce_patterns:
        if pattern in error_lower:
            return 'soft'
    
    # Default to soft if we can't determine
    return 'soft'


# ============================================================================
# Audience Segmentation
# ============================================================================

def get_audience_members(audience):
    """Get members matching an audience's filter rules.
    
    Args:
        audience: Audience model instance
        
    Returns:
        List of (user, email) tuples
    """
    from app.models import User, AudienceMember, EmailSuppressionList
    
    if not audience.is_dynamic:
        # Static audience - return members from AudienceMember table
        members = AudienceMember.query.filter_by(audience_id=audience.id).all()
        return [(m.user, m.email) for m in members]
    
    # Dynamic audience - build query from filter rules
    query = User.query.filter(User.email.isnot(None))
    
    rules = audience.filter_rules or []
    
    for rule in rules:
        field = rule.get('field')
        operator = rule.get('operator')
        value = rule.get('value')
        
        query = _apply_filter_rule(query, User, field, operator, value)
    
    # Exclude suppressed emails
    suppressed = db.session.query(EmailSuppressionList.email).subquery()
    query = query.filter(~User.email.in_(suppressed))
    
    users = query.all()
    return [(user, user.email) for user in users]


def _apply_filter_rule(query, model, field, operator, value):
    """Apply a single filter rule to a query."""
    if not hasattr(model, field):
        return query
    
    column = getattr(model, field)
    
    if operator == 'equals':
        return query.filter(column == value)
    elif operator == 'not_equals':
        return query.filter(column != value)
    elif operator == 'contains':
        return query.filter(column.ilike(f'%{value}%'))
    elif operator == 'starts_with':
        return query.filter(column.ilike(f'{value}%'))
    elif operator == 'ends_with':
        return query.filter(column.ilike(f'%{value}'))
    elif operator == 'gt':
        return query.filter(column > value)
    elif operator == 'gte':
        return query.filter(column >= value)
    elif operator == 'lt':
        return query.filter(column < value)
    elif operator == 'lte':
        return query.filter(column <= value)
    elif operator == 'is_null':
        return query.filter(column.is_(None))
    elif operator == 'is_not_null':
        return query.filter(column.isnot(None))
    elif operator == 'in_list':
        if isinstance(value, str):
            value = [v.strip() for v in value.split(',')]
        return query.filter(column.in_(value))
    elif operator == 'days_ago_gte':
        # Created at least X days ago
        cutoff = datetime.utcnow() - timedelta(days=int(value))
        return query.filter(column <= cutoff)
    elif operator == 'days_ago_lte':
        # Created within last X days
        cutoff = datetime.utcnow() - timedelta(days=int(value))
        return query.filter(column >= cutoff)
    
    return query


def calculate_audience_count(audience):
    """Calculate and cache audience member count."""
    members = get_audience_members(audience)
    audience.member_count = len(members)
    audience.last_calculated_at = datetime.utcnow()
    db.session.commit()
    return audience.member_count


# ============================================================================
# Campaign Statistics
# ============================================================================

def calculate_campaign_stats(campaign):
    """Calculate and update campaign statistics.
    
    Args:
        campaign: EmailCampaign model instance
        
    Returns:
        Dict with calculated stats
    """
    from app.models import EmailSend
    
    sends = EmailSend.query.filter_by(campaign_id=campaign.id)
    
    total_sent = sends.count()
    total_opened = sends.filter(EmailSend.first_opened_at.isnot(None)).count()
    total_clicked = sends.filter(EmailSend.first_clicked_at.isnot(None)).count()
    total_bounced = sends.filter(EmailSend.bounced == True).count()
    total_unsubscribed = sends.filter(EmailSend.unsubscribed == True).count()
    total_complained = sends.filter(EmailSend.complained == True).count()
    
    # Aggregate counts
    from sqlalchemy import func
    open_sum = db.session.query(func.sum(EmailSend.open_count)).filter(
        EmailSend.campaign_id == campaign.id
    ).scalar() or 0
    
    click_sum = db.session.query(func.sum(EmailSend.click_count)).filter(
        EmailSend.campaign_id == campaign.id
    ).scalar() or 0
    
    # Update campaign
    campaign.sent_count = total_sent
    campaign.unique_open_count = total_opened
    campaign.open_count = open_sum
    campaign.unique_click_count = total_clicked
    campaign.click_count = click_sum
    campaign.bounce_count = total_bounced
    campaign.unsubscribe_count = total_unsubscribed
    campaign.complaint_count = total_complained
    
    db.session.commit()
    
    return {
        'sent': total_sent,
        'opens': open_sum,
        'unique_opens': total_opened,
        'clicks': click_sum,
        'unique_clicks': total_clicked,
        'bounces': total_bounced,
        'unsubscribes': total_unsubscribed,
        'complaints': total_complained,
        'open_rate': round((total_opened / total_sent * 100), 2) if total_sent > 0 else 0,
        'click_rate': round((total_clicked / total_sent * 100), 2) if total_sent > 0 else 0,
        'bounce_rate': round((total_bounced / total_sent * 100), 2) if total_sent > 0 else 0
    }


# ============================================================================
# Suppression List Management
# ============================================================================

def add_to_suppression_list(email, reason, source=None):
    """Add email to suppression list.
    
    Args:
        email: Email address to suppress
        reason: Reason (hard_bounce, unsubscribe, complaint)
        source: Optional source identifier (e.g., campaign_id)
    """
    from app.models import EmailSuppressionList
    
    email = email.lower().strip()
    
    existing = EmailSuppressionList.query.filter_by(email=email).first()
    if existing:
        return existing
    
    suppression = EmailSuppressionList(
        email=email,
        reason=reason,
        source=source
    )
    db.session.add(suppression)
    db.session.commit()
    
    return suppression


def is_email_suppressed(email):
    """Check if an email is on the suppression list."""
    from app.models import EmailSuppressionList
    
    email = email.lower().strip()
    return EmailSuppressionList.query.filter_by(email=email).first() is not None


def remove_from_suppression_list(email):
    """Remove email from suppression list (e.g., for re-subscription)."""
    from app.models import EmailSuppressionList
    
    email = email.lower().strip()
    EmailSuppressionList.query.filter_by(email=email).delete()
    db.session.commit()


# ============================================================================
# Drip Sequence Processing
# ============================================================================

def enroll_in_sequence(sequence, user_id=None, email=None, context_data=None):
    """Enroll a user in a drip sequence.
    
    Args:
        sequence: DripSequence model instance
        user_id: Optional user ID
        email: Email address (required if no user_id)
        context_data: Optional dict of data to pass to templates
        
    Returns:
        SequenceEnrollment instance
    """
    from app.models import SequenceEnrollment, User
    
    if not email and user_id:
        user = User.query.get(user_id)
        if user:
            email = user.email
    
    if not email:
        raise ValueError("Email is required for sequence enrollment")
    
    # Check if already enrolled
    existing = SequenceEnrollment.query.filter_by(
        sequence_id=sequence.id,
        email=email,
        status='active'
    ).first()
    
    if existing:
        return existing
    
    enrollment = SequenceEnrollment(
        sequence_id=sequence.id,
        user_id=user_id,
        email=email,
        current_step=0,
        status='active',
        context_data=context_data or {}
    )
    db.session.add(enrollment)
    
    # Calculate first step time
    first_step = sequence.get_step(1)
    if first_step:
        delay_hours = first_step.get('delay_hours', 0)
        enrollment.next_step_at = datetime.utcnow() + timedelta(hours=delay_hours)
    
    db.session.commit()
    return enrollment


def process_sequence_step(enrollment):
    """Process the next step in a sequence enrollment.
    
    Args:
        enrollment: SequenceEnrollment instance
        
    Returns:
        True if step was processed, False otherwise
    """
    from app.models import EmailTemplate, EmailSend, Task
    
    if enrollment.status != 'active':
        return False
    
    sequence = enrollment.sequence
    current_step = enrollment.current_step + 1
    step_config = sequence.get_step(current_step)
    
    if not step_config:
        # Sequence complete
        enrollment.status = 'completed'
        enrollment.completed_at = datetime.utcnow()
        db.session.commit()
        return False
    
    template_id = step_config.get('template_id')
    if not template_id:
        enrollment.advance_to_next_step()
        db.session.commit()
        return True
    
    template = EmailTemplate.query.get(template_id)
    if not template:
        enrollment.advance_to_next_step()
        db.session.commit()
        return True
    
    # Create task to send the email
    task = Task(
        name='send_sequence_email',
        payload={
            'enrollment_id': enrollment.id,
            'template_id': template_id,
            'email': enrollment.email,
            'context': enrollment.context_data
        }
    )
    db.session.add(task)
    
    # Advance to next step
    enrollment.advance_to_next_step()
    db.session.commit()
    
    return True


def get_due_sequence_enrollments():
    """Get all sequence enrollments due for processing."""
    from app.models import SequenceEnrollment
    
    now = datetime.utcnow()
    return SequenceEnrollment.query.filter(
        SequenceEnrollment.status == 'active',
        SequenceEnrollment.next_step_at <= now
    ).all()
