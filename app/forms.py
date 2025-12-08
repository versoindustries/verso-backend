from flask_wtf import FlaskForm
import os
from flask import current_app
from wtforms import (StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField, TextAreaField, DateField, DecimalField, FieldList, FormField,
                      FileField, FileField, FloatField, SelectMultipleField, HiddenField, ValidationError, EmailField, SubmitField, Form, FloatField, StringField )
from wtforms.fields import DateField, EmailField, TelField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, NumberRange, Regexp, URL
from sqlalchemy import text
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from app.models import Role, Service, Estimator
import pytz
from datetime import datetime, timedelta
from flask_ckeditor import CKEditorField

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=100)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', coerce=int, validators=[DataRequired()])
    accept_tos = BooleanField('I accept the Terms and Conditions', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # Exclude 'admin' and 'blogger' roles from the choices
        self.role.choices = [(role.id, role.name) for role in Role.query.filter(~Role.name.in_(['admin', 'blogger'])).all()]

class AcceptTOSForm(FlaskForm):
    accept_tos = BooleanField('I agree to the Terms and Conditions', validators=[DataRequired()])
    submit = SubmitField('Accept')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SettingsForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    password = PasswordField('Password', validators=[Optional()])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    submit = SubmitField('Update Settings')

class ManageRolesForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(ManageRolesForm, self).__init__(*args, **kwargs)
        self.roles.choices = [(role.id, role.name) for role in Role.query.all()]

    roles = SelectMultipleField(
        'Roles',
        coerce=int,  # Coerce form data to integer, as role IDs are integers
        validators=[DataRequired()]
    )
    submit = SubmitField('Update Roles')


class RoleSelectForm(Form):
    def __init__(self, *args, **kwargs):
        super(RoleSelectForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.all()]

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    is_active = BooleanField('Active User')

    submit = SubmitField('Update')

class EstimateRequestForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    phone = TelField('Phone Number', validators=[DataRequired()])
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    preferred_date = DateField('Preferred Date', format='%Y-%m-%d', validators=[DataRequired()])
    preferred_time = SelectField('Preferred Time', validators=[DataRequired()])
    estimator = SelectField('Select Estimator', coerce=int, validators=[DataRequired()])
    service = SelectField('Select Service', coerce=int, validators=[DataRequired()])  # Renamed from plan_option
    submit = SubmitField('Request Free Estimate')
    
    def __init__(self, *args, **kwargs):
        super(EstimateRequestForm, self).__init__(*args, **kwargs)
        self.service.choices = [(0, 'Please Select a Service')] + [(s.id, s.name) for s in Service.query.order_by('display_order').all()]  # Updated to Service
        self.estimator.choices = [(0, 'Please Select an Estimator')] + [(e.id, e.name) for e in Estimator.query.order_by('name').all()]
        self.preferred_time.choices = [(0, 'Please Select a Time')]

class EstimatorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ServiceOptionForm(FlaskForm):  
    name = StringField('Service Name', validators=[DataRequired()])  
    description = StringField('Service Description', validators=[Optional()])  
    display_order = IntegerField('Display Order', validators=[Optional(), NumberRange(min=0)])
    duration_minutes = IntegerField('Duration (Minutes)', default=60, validators=[Optional(), NumberRange(min=15, max=480)])
    submit = SubmitField('Add Service')

class ContactForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    hp_field = StringField('Confirm Email', validators=[Optional()]) # Honeypot
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class CSRFTokenForm(FlaskForm):
    csrf_token = HiddenField()

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    phone = StringField('Phone')
    password = PasswordField('New Password')
    roles = SelectMultipleField('Roles', coerce=int)
    submit = SubmitField('Update User')

class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    phone = StringField('Phone')
    roles = SelectMultipleField('Roles', coerce=int)
    submit = SubmitField('Create User')

class RoleForm(FlaskForm):
    name = StringField('Role Name', validators=[DataRequired()])
    submit = SubmitField('Save')

def generate_time_choices(start_hour=0, end_hour=23, interval_minutes=30):
    """Generate time choices in HH:MM format for a given interval."""
    choices = []
    current_time = datetime.strptime("00:00", "%H:%M")
    end_time = datetime.strptime("23:59", "%H:%M")
    delta = timedelta(minutes=interval_minutes)
    
    while current_time <= end_time:
        time_str = current_time.strftime("%H:%M")
        choices.append((time_str, time_str))
        current_time += delta
    
    return choices

class BusinessConfigForm(FlaskForm):
    business_start_time = SelectField(
        'Business Start Time (HH:MM, 24-hour format)',
        choices=generate_time_choices(),
        validators=[DataRequired()]
    )
    business_end_time = SelectField(
        'Business End Time (HH:MM, 24-hour format)',
        choices=generate_time_choices(),
        validators=[DataRequired()]
    )
    buffer_time_minutes = SelectField(
        'Buffer Time Between Appointments (Minutes)',
        choices=[(15, '15'), (30, '30'), (45, '45'), (60, '60'), (90, '90'), (120, '120')],
        coerce=int,
        validators=[DataRequired()]
    )
    company_timezone = SelectField(
        'Company Timezone',
        choices=[(tz, tz) for tz in pytz.all_timezones],
        validators=[DataRequired()]
    )
    primary_color = StringField('Primary Color (Hex)', validators=[DataRequired(), Length(max=7)])
    secondary_color = StringField('Secondary Color (Hex)', validators=[DataRequired(), Length(max=7)])
    font_family = StringField('Font Family', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Settings')


# Phase 2: Calendar & Scheduling Forms

class AvailabilityForm(FlaskForm):
    """Form for managing weekly availability for an estimator."""
    day_of_week = SelectField(
        'Day of Week',
        choices=[
            (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
            (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
        ],
        coerce=int,
        validators=[DataRequired()]
    )
    start_time = SelectField('Start Time', choices=generate_time_choices(), validators=[DataRequired()])
    end_time = SelectField('End Time', choices=generate_time_choices(), validators=[DataRequired()])
    submit = SubmitField('Add Availability')

    def validate_end_time(self, end_time):
        """Ensure end time is after start time."""
        if self.start_time.data and end_time.data:
            if self.start_time.data >= end_time.data:
                raise ValidationError('End time must be after start time.')


class AvailabilityExceptionForm(FlaskForm):
    """Form for managing exception dates (holidays, PTO, custom hours)."""
    date = DateField('Date', validators=[DataRequired()])
    is_blocked = BooleanField('Fully Blocked (no appointments)')
    custom_start_time = SelectField('Custom Start Time', choices=[('', '-- Default --')] + generate_time_choices(), validators=[Optional()])
    custom_end_time = SelectField('Custom End Time', choices=[('', '-- Default --')] + generate_time_choices(), validators=[Optional()])
    reason = StringField('Reason', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Add Exception')

    def validate(self, extra_validators=None):
        """Custom validation to ensure custom hours are provided when not blocked."""
        if not super().validate(extra_validators):
            return False
        if not self.is_blocked.data:
            if not self.custom_start_time.data or not self.custom_end_time.data:
                self.custom_start_time.errors.append('Custom hours required when not fully blocked.')
                return False
            if self.custom_start_time.data >= self.custom_end_time.data:
                self.custom_end_time.errors.append('End time must be after start time.')
                return False
        return True


class RescheduleRequestForm(FlaskForm):
    """Form for staff to request appointment reschedule."""
    proposed_date = DateField('Proposed Date', validators=[DataRequired()])
    proposed_time = SelectField('Proposed Time', choices=generate_time_choices(), validators=[DataRequired()])
    reason = TextAreaField('Reason for Reschedule', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Request Reschedule')


class AppointmentNotesForm(FlaskForm):
    """Form for staff to add internal notes to appointments."""
    staff_notes = TextAreaField('Internal Notes', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Save Notes')

class CreatePostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = CKEditorField('Content', validators=[DataRequired()])  # Changed to CKEditorField
    category = StringField('Category (Legacy)', validators=[Optional(), Length(max=100)])
    
    # Phase 3: Enhanced blog fields
    blog_category_id = SelectField('Category', coerce=int, validators=[Optional()])
    tags_input = StringField('Tags (comma separated)', validators=[Optional(), Length(max=500)])
    is_featured = BooleanField('Featured Post', default=False)
    publish_at = DateTimeField('Schedule Publication', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    meta_description = TextAreaField('Meta Description (SEO)', validators=[Optional(), Length(max=300)])
    series_id = SelectField('Post Series', coerce=int, validators=[Optional()])
    series_order = IntegerField('Series Order', default=0, validators=[Optional(), NumberRange(min=0)])
    
    is_published = BooleanField('Publish Post', default=False)
    image = FileField('Post Image', validators=[Optional()])
    submit = SubmitField('Create Post')
    
    def __init__(self, *args, **kwargs):
        super(CreatePostForm, self).__init__(*args, **kwargs)
        from app.models import BlogCategory, PostSeries
        categories = BlogCategory.query.order_by(BlogCategory.name).all()
        self.blog_category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in categories]
        series = PostSeries.query.order_by(PostSeries.title).all()
        self.series_id.choices = [(0, '-- Not Part of Series --')] + [(s.id, s.title) for s in series]

    def validate_title(self, title):
        """Ensure title is not empty after stripping whitespace."""
        if not title.data.strip():
            raise ValidationError('Title cannot be empty.')

    def validate_image(self, image):
        """Validate image file type and size."""
        if image.data:
            allowed_extensions = {'png', 'jpg', 'jpeg'}
            max_size = 5 * 1024 * 1024  # 5MB
            filename = image.data.filename
            extension = os.path.splitext(filename)[1].lower().lstrip('.')
            if extension not in allowed_extensions:
                raise ValidationError('Only PNG, JPG, and JPEG files are allowed.')
            # Check file size
            image.data.seek(0, os.SEEK_END)
            file_size = image.data.tell()
            if file_size > max_size:
                raise ValidationError('Image file size must be less than 5MB.')
            image.data.seek(0)  # Reset file pointer

class EditPostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = CKEditorField('Content', validators=[DataRequired()])
    category = StringField('Category (Legacy)', validators=[Optional(), Length(max=100)])
    
    # Phase 3: Enhanced blog fields
    blog_category_id = SelectField('Category', coerce=int, validators=[Optional()])
    tags_input = StringField('Tags (comma separated)', validators=[Optional(), Length(max=500)])
    is_featured = BooleanField('Featured Post', default=False)
    publish_at = DateTimeField('Schedule Publication', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    meta_description = TextAreaField('Meta Description (SEO)', validators=[Optional(), Length(max=300)])
    series_id = SelectField('Post Series', coerce=int, validators=[Optional()])
    series_order = IntegerField('Series Order', default=0, validators=[Optional(), NumberRange(min=0)])
    
    is_published = BooleanField('Publish Post')
    image = FileField('Post Image', validators=[Optional()])
    submit = SubmitField('Update Post')
    
    def __init__(self, *args, **kwargs):
        super(EditPostForm, self).__init__(*args, **kwargs)
        from app.models import BlogCategory, PostSeries
        categories = BlogCategory.query.order_by(BlogCategory.name).all()
        self.blog_category_id.choices = [(0, '-- Select Category --')] + [(c.id, c.name) for c in categories]
        series = PostSeries.query.order_by(PostSeries.title).all()
        self.series_id.choices = [(0, '-- Not Part of Series --')] + [(s.id, s.title) for s in series]

    def validate_title(self, title):
        """Ensure title is not empty after stripping whitespace."""
        if not title.data.strip():
            raise ValidationError('Title cannot be empty.')

    def validate_image(self, image):
        """Validate image file type and size."""
        if image.data:
            allowed_extensions = {'png', 'jpg', 'jpeg'}
            max_size = 5 * 1024 * 1024  # 5MB
            filename = image.data.filename
            extension = os.path.splitext(filename)[1].lower().lstrip('.')
            if extension not in allowed_extensions:
                raise ValidationError('Only PNG, JPG, and JPEG files are allowed.')
            image.data.seek(0, os.SEEK_END)
            file_size = image.data.tell()
            if file_size > max_size:
                raise ValidationError('Image file size must be less than 5MB.')
            image.data.seek(0)  # Reset file pointer

class PageForm(FlaskForm):
    """Form for creating/editing pages with staging workflow and SEO controls."""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=200)])
    content = CKEditorField('Content', validators=[DataRequired()])
    meta_description = TextAreaField('Meta Description', validators=[Optional(), Length(max=300)])
    
    # Phase 12: Staging workflow
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('published', 'Published')
    ], default='draft', validators=[DataRequired()])
    
    # Phase 12: SEO enhancements
    canonical_url = StringField('Canonical URL', validators=[Optional(), Length(max=500), URL()])
    schema_type = SelectField('Schema.org Type', choices=[
        ('WebPage', 'Web Page'),
        ('AboutPage', 'About Page'),
        ('ContactPage', 'Contact Page'),
        ('FAQPage', 'FAQ Page'),
        ('ItemPage', 'Item Page'),
        ('ProfilePage', 'Profile Page'),
        ('SearchResultsPage', 'Search Results'),
        ('CollectionPage', 'Collection Page')
    ], default='WebPage', validators=[DataRequired()])
    
    # Legacy field - kept for backwards compatibility
    is_published = BooleanField('Publish Page (Legacy)')
    
    # Revision tracking
    revision_note = StringField('Revision Note', validators=[Optional(), Length(max=255)])
    
    submit = SubmitField('Save Page')

    def validate_slug(self, slug):
        """Ensure slug is URL safe and unique (handled in route usually, but good to check format)."""
        # Basic check, mainly rely on uniqueness constraint catch in route
        if not slug.data.replace('-', '').replace('_', '').isalnum():
             raise ValidationError('Slug must contain only letters, numbers, hyphens, and underscores.')


class PageCustomFieldForm(FlaskForm):
    """Form for managing custom fields on pages."""
    field_name = StringField('Field Name', validators=[DataRequired(), Length(max=100)])
    field_type = SelectField('Field Type', choices=[
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Boolean (Yes/No)'),
        ('json', 'JSON')
    ], default='text', validators=[DataRequired()])
    field_value = TextAreaField('Value', validators=[Optional()])
    display_order = IntegerField('Display Order', default=0, validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Save Field')

class LocationForm(FlaskForm):
    name = StringField('Location Name', validators=[DataRequired(), Length(max=100)])
    address = StringField('Address', validators=[Length(max=255)])
    submit = SubmitField('Save Location')

class ApiKeyForm(FlaskForm):
    name = StringField('Key Name', validators=[DataRequired(), Length(max=100)])
    scopes = SelectMultipleField(
        'Scopes',
        choices=[
            ('read:leads', 'Read Leads'),
            ('read:orders', 'Read Orders'),
            ('read:products', 'Read Products')
        ],
        coerce=str,
        validators=[Optional()] # Optional means empty list is allowed? Or DataRequired if we want at least one scope.
    )
    submit = SubmitField('Generate Key')


# ============================================================================
# Phase 3: Blog Platform Enhancement Forms
# ============================================================================

class CommentForm(FlaskForm):
    """Form for submitting comments on blog posts."""
    author_name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    author_email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    content = TextAreaField('Comment', validators=[DataRequired(), Length(min=10, max=2000)])
    parent_id = HiddenField()  # For reply threading
    submit = SubmitField('Post Comment')


class BlogCategoryForm(FlaskForm):
    """Admin form for managing blog categories."""
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('URL Slug', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    parent_id = SelectField('Parent Category', coerce=int, validators=[Optional()])
    display_order = IntegerField('Display Order', default=0, validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Save Category')
    
    def __init__(self, *args, **kwargs):
        super(BlogCategoryForm, self).__init__(*args, **kwargs)
        from app.models import BlogCategory
        categories = BlogCategory.query.order_by(BlogCategory.name).all()
        self.parent_id.choices = [(0, '-- No Parent (Top Level) --')] + [(c.id, c.name) for c in categories]


class TagForm(FlaskForm):
    """Admin form for managing blog tags."""
    name = StringField('Tag Name', validators=[DataRequired(), Length(max=50)])
    slug = StringField('URL Slug', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Save Tag')


class PostSeriesForm(FlaskForm):
    """Admin form for managing post series."""
    title = StringField('Series Title', validators=[DataRequired(), Length(max=200)])
    slug = StringField('URL Slug', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Save Series')


class BlogSearchForm(FlaskForm):
    """Simple search form for the blog."""
    q = StringField('Search', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Search')


class CommentModerationForm(FlaskForm):
    """Form for moderating comments (bulk actions)."""
    action = SelectField('Action', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('spam', 'Mark as Spam'),
        ('delete', 'Delete')
    ], validators=[DataRequired()])
    submit = SubmitField('Apply')


# ============================================================================
# Phase 4: CRM & Lead Management Forms
# ============================================================================

class LeadNoteForm(FlaskForm):
    """Form for adding notes to leads."""
    content = TextAreaField('Note', validators=[DataRequired(), Length(min=1, max=5000)])
    is_pinned = BooleanField('Pin this note', default=False)
    submit = SubmitField('Add Note')


class PipelineStageForm(FlaskForm):
    """Form for managing pipeline stages."""
    name = StringField('Stage Name', validators=[DataRequired(), Length(max=50)])
    pipeline_name = SelectField('Pipeline', choices=[
        ('default', 'Default Pipeline'),
        ('sales', 'Sales Pipeline'),
        ('support', 'Support Pipeline')
    ], validators=[DataRequired()])
    order = IntegerField('Display Order', default=0, validators=[NumberRange(min=0, max=100)])
    color = StringField('Color (Hex)', default='#6c757d', validators=[
        DataRequired(), 
        Length(min=4, max=7),
        Regexp(r'^#[0-9A-Fa-f]{3,6}$', message='Enter a valid hex color code')
    ])
    probability = IntegerField('Conversion Probability (%)', default=0, validators=[NumberRange(min=0, max=100)])
    is_won_stage = BooleanField('This stage marks lead as Won')
    is_lost_stage = BooleanField('This stage marks lead as Lost')
    submit = SubmitField('Save Stage')


class EmailTemplateForm(FlaskForm):
    """Form for creating/editing email templates."""
    name = StringField('Template Name', validators=[DataRequired(), Length(max=100)])
    subject = StringField('Email Subject', validators=[DataRequired(), Length(max=200)])
    body = TextAreaField('Email Body', validators=[DataRequired()], 
                         description='Use {{first_name}}, {{last_name}}, {{email}}, {{company}} as placeholders')
    template_type = SelectField('Template Type', choices=[
        ('general', 'General'),
        ('welcome', 'Welcome'),
        ('follow_up', 'Follow Up'),
        ('won', 'Won Lead'),
        ('lost', 'Lost Lead'),
        ('reminder', 'Reminder')
    ], validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Template')


class LeadAssignForm(FlaskForm):
    """Form for assigning leads to team members."""
    assigned_to_id = SelectField('Assign To', coerce=int, validators=[Optional()])
    submit = SubmitField('Assign')
    
    def __init__(self, *args, **kwargs):
        super(LeadAssignForm, self).__init__(*args, **kwargs)
        from app.models import User, Role
        # Get users with admin or sales roles
        users = User.query.join(User.roles).filter(
            Role.name.in_(['admin', 'employee'])
        ).distinct().all()
        self.assigned_to_id.choices = [(0, '-- Unassigned --')] + [(u.id, f"{u.first_name or ''} {u.last_name or ''} ({u.email})".strip()) for u in users]


class FollowUpReminderForm(FlaskForm):
    """Form for creating follow-up reminders."""
    due_date = DateTimeField('Due Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    note = TextAreaField('Reminder Note', validators=[Optional(), Length(max=500)])
    assigned_to_id = SelectField('Assign To', coerce=int, validators=[Optional()])
    submit = SubmitField('Create Reminder')
    
    def __init__(self, *args, **kwargs):
        super(FollowUpReminderForm, self).__init__(*args, **kwargs)
        from app.models import User, Role
        users = User.query.join(User.roles).filter(
            Role.name.in_(['admin', 'employee'])
        ).distinct().all()
        self.assigned_to_id.choices = [(0, '-- Myself --')] + [(u.id, f"{u.first_name or ''} {u.last_name or ''} ({u.email})".strip()) for u in users]


class LeadScoreRuleForm(FlaskForm):
    """Form for managing lead scoring rules."""
    name = StringField('Rule Name', validators=[DataRequired(), Length(max=100)])
    category = SelectField('Category', choices=[
        ('source', 'Lead Source'),
        ('engagement', 'Engagement'),
        ('fit', 'Customer Fit'),
        ('behavior', 'Behavior')
    ], validators=[DataRequired()])
    condition_type = SelectField('Condition', choices=[
        ('source_equals', 'Source Equals'),
        ('has_phone', 'Has Phone Number'),
        ('message_length_gt', 'Message Length Greater Than'),
        ('email_domain_equals', 'Email Domain Equals'),
        ('status_equals', 'Current Status Equals')
    ], validators=[DataRequired()])
    condition_value = StringField('Value', validators=[Optional(), Length(max=100)])
    points = IntegerField('Points (can be negative)', validators=[DataRequired(), NumberRange(min=-100, max=100)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Rule')


class SendEmailForm(FlaskForm):
    """Form for sending email to lead using a template."""
    template_id = SelectField('Email Template', coerce=int, validators=[DataRequired()])
    custom_subject = StringField('Subject Override', validators=[Optional(), Length(max=200)])
    custom_body = TextAreaField('Additional Message', validators=[Optional()])
    submit = SubmitField('Send Email')
    
    def __init__(self, *args, **kwargs):
        super(SendEmailForm, self).__init__(*args, **kwargs)
        from app.models import EmailTemplate
        templates = EmailTemplate.query.filter_by(is_active=True).all()
        self.template_id.choices = [(0, '-- Select Template --')] + [(t.id, f"{t.name} ({t.template_type})") for t in templates]


# ============================================================================
# Phase 5: Employee Portal & HR Forms
# ============================================================================

class LeaveRequestForm(FlaskForm):
    """Enhanced leave request form with leave types."""
    leave_type = SelectField('Leave Type', choices=[
        ('vacation', 'Vacation'),
        ('sick', 'Sick Leave'),
        ('personal', 'Personal Leave'),
        ('unpaid', 'Unpaid Leave')
    ], validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Submit Request')
    
    def validate_end_date(self, end_date):
        """Ensure end date is on or after start date."""
        if self.start_date.data and end_date.data:
            if end_date.data < self.start_date.data:
                raise ValidationError('End date must be on or after start date.')


class LeaveApprovalForm(FlaskForm):
    """Form for admin/manager to approve or reject leave requests."""
    action = SelectField('Action', choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ], validators=[DataRequired()])
    admin_notes = TextAreaField('Notes (visible to employee)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit Decision')


class LeaveBalanceAdjustForm(FlaskForm):
    """Form for admin to adjust leave balances."""
    user_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    leave_type = SelectField('Leave Type', choices=[
        ('vacation', 'Vacation'),
        ('sick', 'Sick Leave'),
        ('personal', 'Personal Leave'),
        ('unpaid', 'Unpaid Leave')
    ], validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=2020, max=2100)])
    balance_days = FloatField('Total Days Allocated', validators=[DataRequired(), NumberRange(min=0, max=365)])
    carryover_days = FloatField('Carryover Days', default=0, validators=[NumberRange(min=0, max=365)])
    submit = SubmitField('Save Balance')
    
    def __init__(self, *args, **kwargs):
        super(LeaveBalanceAdjustForm, self).__init__(*args, **kwargs)
        from app.models import User
        users = User.query.order_by(User.last_name, User.first_name).all()
        self.user_id.choices = [(u.id, f"{u.first_name or ''} {u.last_name or ''} ({u.email})".strip()) for u in users]


class DocumentShareForm(FlaskForm):
    """Form for sharing encrypted documents."""
    share_type = SelectField('Share With', choices=[
        ('user', 'Specific User'),
        ('role', 'Role')
    ], validators=[DataRequired()])
    shared_with_user_id = SelectField('User', coerce=int, validators=[Optional()])
    shared_with_role = SelectField('Role', choices=[
        ('', '-- Select Role --'),
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('manager', 'Manager')
    ], validators=[Optional()])
    permissions = SelectField('Permissions', choices=[
        ('view', 'View Only'),
        ('download', 'View & Download')
    ], validators=[DataRequired()])
    submit = SubmitField('Share Document')
    
    def __init__(self, *args, **kwargs):
        super(DocumentShareForm, self).__init__(*args, **kwargs)
        from app.models import User
        users = User.query.order_by(User.last_name, User.first_name).all()
        self.shared_with_user_id.choices = [(0, '-- Select User --')] + [(u.id, f"{u.first_name or ''} {u.last_name or ''} ({u.email})".strip()) for u in users]


class DocumentUploadForm(FlaskForm):
    """Enhanced document upload form with category and expiration."""
    title = StringField('Document Title', validators=[DataRequired(), Length(max=200)])
    category = SelectField('Category', choices=[
        ('personal', 'Personal'),
        ('contracts', 'Contracts'),
        ('certifications', 'Certifications/Licenses'),
        ('training', 'Training Materials')
    ], validators=[DataRequired()])
    expires_at = DateField('Expiration Date (for certifications)', validators=[Optional()])
    requires_signature = BooleanField('Requires Acknowledgment Signature')
    file = FileField('File', validators=[DataRequired()])
    submit = SubmitField('Upload Document')


class TimeEntryForm(FlaskForm):
    """Form for clock in/out notes."""
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit')


class EmployeeSearchForm(FlaskForm):
    """Form for searching employee directory by skills."""
    q = StringField('Search Skills', validators=[Optional(), Length(max=100)])
    department = SelectField('Department', validators=[Optional()])
    submit = SubmitField('Search')
    
    def __init__(self, *args, **kwargs):
        super(EmployeeSearchForm, self).__init__(*args, **kwargs)
        from app.models import User
        departments = User.query.with_entities(User.department).filter(User.department.isnot(None)).distinct().all()
        self.department.choices = [('', 'All Departments')] + [(d[0], d[0]) for d in departments if d[0]]


class EmployeeProfileForm(FlaskForm):
    """Enhanced employee profile form with org chart fields."""
    first_name = StringField('First Name', validators=[Optional(), Length(max=100)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=100)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=1000)])
    skills = StringField('Skills (comma separated)', validators=[Optional(), Length(max=255)])
    emergency_contacts = TextAreaField('Emergency Contacts', validators=[Optional()])
    job_title = StringField('Job Title', validators=[Optional(), Length(max=100)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Update Profile')


# ============================================================================
# Phase 22: Registration & User Experience Hardening Forms
# ============================================================================

class OnboardingProfileForm(FlaskForm):
    """Form for onboarding profile completion step."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    phone = TelField('Phone Number', validators=[Optional(), Length(max=20)])
    timezone = SelectField('Timezone', validators=[Optional()])
    bio = TextAreaField('Tell us about yourself', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Continue')
    
    def __init__(self, *args, **kwargs):
        super(OnboardingProfileForm, self).__init__(*args, **kwargs)
        # Common timezones first, then all others
        common_tz = ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 'UTC']
        all_tz = sorted([tz for tz in pytz.common_timezones if tz not in common_tz])
        self.timezone.choices = [('', '-- Select Timezone --')] + [(tz, tz) for tz in common_tz] + [(tz, tz) for tz in all_tz]


class OnboardingPreferencesForm(FlaskForm):
    """Form for onboarding notification preferences step."""
    email_marketing = BooleanField('Receive marketing emails and promotions', default=True)
    email_order_updates = BooleanField('Receive order and shipment updates', default=True)
    email_appointment_reminders = BooleanField('Receive appointment reminders', default=True)
    email_newsletter = BooleanField('Subscribe to our newsletter', default=True)
    submit = SubmitField('Complete Setup')


class UserPreferenceForm(FlaskForm):
    """Form for user preference center (granular settings)."""
    # Email preferences
    email_marketing = BooleanField('Marketing emails and promotions')
    email_order_updates = BooleanField('Order and shipment updates')
    email_appointment_reminders = BooleanField('Appointment reminders')
    email_digest_weekly = BooleanField('Weekly digest summary')
    email_newsletter = BooleanField('Newsletter subscription')
    
    # Push/SMS preferences
    push_enabled = BooleanField('Enable push notifications')
    sms_enabled = BooleanField('Enable SMS notifications')
    
    # Privacy preferences
    show_activity_status = BooleanField('Show my activity status')
    show_profile_publicly = BooleanField('Make my profile publicly visible')
    
    # Display preferences
    theme = SelectField('Theme', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System Default')
    ])
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Español'),
    ])
    
    submit = SubmitField('Save Preferences')


class ResendVerificationForm(FlaskForm):
    """Form for resending email verification."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Resend Verification Email')

