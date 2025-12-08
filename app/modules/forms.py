"""
Forms & Data Collection Platform - Business Logic Module

This module provides the form builder engine with:
- Dynamic form rendering from JSON schema
- Field type registry and validation
- Spam protection (honeypot, rate limiting)
- Submission processing and sanitization
"""

from datetime import datetime, timedelta
from flask import request, current_app
import bleach
import re
import hashlib
from functools import wraps


# ============================================================================
# Field Type Registry
# ============================================================================

FIELD_TYPES = {
    'text': {
        'label': 'Text Input',
        'html_type': 'text',
        'validators': ['required', 'min_length', 'max_length', 'pattern'],
    },
    'email': {
        'label': 'Email',
        'html_type': 'email',
        'validators': ['required', 'email'],
    },
    'phone': {
        'label': 'Phone Number',
        'html_type': 'tel',
        'validators': ['required', 'phone'],
    },
    'number': {
        'label': 'Number',
        'html_type': 'number',
        'validators': ['required', 'min', 'max'],
    },
    'date': {
        'label': 'Date',
        'html_type': 'date',
        'validators': ['required', 'min_date', 'max_date'],
    },
    'datetime': {
        'label': 'Date & Time',
        'html_type': 'datetime-local',
        'validators': ['required'],
    },
    'textarea': {
        'label': 'Text Area',
        'html_type': 'textarea',
        'validators': ['required', 'min_length', 'max_length'],
    },
    'select': {
        'label': 'Dropdown',
        'html_type': 'select',
        'validators': ['required'],
    },
    'multi_select': {
        'label': 'Multi-Select',
        'html_type': 'select',
        'multiple': True,
        'validators': ['required', 'min_selections', 'max_selections'],
    },
    'checkbox': {
        'label': 'Checkbox',
        'html_type': 'checkbox',
        'validators': ['required'],
    },
    'checkbox_group': {
        'label': 'Checkbox Group',
        'html_type': 'checkbox',
        'multiple': True,
        'validators': ['required', 'min_selections'],
    },
    'radio': {
        'label': 'Radio Buttons',
        'html_type': 'radio',
        'validators': ['required'],
    },
    'file': {
        'label': 'File Upload',
        'html_type': 'file',
        'validators': ['required', 'file_types', 'max_size'],
    },
    'signature': {
        'label': 'Signature',
        'html_type': 'hidden',  # Uses canvas
        'validators': ['required'],
    },
    'rating': {
        'label': 'Rating',
        'html_type': 'radio',
        'validators': ['required', 'min', 'max'],
    },
    'range': {
        'label': 'Range Slider',
        'html_type': 'range',
        'validators': ['required', 'min', 'max'],
    },
    'hidden': {
        'label': 'Hidden Field',
        'html_type': 'hidden',
        'validators': [],
    },
    'heading': {
        'label': 'Section Heading',
        'html_type': None,  # Display only
        'validators': [],
    },
    'paragraph': {
        'label': 'Paragraph Text',
        'html_type': None,  # Display only
        'validators': [],
    },
}


# ============================================================================
# Validation Engine
# ============================================================================

