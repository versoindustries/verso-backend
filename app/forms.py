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
    password = PasswordField('Password', validators=[DataRequired()])
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
    submit = SubmitField('Add Service')  

class ContactForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
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
    submit = SubmitField('Save Settings')

class CreatePostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = CKEditorField('Content', validators=[DataRequired()])  # Changed to CKEditorField
    category = StringField('Category', validators=[Optional(), Length(max=100)])
    is_published = BooleanField('Publish Post', default=False)
    image = FileField('Post Image', validators=[Optional()])
    submit = SubmitField('Create Post')

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
    content = CKEditorField('Content', validators=[DataRequired()])  # Replace TextAreaField
    category = StringField('Category', validators=[Optional(), Length(max=100)])
    is_published = BooleanField('Publish Post')
    image = FileField('Post Image', validators=[Optional()])
    submit = SubmitField('Update Post')

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