class ValidationError(Exception):
    """Custom validation error."""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class FormValidator:
    """Validates form submissions against schema."""
    
    def __init__(self, form_definition):
        self.form = form_definition
        self.errors = {}
    
    def validate(self, data):
        """
        Validate submission data against form schema.
        
        Returns (is_valid, errors_dict)
        """
        self.errors = {}
        fields_schema = self.form.fields_schema or []
        
        for field_def in fields_schema:
            field_name = field_def.get('name')
            field_type = field_def.get('type')
            is_required = field_def.get('required', False)
            validation = field_def.get('validation', {})
            
            value = data.get(field_name)
            
            # Skip display-only fields
            if field_type in ('heading', 'paragraph'):
                continue
            
            # Required check
            if is_required and not self._has_value(value):
                self.errors[field_name] = 'This field is required.'
                continue
            
            # Skip validation for empty optional fields
            if not self._has_value(value):
                continue
            
            # Type-specific validation
            error = self._validate_field(field_name, field_type, value, validation)
            if error:
                self.errors[field_name] = error
        
        return len(self.errors) == 0, self.errors
    
    def _has_value(self, value):
        """Check if a value is present (not empty)."""
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == '':
            return False
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False
        return True
    
    def _validate_field(self, name, field_type, value, validation):
        """Validate a single field value."""
        
        # Email validation
        if field_type == 'email':
            if not self._is_valid_email(value):
                return 'Please enter a valid email address.'
        
        # Phone validation
        elif field_type == 'phone':
            if not self._is_valid_phone(value):
                return 'Please enter a valid phone number.'
        
        # Number validation
        elif field_type in ('number', 'range'):
            try:
                num_value = float(value)
                if 'min' in validation and num_value < validation['min']:
                    return f'Value must be at least {validation["min"]}.'
                if 'max' in validation and num_value > validation['max']:
                    return f'Value must be at most {validation["max"]}.'
            except (ValueError, TypeError):
                return 'Please enter a valid number.'
        
        # Rating validation
        elif field_type == 'rating':
            try:
                rating = int(value)
                scale = validation.get('scale', 5)
                if rating < 1 or rating > scale:
                    return f'Rating must be between 1 and {scale}.'
            except (ValueError, TypeError):
                return 'Please select a rating.'
        
        # Text length validation
        elif field_type in ('text', 'textarea'):
            str_value = str(value)
            if 'min_length' in validation and len(str_value) < validation['min_length']:
                return f'Must be at least {validation["min_length"]} characters.'
            if 'max_length' in validation and len(str_value) > validation['max_length']:
                return f'Must be at most {validation["max_length"]} characters.'
            if 'pattern' in validation:
                if not re.match(validation['pattern'], str_value):
                    return validation.get('pattern_message', 'Invalid format.')
        
        # Multi-select validation
        elif field_type in ('multi_select', 'checkbox_group'):
            if not isinstance(value, list):
                value = [value]
            if 'min_selections' in validation and len(value) < validation['min_selections']:
                return f'Select at least {validation["min_selections"]} options.'
            if 'max_selections' in validation and len(value) > validation['max_selections']:
                return f'Select at most {validation["max_selections"]} options.'
        
        # Date validation
        elif field_type == 'date':
            try:
                date_value = datetime.strptime(value, '%Y-%m-%d').date()
                if 'min_date' in validation:
                    min_date = datetime.strptime(validation['min_date'], '%Y-%m-%d').date()
                    if date_value < min_date:
                        return f'Date must be on or after {min_date.strftime("%B %d, %Y")}.'
                if 'max_date' in validation:
                    max_date = datetime.strptime(validation['max_date'], '%Y-%m-%d').date()
                    if date_value > max_date:
                        return f'Date must be on or before {max_date.strftime("%B %d, %Y")}.'
            except ValueError:
                return 'Please enter a valid date.'
        
        return None
    
    def _is_valid_email(self, email):
        """Basic email validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(email)))
    
    def _is_valid_phone(self, phone):
        """Basic phone validation (allows various formats)."""
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.\+]', '', str(phone))
        # Should have 10-15 digits
        return bool(re.match(r'^\d{10,15}$', cleaned))


# ============================================================================
# Spam Protection
# ============================================================================

# In-memory rate limiting (for production, use Redis)
_rate_limit_cache = {}


def check_honeypot(data, honeypot_field='hp_field'):
    """
    Check if honeypot field was filled (indicates bot).
    
    Returns True if spam is detected.
    """
    return bool(data.get(honeypot_field))


def check_rate_limit(ip_address, form_id, max_submissions=5, window_minutes=60):
    """
    Check if IP has exceeded submission rate limit.
    
    Returns True if rate limit exceeded.
    """
    if not ip_address:
        return False
    
    key = f"{ip_address}:{form_id}"
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)
    
    # Clean old entries
    if key in _rate_limit_cache:
        _rate_limit_cache[key] = [
            ts for ts in _rate_limit_cache[key] 
            if ts > window_start
        ]
    else:
        _rate_limit_cache[key] = []
    
    # Check limit
    if len(_rate_limit_cache[key]) >= max_submissions:
        return True
    
    # Record this submission
    _rate_limit_cache[key].append(now)
    return False


def calculate_spam_score(data, ip_address=None):
    """
    Calculate a spam score (0-100) for a submission.
    
    Higher score = more likely spam.
    """
    score = 0
    
    # Check for common spam patterns
    text_content = ' '.join(str(v) for v in data.values() if isinstance(v, str))
    
    # Links in submission (common in spam)
    url_pattern = r'https?://\S+'
    url_count = len(re.findall(url_pattern, text_content))
    score += min(url_count * 15, 45)  # Max 45 points for URLs
    
    # All caps text
    if text_content.isupper() and len(text_content) > 20:
        score += 10
    
    # Common spam keywords
    spam_keywords = ['viagra', 'casino', 'lottery', 'winner', 'bitcoin', 'crypto', 'free money']
    for keyword in spam_keywords:
        if keyword.lower() in text_content.lower():
            score += 20
    
    # Very short submission time (filled too fast - likely bot)
    # This would need to be tracked with a hidden timestamp field
    
    # Submission from known problematic IP ranges (would need IP database)
    
    return min(score, 100)


# ============================================================================
# Submission Processing
# ============================================================================

def sanitize_submission(data, fields_schema):
    """
    Sanitize submission data.
    
    - Strips HTML from text fields
    - Validates and cleans file references
    - Removes unexpected fields
    """
    sanitized = {}
    allowed_fields = {f['name'] for f in (fields_schema or [])}
    
    for field_name, value in data.items():
        # Skip fields not in schema
        if field_name not in allowed_fields:
            continue
        
        # Find field definition
        field_def = next((f for f in fields_schema if f['name'] == field_name), None)
        if not field_def:
            continue
        
        field_type = field_def.get('type')
        
        # Sanitize based on type
        if field_type in ('text', 'textarea', 'email', 'phone'):
            # Strip HTML tags
            sanitized[field_name] = bleach.clean(str(value).strip(), tags=[], strip=True)
        
        elif field_type in ('number', 'range', 'rating'):
            try:
                if '.' in str(value):
                    sanitized[field_name] = float(value)
                else:
                    sanitized[field_name] = int(value)
            except (ValueError, TypeError):
                sanitized[field_name] = None
        
        elif field_type in ('select', 'radio'):
            sanitized[field_name] = str(value) if value else None
        
        elif field_type in ('multi_select', 'checkbox_group'):
            if isinstance(value, list):
                sanitized[field_name] = [str(v) for v in value]
            else:
                sanitized[field_name] = [str(value)] if value else []
        
        elif field_type == 'checkbox':
            sanitized[field_name] = value in (True, 'true', 'True', '1', 'on', 'yes')
        
        elif field_type == 'date':
            sanitized[field_name] = str(value) if value else None
        
        elif field_type == 'hidden':
            sanitized[field_name] = str(value) if value else None
        
        elif field_type == 'signature':
            # Base64 encoded signature data
            sanitized[field_name] = str(value) if value else None
        
        else:
            sanitized[field_name] = value
    
    return sanitized


def extract_utm_params(request_args):
    """Extract UTM parameters from request query string."""
    utm_keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
    return {key: request_args.get(key) for key in utm_keys if request_args.get(key)}


def get_client_ip():
    """Get client IP address, handling proxies."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers['X-Real-IP']
    return request.remote_addr


def hash_ip(ip_address):
    """Hash IP address for privacy-preserving storage."""
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode()).hexdigest()[:32]


# ============================================================================
# Form Rendering Helpers
# ============================================================================

def render_field_html(field_def, value=None, errors=None):
    """
    Generate HTML for a single form field.
    
    This is used by the Jinja macro but can also be called directly.
    """
    field_type = field_def.get('type')
    field_name = field_def.get('name')
    label = field_def.get('label', field_name)
    required = field_def.get('required', False)
    placeholder = field_def.get('placeholder', '')
    options = field_def.get('options', [])
    validation = field_def.get('validation', {})
    css_class = field_def.get('css_class', '')
    description = field_def.get('description', '')
    
    # Get HTML input type
    type_info = FIELD_TYPES.get(field_type, FIELD_TYPES['text'])
    html_type = type_info.get('html_type')
    
    html_parts = []
    
    # Display-only fields
    if field_type == 'heading':
        return f'<h3 class="form-heading {css_class}">{label}</h3>'
    elif field_type == 'paragraph':
        return f'<p class="form-paragraph {css_class}">{description}</p>'
    
    # Field wrapper
    html_parts.append(f'<div class="form-group {css_class}" id="field-{field_name}-wrapper">')
    
    # Label
    req_mark = ' <span class="text-danger">*</span>' if required else ''
    if field_type not in ('checkbox', 'hidden'):
        html_parts.append(f'<label for="{field_name}" class="form-label">{label}{req_mark}</label>')
    
    # Description
    if description and field_type not in ('hidden',):
        html_parts.append(f'<small class="form-text text-muted">{description}</small>')
    
    # Input element based on type
    if field_type == 'textarea':
        rows = validation.get('rows', 4)
        html_parts.append(
            f'<textarea name="{field_name}" id="{field_name}" class="form-control" '
            f'rows="{rows}" placeholder="{placeholder}"'
            f'{" required" if required else ""}>{value or ""}</textarea>'
        )
    
    elif field_type in ('select', 'multi_select'):
        multiple = 'multiple' if field_type == 'multi_select' else ''
        html_parts.append(f'<select name="{field_name}" id="{field_name}" class="form-select" {multiple}>')
        if not required:
            html_parts.append('<option value="">-- Select --</option>')
        for opt in options:
            opt_val = opt.get('value', opt) if isinstance(opt, dict) else opt
            opt_label = opt.get('label', opt) if isinstance(opt, dict) else opt
            selected = 'selected' if value == opt_val else ''
            html_parts.append(f'<option value="{opt_val}" {selected}>{opt_label}</option>')
        html_parts.append('</select>')
    
    elif field_type in ('radio', 'checkbox_group'):
        html_parts.append(f'<div class="form-check-group">')
        for opt in options:
            opt_val = opt.get('value', opt) if isinstance(opt, dict) else opt
            opt_label = opt.get('label', opt) if isinstance(opt, dict) else opt
            input_type = 'radio' if field_type == 'radio' else 'checkbox'
            checked = 'checked' if value == opt_val or (isinstance(value, list) and opt_val in value) else ''
            html_parts.append(f'''
                <div class="form-check">
                    <input type="{input_type}" name="{field_name}" id="{field_name}_{opt_val}" 
                           value="{opt_val}" class="form-check-input" {checked}>
                    <label class="form-check-label" for="{field_name}_{opt_val}">{opt_label}</label>
                </div>
            ''')
        html_parts.append('</div>')
    
    elif field_type == 'checkbox':
        checked = 'checked' if value else ''
        html_parts.append(f'''
            <div class="form-check">
                <input type="checkbox" name="{field_name}" id="{field_name}" 
                       value="1" class="form-check-input" {checked}{" required" if required else ""}>
                <label class="form-check-label" for="{field_name}">{label}{req_mark}</label>
            </div>
        ''')
    
    elif field_type == 'rating':
        scale = validation.get('scale', 5)
        html_parts.append('<div class="rating-input">')
        for i in range(1, scale + 1):
            checked = 'checked' if value == i else ''
            html_parts.append(f'''
                <input type="radio" name="{field_name}" id="{field_name}_{i}" value="{i}" {checked}>
                <label for="{field_name}_{i}"><i class="bi bi-star-fill"></i></label>
            ''')
        html_parts.append('</div>')
    
    elif field_type == 'range':
        min_val = validation.get('min', 0)
        max_val = validation.get('max', 100)
        step = validation.get('step', 1)
        html_parts.append(f'''
            <input type="range" name="{field_name}" id="{field_name}" 
                   class="form-range" min="{min_val}" max="{max_val}" step="{step}"
                   value="{value or min_val}">
            <output for="{field_name}">{value or min_val}</output>
        ''')
    
    elif field_type == 'file':
        accept = ','.join(validation.get('allowed_types', []))
        html_parts.append(f'''
            <input type="file" name="{field_name}" id="{field_name}" 
                   class="form-control" accept="{accept}"{" required" if required else ""}>
        ''')
    
    else:
        # Standard input types (text, email, phone, number, date, etc.)
        attrs = [
            f'type="{html_type}"',
            f'name="{field_name}"',
            f'id="{field_name}"',
            'class="form-control"',
            f'placeholder="{placeholder}"',
        ]
        if value:
            attrs.append(f'value="{value}"')
        if required:
            attrs.append('required')
        if 'min_length' in validation:
            attrs.append(f'minlength="{validation["min_length"]}"')
        if 'max_length' in validation:
            attrs.append(f'maxlength="{validation["max_length"]}"')
        if 'min' in validation:
            attrs.append(f'min="{validation["min"]}"')
        if 'max' in validation:
            attrs.append(f'max="{validation["max"]}"')
        if 'pattern' in validation:
            attrs.append(f'pattern="{validation["pattern"]}"')
        
        html_parts.append(f'<input {" ".join(attrs)}>')
    
    # Error message
    if errors and field_name in errors:
        html_parts.append(f'<div class="invalid-feedback d-block">{errors[field_name]}</div>')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)


def generate_form_html(form_definition, data=None, errors=None, include_wrapper=True):
    """
    Generate complete form HTML from definition.
    """
    parts = []
    
    if include_wrapper:
        action_url = f'/forms/{form_definition.slug}/submit'
        parts.append(f'<form method="POST" action="{action_url}" class="dynamic-form" enctype="multipart/form-data">')
        parts.append('<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">')
        
        # Honeypot field (hidden from users, visible to bots)
        if (form_definition.settings or {}).get('honeypot', True):
            parts.append('''
                <div style="display:none;" aria-hidden="true">
                    <label for="hp_field">Leave this empty</label>
                    <input type="text" name="hp_field" id="hp_field" tabindex="-1" autocomplete="off">
                </div>
            ''')
    
    # Render each field
    for field_def in (form_definition.fields_schema or []):
        field_name = field_def.get('name')
        field_value = (data or {}).get(field_name)
        parts.append(render_field_html(field_def, value=field_value, errors=errors))
    
    if include_wrapper:
        submit_text = (form_definition.settings or {}).get('submit_text', 'Submit')
        parts.append(f'''
            <div class="form-group mt-4">
                <button type="submit" class="btn btn-primary">{submit_text}</button>
            </div>
        ''')
        parts.append('</form>')
    
    return '\n'.join(parts)


# ============================================================================
# Integration Handlers
# ============================================================================

def process_integrations(form, submission):
    """
    Process all active integrations for a form submission.
    
    Returns list of (integration, success, error) tuples.
    """
    results = []
    
    for integration in form.integrations.filter_by(is_active=True):
        try:
            success = _execute_integration(integration, submission)
            integration.record_trigger()
            results.append((integration, success, None))
        except Exception as e:
            integration.record_trigger(error=str(e))
            results.append((integration, False, str(e)))
            current_app.logger.error(f"Integration {integration.id} failed: {e}")
    
    return results


def _execute_integration(integration, submission):
    """Execute a single integration."""
    from app.models import Lead, ContactFormSubmission
    from app.database import db
    import requests
    
    config = integration.config or {}
    field_mapping = integration.field_mapping or {}
    
    # Map submission data to integration fields
    mapped_data = {}
    for target_field, source_field in field_mapping.items():
        mapped_data[target_field] = submission.get_field_value(source_field)
    
    if integration.integration_type == 'webhook':
        # POST to webhook URL
        url = config.get('url')
        if not url:
            return False
        
        headers = config.get('headers', {'Content-Type': 'application/json'})
        method = config.get('method', 'POST').upper()
        
        payload = {
            'form_id': submission.form_id,
            'form_name': submission.form.name,
            'submission_id': submission.id,
            'submitted_at': submission.submitted_at.isoformat(),
            'data': submission.data,
            'mapped_data': mapped_data,
        }
        
        response = requests.request(method, url, json=payload, headers=headers, timeout=10)
        return response.status_code < 400
    
    elif integration.integration_type == 'crm_lead':
        # Create CRM lead
        lead = Lead(
            first_name=mapped_data.get('first_name', ''),
            last_name=mapped_data.get('last_name', ''),
            email=mapped_data.get('email', ''),
            phone=mapped_data.get('phone', ''),
            company=mapped_data.get('company', ''),
            source=f'form:{submission.form.slug}',
            notes=str(submission.data),
        )
        db.session.add(lead)
        db.session.commit()
        return True
    
    elif integration.integration_type == 'email_notify':
        # Send email notification
        from app.modules.email_marketing import send_transactional_email
        
        recipients = config.get('recipients', [])
        subject = config.get('subject', f'New form submission: {submission.form.name}')
        
        # Build email body
        body_lines = [f'<h2>New submission from {submission.form.name}</h2>']
        for key, value in submission.data.items():
            body_lines.append(f'<p><strong>{key}:</strong> {value}</p>')
        body_html = '\n'.join(body_lines)
        
        for recipient in recipients:
            send_transactional_email(recipient, subject, body_html)
        
        return True
    
    return False
