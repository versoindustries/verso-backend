from datetime import datetime
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
import flask
from flask import current_app
import enum
from .extensions import bcrypt
import sqlalchemy
from app.database import db
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_utils import ChoiceType
import json
from sqlalchemy import JSON, event, Index
from sqlalchemy.sql import func
from sqlalchemy.ext.mutable import MutableList
import pytz


user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(120), nullable=True)
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    phone = db.Column(db.String(20), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    tos_accepted = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # For bulk user activation/deactivation
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    skills = db.Column(db.String(255), nullable=True)
    skills = db.Column(db.String(255), nullable=True)
    emergency_contacts = db.Column(db.Text, nullable=True)  # JSON or text description
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    location = db.relationship('Location', backref='users')
    
    # Phase 5: Employee Portal enhancements
    reports_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    profile_photo_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)
    
    # Self-referential relationship for org chart
    reports_to = db.relationship('User', remote_side='User.id', backref=db.backref('direct_reports', lazy='dynamic'))
    profile_photo = db.relationship('Media', foreign_keys=[profile_photo_id])
    
    # Phase 22: Registration & UX Hardening
    oauth_provider = db.Column(db.String(20), nullable=True)  # 'google', 'apple', 'microsoft', None
    oauth_id = db.Column(db.String(255), nullable=True)  # Provider's unique user ID
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    email_verification_sent_at = db.Column(db.DateTime, nullable=True)
    profile_completion_score = db.Column(db.Integer, default=0)
    onboarding_completed = db.Column(db.Boolean, default=False)
    onboarding_completed_at = db.Column(db.DateTime, nullable=True)
    last_activity_at = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)  # Track last login time for admin dashboard KPIs
    timezone = db.Column(db.String(50), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)  # Use the method to hash the password

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expiration=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id': self.id}, salt='password-reset-salt')

    @staticmethod
    def confirm_reset_token(token, expiration=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='password-reset-salt', max_age=expiration)
        except:
            return None
        return User.query.get(data['id'])

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

    def add_role(self, role):
        if not self.has_role(role.name):
            self.roles.append(role)

    def remove_role(self, role):
        if self.has_role(role.name):
            self.roles.remove(role)

    # Phase 22: Email Verification Methods
    def generate_email_verification_token(self):
        """Generate a token for email verification."""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        self.email_verification_token = s.dumps({'id': self.id, 'email': self.email}, salt='email-verify-salt')
        self.email_verification_sent_at = datetime.utcnow()
        return self.email_verification_token
    
    @staticmethod
    def verify_email_token(token, expiration=86400):
        """Verify an email verification token (default 24 hours expiration)."""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='email-verify-salt', max_age=expiration)
        except:
            return None
        return User.query.get(data['id'])
    
    def calculate_profile_completion_score(self):
        """Calculate profile completion percentage."""
        fields = [
            (self.first_name, 10),
            (self.last_name, 10),
            (self.phone, 15),
            (self.bio, 10),
            (self.timezone, 10),
            (self.avatar_url or (self.profile_photo_id is not None), 15),
            (self.email_verified, 20),
            (self.onboarding_completed, 10),
        ]
        score = sum(weight for value, weight in fields if value)
        self.profile_completion_score = score
        return score
    
    def log_activity(self, activity_type, title, description=None, related_type=None, related_id=None, icon='fa-circle'):
        """Log a user activity to the activity feed."""
        from app.models import UserActivity
        activity = UserActivity(
            user_id=self.id,
            activity_type=activity_type,
            title=title,
            description=description,
            related_type=related_type,
            related_id=related_id,
            icon=icon
        )
        db.session.add(activity)
        self.last_activity_at = datetime.utcnow()
        return activity

    def __repr__(self):
        return f'<User username={self.username} email={self.email}>'
    
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship('User', secondary=user_roles, back_populates='roles')

    def __repr__(self):
        return f'<Role {self.name}>'

class Service(db.Model):
    __tablename__ = 'service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0)
    duration_minutes = db.Column(db.Integer, default=60)  # Phase 2: Service duration

class Appointment(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='New') # New, Contacted, Qualified, Won, Lost
    notes = db.Column(db.Text, nullable=True)
    preferred_date_time = db.Column(db.DateTime, nullable=False)  # Ensure this is stored as UTC
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    estimator_id = db.Column(db.Integer, db.ForeignKey('estimator.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # UTC by default for created_at
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)  # UTC by default for updated_at
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    
    # Phase 2: Staff self-service fields
    staff_notes = db.Column(db.Text, nullable=True)  # Internal notes (not visible to customer)
    checked_in_at = db.Column(db.DateTime, nullable=True)
    checked_out_at = db.Column(db.DateTime, nullable=True)
    
    # Phase 2: Recurring appointments
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_parent_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)
    location = db.relationship('Location', backref='appointments')

    # Phase 17: Advanced Scheduling fields
    appointment_type_id = db.Column(db.Integer, db.ForeignKey('appointment_type.id'), nullable=True)
    current_attendees = db.Column(db.Integer, default=1)
    max_attendees = db.Column(db.Integer, default=1)  # Snapshot from type at booking time
    intake_form_data = db.Column(db.JSON, default=dict)
    checked_in_method = db.Column(db.String(20), nullable=True)  # qr, manual
    confirmation_sent_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    estimator = db.relationship('Estimator', backref=db.backref('appointments', lazy=True))
    service = db.relationship('Service', backref=db.backref('appointments', lazy=True))
    recurring_children = db.relationship('Appointment', backref=db.backref('recurring_parent', remote_side=[id]), lazy='dynamic')
    appointment_type = db.relationship('AppointmentType', backref=db.backref('appointments', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'email': self.email,
            'preferred_date_time': self.preferred_date_time.isoformat() if self.preferred_date_time else None,
            'service_id': self.service_id,
            'estimator_id': self.estimator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'service': self.service.name if self.service else None,
            'estimator': self.estimator.name if self.estimator else None
        }

    # To ensure timestamps are always stored as UTC
    @staticmethod
    def to_utc(naive_datetime):
        """Converts a naive datetime to UTC"""
        return pytz.utc.localize(naive_datetime)

    @staticmethod
    def from_utc(utc_datetime):
        """Converts a UTC datetime to naive local time if needed"""
        return utc_datetime.astimezone(pytz.utc).replace(tzinfo=None)
    
@event.listens_for(Appointment, "before_insert")
def receive_before_insert(mapper, connection, target):
    # Make sure 'created_at' is always UTC
    target.created_at = datetime.utcnow()

@event.listens_for(Appointment, "before_update")
def receive_before_update(mapper, connection, target):
    # Make sure 'updated_at' is always UTC
    target.updated_at = datetime.utcnow()

class Estimator(db.Model):
    __tablename__ = 'estimator'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Phase 2: Link to User account
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Filter active estimators
    
    user = db.relationship('User', backref=db.backref('estimator_profile', uselist=False))


# Phase 2: Availability Models

class Availability(db.Model):
    """Recurring weekly availability for estimators."""
    __tablename__ = 'availability'
    id = db.Column(db.Integer, primary_key=True)
    estimator_id = db.Column(db.Integer, db.ForeignKey('estimator.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_recurring = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    estimator = db.relationship('Estimator', backref=db.backref('availabilities', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (
        Index('idx_availability_estimator_day', 'estimator_id', 'day_of_week'),
    )

    def __repr__(self):
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        return f'<Availability {days[self.day_of_week]} {self.start_time}-{self.end_time}>'


class AvailabilityException(db.Model):
    """Exception dates for holidays, PTO, or custom hours."""
    __tablename__ = 'availability_exception'
    id = db.Column(db.Integer, primary_key=True)
    estimator_id = db.Column(db.Integer, db.ForeignKey('estimator.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    is_blocked = db.Column(db.Boolean, default=True)  # True = fully blocked, False = custom hours
    custom_start_time = db.Column(db.Time, nullable=True)  # Only if is_blocked=False
    custom_end_time = db.Column(db.Time, nullable=True)
    reason = db.Column(db.String(100), nullable=True)  # e.g., "Holiday", "PTO"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    estimator = db.relationship('Estimator', backref=db.backref('availability_exceptions', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (
        Index('idx_exception_estimator_date', 'estimator_id', 'date'),
    )

    def __repr__(self):
        return f'<AvailabilityException {self.date} blocked={self.is_blocked}>'


class RescheduleRequest(db.Model):
    """Staff-initiated reschedule proposals."""
    __tablename__ = 'reschedule_request'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Staff who proposed
    proposed_datetime = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    appointment = db.relationship('Appointment', backref=db.backref('reschedule_requests', lazy=True))
    user = db.relationship('User', backref=db.backref('reschedule_requests', lazy=True))
    
    __table_args__ = (
        Index('idx_reschedule_status', 'status'),
    )

    def __repr__(self):
        return f'<RescheduleRequest appointment={self.appointment_id} status={self.status}>'

class ContactFormSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='New')  # Dynamic via PipelineStage
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, default=list)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    
    # Phase 4: CRM Enhancements
    source = db.Column(db.String(50), default='contact_form')  # 'contact_form', 'referral', 'website', etc.
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    custom_fields = db.Column(db.JSON, default=dict)  # Dynamic form fields
    
    assigned_to = db.relationship('User', backref=db.backref('assigned_leads', lazy=True))
    location = db.relationship('Location', backref='contact_submissions')

class BusinessConfig(db.Model):
    __tablename__ = 'business_config'
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BusinessConfig {self.setting_name}={self.setting_value}>'
    
class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True)  # Legacy field, kept for migration
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    image = db.Column(db.LargeBinary, nullable=True)  # Store image as BLOB
    image_mime_type = db.Column(db.String(50), nullable=True)  # Store MIME type (e.g., image/png)
    
    # Phase 3: Blog Platform Enhancement fields
    blog_category_id = db.Column(db.Integer, db.ForeignKey('blog_category.id'), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    series_id = db.Column(db.Integer, db.ForeignKey('post_series.id'), nullable=True)
    series_order = db.Column(db.Integer, default=0)
    publish_at = db.Column(db.DateTime, nullable=True)  # For scheduled publishing
    meta_description = db.Column(db.String(300), nullable=True)
    read_time_minutes = db.Column(db.Integer, nullable=True)

    # Relationships
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

    __table_args__ = (
        Index('idx_post_slug', 'slug'),  # Index for faster slug lookups
        Index('idx_post_publish_at', 'publish_at'),  # Phase 3: For scheduled publishing queries
    )
    
    def calculate_read_time(self):
        """Calculate estimated read time in minutes based on content word count."""
        if self.content:
            word_count = len(self.content.split())
            # Average reading speed: 200 words per minute
            return max(1, round(word_count / 200))
        return 1

    def __repr__(self):
        return f'<Post title={self.title} slug={self.slug}>'

@event.listens_for(Post, "before_insert")
def post_before_insert(mapper, connection, target):
    # Ensure created_at is always UTC
    target.created_at = datetime.utcnow()

@event.listens_for(Post, "before_update")
def post_before_update(mapper, connection, target):
    # Ensure updated_at is always UTC
    target.updated_at = datetime.utcnow()


# ============================================================================
# Phase 3: Blog Platform Enhancement Models
# ============================================================================

# Many-to-many association table for Post-Tag relationship
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# Many-to-many for multi-author posts
post_authors = db.Table('post_authors',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class Tag(db.Model):
    """Tags for blog posts with many-to-many relationship."""
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', secondary=post_tags, back_populates='tags')
    
    def __repr__(self):
        return f'<Tag {self.name}>'


class BlogCategory(db.Model):
    """Hierarchical categories for blog posts (separate from product Category)."""
    __tablename__ = 'blog_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('blog_category.id'), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    children = db.relationship('BlogCategory', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def __repr__(self):
        return f'<BlogCategory {self.name}>'
    
    def get_ancestors(self):
        """Return list of ancestor categories (for breadcrumbs)."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors


class PostSeries(db.Model):
    """Group related posts into a series."""
    __tablename__ = 'post_series'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='series', lazy='dynamic', order_by='Post.series_order')
    
    def __repr__(self):
        return f'<PostSeries {self.title}>'


class PostRevision(db.Model):
    """Track revision history for blog posts."""
    __tablename__ = 'post_revision'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    revision_note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    post = db.relationship('Post', backref=db.backref('revisions', lazy='dynamic', order_by='PostRevision.created_at.desc()'))
    user = db.relationship('User')
    
    __table_args__ = (
        Index('idx_revision_post_created', 'post_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<PostRevision post={self.post_id} at {self.created_at}>'


class Comment(db.Model):
    """Comments on blog posts with threading and moderation support."""
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # For guest comments
    author_name = db.Column(db.String(100), nullable=True)
    author_email = db.Column(db.String(120), nullable=True)
    
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, spam, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_hash = db.Column(db.String(64), nullable=True)
    
    # Relationships
    post = db.relationship('Post', backref=db.backref('comments', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    __table_args__ = (
        Index('idx_comment_post_status', 'post_id', 'status'),
        Index('idx_comment_status', 'status'),
    )
    
    def get_display_name(self):
        """Return author name for display."""
        if self.user:
            return self.user.username
        return self.author_name or 'Anonymous'
    
    def __repr__(self):
        return f'<Comment {self.id} on post {self.post_id} status={self.status}>'


class PostImage(db.Model):
    """Gallery images for blog posts (beyond the main hero image)."""
    __tablename__ = 'post_image'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    alt_text = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    post = db.relationship('Post', backref=db.backref('gallery_images', lazy=True, order_by='PostImage.display_order'))
    media = db.relationship('Media')
    
    def __repr__(self):
        return f'<PostImage {self.id} for post {self.post_id}>'



# Post relationships (defined after related classes exist)
Post.tags = db.relationship('Tag', secondary=post_tags, back_populates='posts')
Post.blog_category = db.relationship('BlogCategory', backref=db.backref('posts', lazy='dynamic'))
Post.additional_authors = db.relationship('User', secondary=post_authors, backref='contributed_posts')

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    data = db.Column(db.LargeBinary)  # The file content
    mimetype = db.Column(db.String(100))
    size = db.Column(db.Integer)
    checksum = db.Column(db.String(64))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Media {self.filename}>'

class Page(db.Model):
    """Content page with staging workflow and SEO features."""
    __tablename__ = 'page'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text, nullable=True)  # The raw HTML content from CKEditor
    meta_description = db.Column(db.String(300), nullable=True)
    is_published = db.Column(db.Boolean, default=False, nullable=False)  # Legacy, kept for compatibility
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Phase 12: Content Management Enhancement fields
    status = db.Column(db.String(20), default='draft')  # draft, review, published
    canonical_url = db.Column(db.String(500), nullable=True)  # Override canonical URL
    schema_type = db.Column(db.String(50), default='WebPage')  # Schema.org type: WebPage, AboutPage, ContactPage, FAQPage, etc.
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    author = db.relationship('User', backref=db.backref('authored_pages', lazy=True))

    __table_args__ = (
        Index('idx_page_slug', 'slug'),
        Index('idx_page_status', 'status'),
    )

    def __repr__(self):
        return f'<Page title={self.title} slug={self.slug} status={self.status}>'
    
    def is_visible(self):
        """Check if page should be publicly visible."""
        return self.status == 'published' or self.is_published


class PageRevision(db.Model):
    """Track revision history for pages with full content snapshots."""
    __tablename__ = 'page_revision'
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text, nullable=True)
    meta_description = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    revision_note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    page = db.relationship('Page', backref=db.backref('revisions', lazy='dynamic', order_by='PageRevision.created_at.desc()'))
    user = db.relationship('User')
    
    __table_args__ = (
        Index('idx_page_revision_page_created', 'page_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<PageRevision page={self.page_id} at {self.created_at}>'


class PageCustomField(db.Model):
    """Custom key-value fields for flexible page schema."""
    __tablename__ = 'page_custom_field'
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(20), default='text')  # text, number, date, boolean, json
    field_value = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    page = db.relationship('Page', backref=db.backref('custom_fields', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (
        Index('idx_pcf_page', 'page_id'),
        db.UniqueConstraint('page_id', 'field_name', name='uq_page_field'),
    )
    
    def get_typed_value(self):
        """Return value cast to appropriate Python type."""
        if self.field_value is None:
            return None
        if self.field_type == 'number':
            try:
                return float(self.field_value)
            except ValueError:
                return 0
        elif self.field_type == 'boolean':
            return self.field_value.lower() in ('true', '1', 'yes')
        elif self.field_type == 'json':
            import json
            try:
                return json.loads(self.field_value)
            except json.JSONDecodeError:
                return {}
        elif self.field_type == 'date':
            from datetime import datetime as dt
            try:
                return dt.fromisoformat(self.field_value)
            except ValueError:
                return None
        return self.field_value  # text
    
    def __repr__(self):
        return f'<PageCustomField {self.field_name}={self.field_value[:20] if self.field_value else None}>'


class PageRender(db.Model):
    """
    Cache table to store the fully rendered HTML for a page.
    This allows fast serving without re-rendering templates or re-processing content on every request.
    """
    __tablename__ = 'page_render'
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False, unique=True)
    rendered_html = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    page = db.relationship('Page', backref=db.backref('render', uselist=False, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<PageRender page_id={self.page_id}>'

@event.listens_for(Page, "before_insert")
def page_before_insert(mapper, connection, target):
    target.created_at = datetime.utcnow()

@event.listens_for(Page, "before_update")
def page_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()

# ============================================================================
# Phase 6: Messaging & Notifications Models
# ============================================================================

# Many-to-many association table for channel members
channel_members = db.Table('channel_members',
    db.Column('channel_id', db.Integer, db.ForeignKey('channel.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class Channel(db.Model):
    """Messaging channel (public, private, or direct message)."""
    __tablename__ = 'channel'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), default='public')  # public, private, direct
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Phase 6: New fields
    is_archived = db.Column(db.Boolean, default=False)
    is_direct = db.Column(db.Boolean, default=False)  # True for 1:1 DM channels
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    
    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_channels')
    members = db.relationship('User', secondary=channel_members, backref=db.backref('channels', lazy=True))
    
    __table_args__ = (
        Index('idx_channel_type', 'type'),
        Index('idx_channel_archived', 'is_archived'),
    )

    def __repr__(self):
        return f'<Channel {self.name}>'
    
    def get_display_name(self, current_user=None):
        """Get display name for channel. For DMs, show the other user's name."""
        if self.is_direct and current_user:
            other_members = [m for m in self.members if m.id != current_user.id]
            if other_members:
                return other_members[0].username
        return self.name


class Message(db.Model):
    """Message in a channel."""
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    attachment_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_by = db.Column(db.JSON, default=list)  # List of user_ids who read this
    
    # Phase 6: Thread support (optional)
    parent_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    
    # Relationships
    channel = db.relationship('Channel', backref=db.backref('messages', lazy=True, cascade="all, delete-orphan"))
    user = db.relationship('User', backref=db.backref('messages', lazy=True))
    attachment = db.relationship('Media', backref='messages')
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    __table_args__ = (
        Index('idx_message_channel_created', 'channel_id', 'created_at'),
    )

    def __repr__(self):
        return f'<Message {self.id} in Channel {self.channel_id}>'
    
    def get_mentions(self):
        """Extract @username mentions from content."""
        import re
        mentions = re.findall(r'@(\w+)', self.content or '')
        return mentions


class ChannelMember(db.Model):
    """Track channel membership with read receipts."""
    __tablename__ = 'channel_member'
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_read_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    last_read_at = db.Column(db.DateTime, nullable=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_muted = db.Column(db.Boolean, default=False)
    
    channel = db.relationship('Channel', backref=db.backref('membership_records', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('channel_memberships', lazy=True))
    last_read_message = db.relationship('Message', foreign_keys=[last_read_message_id])
    
    __table_args__ = (
        db.UniqueConstraint('channel_id', 'user_id', name='uq_channel_member'),
        Index('idx_cm_channel', 'channel_id'),
        Index('idx_cm_user', 'user_id'),
    )
    
    def __repr__(self):
        return f'<ChannelMember channel={self.channel_id} user={self.user_id}>'


class MessageReaction(db.Model):
    """Emoji reactions on messages."""
    __tablename__ = 'message_reaction'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emoji = db.Column(db.String(20), nullable=False)  # Unicode emoji or shortcode
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    message = db.relationship('Message', backref=db.backref('reactions', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('message_reactions', lazy=True))
    
    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', 'emoji', name='uq_message_reaction'),
        Index('idx_reaction_message', 'message_id'),
    )
    
    def __repr__(self):
        return f'<MessageReaction {self.emoji} on {self.message_id}>'


class Notification(db.Model):
    """Unified notification system for all app events."""
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # message, leave_approved, appointment_reminder, order_placed, mention, etc.
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(500), nullable=True)  # URL to navigate to when clicked
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional: Related entity reference
    related_type = db.Column(db.String(50), nullable=True)  # 'channel', 'order', 'leave_request', etc.
    related_id = db.Column(db.Integer, nullable=True)
    
    # For email digest tracking
    email_sent = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', order_by='Notification.created_at.desc()'))
    
    __table_args__ = (
        Index('idx_notification_user_read', 'user_id', 'is_read'),
        Index('idx_notification_created', 'created_at'),
        Index('idx_notification_type', 'type'),
    )
    
    def __repr__(self):
        return f'<Notification {self.type}: {self.title[:30]}>'
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary for JSON response."""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'body': self.body,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'related_type': self.related_type,
            'related_id': self.related_id
        }


class NotificationPreference(db.Model):
    """User preferences for notification delivery."""
    __tablename__ = 'notification_preference'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Email digest settings
    email_digest_enabled = db.Column(db.Boolean, default=True)
    email_digest_frequency = db.Column(db.String(20), default='daily')  # daily, weekly, never
    
    # Per-type settings (stored as JSON)
    muted_types = db.Column(db.JSON, default=list)  # List of notification types to mute
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('notification_preferences', uselist=False))
    
    def __repr__(self):
        return f'<NotificationPreference user={self.user_id}>'


# ============================================================================
# Phase 22: Registration & User Experience Hardening Models
# ============================================================================

class OnboardingStep(db.Model):
    """Track user progress through onboarding steps."""
    __tablename__ = 'onboarding_step'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    step_name = db.Column(db.String(50), nullable=False)  # welcome, profile, preferences, tour
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    data = db.Column(db.JSON, default=dict)  # Step-specific data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('onboarding_steps', lazy=True, cascade='all, delete-orphan'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'step_name', name='uq_onboarding_step'),
        Index('idx_onboarding_user', 'user_id'),
    )
    
    def __repr__(self):
        return f'<OnboardingStep user={self.user_id} step={self.step_name} completed={self.completed}>'


class UserActivity(db.Model):
    """Unified activity feed for user dashboard."""
    __tablename__ = 'user_activity'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # order_placed, appointment_booked, profile_updated, login, etc.
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    related_type = db.Column(db.String(50), nullable=True)  # order, appointment, post, etc.
    related_id = db.Column(db.Integer, nullable=True)
    icon = db.Column(db.String(50), default='fa-circle')
    extra_data = db.Column(db.JSON, default=dict)  # Additional context data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('activities', lazy='dynamic', order_by='UserActivity.created_at.desc()'))
    
    __table_args__ = (
        Index('idx_activity_user_created', 'user_id', 'created_at'),
        Index('idx_activity_type', 'activity_type'),
    )
    
    def __repr__(self):
        return f'<UserActivity {self.activity_type}: {self.title[:30]}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON response."""
        return {
            'id': self.id,
            'activity_type': self.activity_type,
            'title': self.title,
            'description': self.description,
            'related_type': self.related_type,
            'related_id': self.related_id,
            'icon': self.icon,
            'created_at': self.created_at.isoformat(),
            'extra_data': self.extra_data
        }


class UserPreference(db.Model):
    """Granular user preferences for notifications, privacy, and display."""
    __tablename__ = 'user_preference'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    
    # Email preferences
    email_marketing = db.Column(db.Boolean, default=True)
    email_order_updates = db.Column(db.Boolean, default=True)
    email_appointment_reminders = db.Column(db.Boolean, default=True)
    email_digest_weekly = db.Column(db.Boolean, default=False)
    email_newsletter = db.Column(db.Boolean, default=True)
    
    # Push/SMS preferences
    push_enabled = db.Column(db.Boolean, default=False)
    sms_enabled = db.Column(db.Boolean, default=False)
    
    # Privacy preferences
    show_activity_status = db.Column(db.Boolean, default=True)
    show_profile_publicly = db.Column(db.Boolean, default=False)
    
    # Display preferences
    theme = db.Column(db.String(20), default='light')  # light, dark, system
    language = db.Column(db.String(10), default='en')
    
    # GDPR
    data_export_requested_at = db.Column(db.DateTime, nullable=True)
    data_export_completed_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('preferences', uselist=False))
    
    def __repr__(self):
        return f'<UserPreference user={self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON/form population."""
        return {
            'email_marketing': self.email_marketing,
            'email_order_updates': self.email_order_updates,
            'email_appointment_reminders': self.email_appointment_reminders,
            'email_digest_weekly': self.email_digest_weekly,
            'email_newsletter': self.email_newsletter,
            'push_enabled': self.push_enabled,
            'sms_enabled': self.sms_enabled,
            'show_activity_status': self.show_activity_status,
            'show_profile_publicly': self.show_profile_publicly,
            'theme': self.theme,
            'language': self.language
        }


class SavedItem(db.Model):
    """User's saved/bookmarked items (products, posts, etc)."""
    __tablename__ = 'saved_item'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # product, post, page
    item_id = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=True)  # Optional user notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('saved_items', lazy='dynamic', cascade='all, delete-orphan'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'item_type', 'item_id', name='uq_saved_item'),
        Index('idx_saved_user_type', 'user_id', 'item_type'),
    )
    
    def __repr__(self):
        return f'<SavedItem user={self.user_id} {self.item_type}:{self.item_id}>'

class LeaveRequest(db.Model):
    """Enhanced leave request with approval workflow and leave types."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Phase 5: Leave Management enhancements
    leave_type = db.Column(db.String(50), default='vacation')  # vacation, sick, personal, unpaid
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('leave_requests', lazy=True))
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    
    __table_args__ = (
        Index('idx_leave_user_status', 'user_id', 'status'),
        Index('idx_leave_dates', 'start_date', 'end_date'),
    )
    
    def days_requested(self):
        """Calculate the number of days in this leave request."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def __repr__(self):
        return f'<LeaveRequest {self.user_id} {self.leave_type} {self.status}>'


class LeaveType(db.Model):
    """Configurable leave types with policies."""
    __tablename__ = 'leave_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # vacation, sick, personal, unpaid
    display_name = db.Column(db.String(100), nullable=False)
    default_days_per_year = db.Column(db.Integer, default=0)
    allows_carryover = db.Column(db.Boolean, default=False)
    max_carryover_days = db.Column(db.Integer, default=0)
    is_paid = db.Column(db.Boolean, default=True)
    requires_approval = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LeaveType {self.name}>'


class LeaveBalance(db.Model):
    """Track leave entitlements per user per year."""
    __tablename__ = 'leave_balance'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # Matches LeaveType.name
    year = db.Column(db.Integer, nullable=False)
    balance_days = db.Column(db.Float, default=0)  # Total allocated days
    used_days = db.Column(db.Float, default=0)  # Days used
    carryover_days = db.Column(db.Float, default=0)  # Days carried from previous year
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('leave_balances', lazy=True))
    
    __table_args__ = (
        Index('idx_balance_user_type_year', 'user_id', 'leave_type', 'year'),
        db.UniqueConstraint('user_id', 'leave_type', 'year', name='uq_user_leave_year'),
    )
    
    def remaining_days(self):
        """Calculate remaining leave balance."""
        return self.balance_days + self.carryover_days - self.used_days
    
    def __repr__(self):
        return f'<LeaveBalance {self.user_id} {self.leave_type} {self.year}: {self.remaining_days()} remaining>'


class EncryptedDocument(db.Model):
    """Enhanced encrypted document with sharing and expiration."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    blob_data = db.Column(db.LargeBinary, nullable=False)  # Encrypted content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Phase 5: Document Management enhancements
    category = db.Column(db.String(50), default='personal')  # contracts, certifications, personal
    expires_at = db.Column(db.Date, nullable=True)  # For certifications/licenses
    requires_signature = db.Column(db.Boolean, default=False)
    signed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    signed_at = db.Column(db.DateTime, nullable=True)
    mimetype = db.Column(db.String(100), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('documents', lazy=True))
    signed_by = db.relationship('User', foreign_keys=[signed_by_id])
    
    __table_args__ = (
        Index('idx_doc_user_category', 'user_id', 'category'),
        Index('idx_doc_expiry', 'expires_at'),
    )

    def __repr__(self):
        return f'<EncryptedDocument {self.title}>'


class DocumentShare(db.Model):
    """Enable document sharing between users or roles."""
    __tablename__ = 'document_share'
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('encrypted_document.id'), nullable=False)
    shared_with_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    shared_with_role = db.Column(db.String(50), nullable=True)  # Role name for role-based sharing
    permissions = db.Column(db.String(20), default='view')  # view, download
    shared_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    document = db.relationship('EncryptedDocument', backref=db.backref('shares', lazy=True, cascade='all, delete-orphan'))
    shared_with_user = db.relationship('User', foreign_keys=[shared_with_user_id], backref='shared_documents_received')
    shared_by = db.relationship('User', foreign_keys=[shared_by_id])
    
    __table_args__ = (
        Index('idx_share_doc', 'document_id'),
        Index('idx_share_user', 'shared_with_user_id'),
        Index('idx_share_role', 'shared_with_role'),
    )

    def __repr__(self):
        return f'<DocumentShare doc={self.document_id} to user={self.shared_with_user_id} role={self.shared_with_role}>'


class TimeEntry(db.Model):
    """Clock in/out tracking for hourly employees."""
    __tablename__ = 'time_entry'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)  # Calculated on clock out
    date = db.Column(db.Date, nullable=False)  # For easy grouping by date
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('time_entries', lazy=True))
    
    __table_args__ = (
        Index('idx_time_user_date', 'user_id', 'date'),
    )
    
    def calculate_duration(self):
        """Calculate duration in minutes if clocked out."""
        if self.clock_in and self.clock_out:
            delta = self.clock_out - self.clock_in
            return int(delta.total_seconds() / 60)
        return None

    def __repr__(self):
        return f'<TimeEntry {self.user_id} {self.date}>'


class Task(db.Model):
    """Background task with retry logic, priority, and dead letter queue support."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed, dead_letter
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.Text, nullable=True)
    
    # Phase 8: Retry logic fields
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    next_retry_at = db.Column(db.DateTime, nullable=True)  # When to retry (for exponential backoff)
    
    # Phase 8: Priority field (higher = processed first)
    priority = db.Column(db.Integer, default=0)  # -10=low, 0=normal, 10=high
    
    __table_args__ = (
        Index('idx_task_status_priority', 'status', 'priority'),
        Index('idx_task_next_retry', 'next_retry_at'),
    )

    def __repr__(self):
        return f'<Task {self.name} {self.status} pri={self.priority}>'
    
    def calculate_next_retry(self):
        """Calculate next retry time using exponential backoff (2^retry_count minutes)."""
        if self.retry_count >= self.max_retries:
            return None
        delay_minutes = 2 ** self.retry_count  # 1, 2, 4, 8, ... minutes
        return datetime.utcnow() + timedelta(minutes=delay_minutes)
    
    def should_move_to_dead_letter(self):
        """Check if task should be moved to dead letter queue."""
        return self.retry_count >= self.max_retries


class CronTask(db.Model):
    """Scheduled task configuration for cron-like job execution."""
    __tablename__ = 'cron_task'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    handler = db.Column(db.String(100), nullable=False)  # Task handler name
    schedule = db.Column(db.String(50), nullable=False)  # @hourly, @daily, @weekly, or cron expression
    payload = db.Column(db.JSON, default=dict)
    is_active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime, nullable=True)
    next_run = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_cron_active_next', 'is_active', 'next_run'),
    )
    
    def __repr__(self):
        return f'<CronTask {self.name} schedule={self.schedule}>'


class WorkerHeartbeat(db.Model):
    """Worker status tracking for observability."""
    __tablename__ = 'worker_heartbeat'
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.String(50), nullable=False, unique=True)
    last_heartbeat = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='running')  # running, stopped
    tasks_processed = db.Column(db.Integer, default=0)
    tasks_failed = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    hostname = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<WorkerHeartbeat {self.worker_id} {self.status}>'
    
    def is_alive(self, timeout_seconds=60):
        """Check if worker is considered alive (heartbeat within timeout)."""
        if self.last_heartbeat is None:
            return False
        return (datetime.utcnow() - self.last_heartbeat).total_seconds() < timeout_seconds

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False) # Markdown or text
    full_html = db.Column(db.Text, nullable=True) # Rendered HTML
    sent_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='draft') # draft, queued, sent
    recipient_tags = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PageView(db.Model):
    """Enhanced page view tracking with session and UTM support."""
    __tablename__ = 'page_view'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), nullable=True, index=True)  # Session token
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    url = db.Column(db.String(500), nullable=False)
    referrer = db.Column(db.String(500), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)  # Increased length
    ip_hash = db.Column(db.String(64), nullable=True)  # Hashed IP for privacy
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    load_time_ms = db.Column(db.Integer, nullable=True)  # Page load time in milliseconds
    
    # UTM tracking parameters
    utm_source = db.Column(db.String(100), nullable=True)  # e.g., google, newsletter
    utm_medium = db.Column(db.String(100), nullable=True)  # e.g., cpc, email
    utm_campaign = db.Column(db.String(100), nullable=True)  # Campaign name
    utm_term = db.Column(db.String(100), nullable=True)  # Paid search keywords
    utm_content = db.Column(db.String(100), nullable=True)  # A/B test identifier
    
    # Device info (parsed from user_agent)
    device_type = db.Column(db.String(20), nullable=True)  # desktop, mobile, tablet
    browser = db.Column(db.String(50), nullable=True)
    os = db.Column(db.String(50), nullable=True)
    
    user = db.relationship('User', backref=db.backref('page_views', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_pageview_session', 'session_id'),
        Index('idx_pageview_timestamp', 'timestamp'),
        Index('idx_pageview_url', 'url'),
        Index('idx_pageview_utm', 'utm_source', 'utm_medium', 'utm_campaign'),
    )
    
    def __repr__(self):
        return f'<PageView {self.url} at {self.timestamp}>'

class UnsubscribedEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    unsubscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UnsubscribedEmail {self.email}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Integer, nullable=False) # In cents
    currency = db.Column(db.String(3), default='usd')
    inventory_count = db.Column(db.Integer, default=0)
    
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    
    # Digital goods
    is_digital = db.Column(db.Boolean, default=False)
    file_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Category support
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    
    # Subscription products
    is_subscription = db.Column(db.Boolean, default=False)
    stripe_price_id = db.Column(db.String(100), nullable=True)  # For recurring billing

    # Relationships
    image = db.relationship('Media', foreign_keys=[media_id])
    file = db.relationship('Media', foreign_keys=[file_id])

    def __repr__(self):
        return f'<Product {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Nullable for guest checkout
    status = db.Column(db.String(20), default='pending') # pending, paid, shipped, cancelled
    total_amount = db.Column(db.Integer, nullable=False) # In cents
    currency = db.Column(db.String(3), default='usd')
    
    stripe_payment_intent_id = db.Column(db.String(100), nullable=True)
    
    # Simple shipping address storage for now (JSON or text)
    shipping_address = db.Column(db.Text, nullable=True)
    
    # Contact info for guests
    email = db.Column(db.String(120), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    
    # Fulfillment tracking
    fulfillment_status = db.Column(db.String(20), default='unfulfilled')  # unfulfilled, shipped, delivered, returned
    tracking_number = db.Column(db.String(100), nullable=True)
    carrier = db.Column(db.String(50), nullable=True)  # e.g., 'usps', 'fedex', 'ups'
    shipped_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Order {self.id} {self.status}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price_at_purchase = db.Column(db.Integer, nullable=False) # In cents
    
    product = db.relationship('Product')

    def __repr__(self):
        return f'<OrderItem {self.product_id} x{self.quantity}>'


class DownloadToken(db.Model):
    """Secure download tokens for digital products."""
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    max_downloads = db.Column(db.Integer, default=3)
    download_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order_item = db.relationship('OrderItem', backref='download_tokens')
    user = db.relationship('User', backref='download_tokens')
    
    def is_valid(self):
        """Check if token is still valid (not expired, downloads remaining)."""
        if datetime.utcnow() > self.expires_at:
            return False
        if self.download_count >= self.max_downloads:
            return False
        return True
    
    def use(self):
        """Increment download count."""
        self.download_count += 1
        db.session.commit()

    def __repr__(self):
        return f'<DownloadToken {self.token[:8]}...>'

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(50), nullable=False) # e.g., 'create_user', 'update_config'
    target_type = db.Column(db.String(50)) # e.g., 'User', 'BusinessConfig'
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.JSON, nullable=True) # Changeset or metadata
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id}>'

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Location {self.name}>'

import hashlib

class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_hash = db.Column(db.String(128), unique=True, nullable=False) # SHA256 of the actual key
    prefix = db.Column(db.String(8), nullable=False) # First 7 chars for display
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    scopes = db.Column(db.JSON, default=list) # e.g. ['read:leads', 'write:orders']
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref='api_keys')
    
    def set_key(self, key):
        """Sets the key_hash and prefix from a raw key."""
        self.key_hash = hashlib.sha256(key.encode('utf-8')).hexdigest()
        self.prefix = key[:7]
        
    def check_key(self, key):
        """Checks if the provided key matches the hash."""
        return self.key_hash == hashlib.sha256(key.encode('utf-8')).hexdigest()

    def __repr__(self):
        return f'<ApiKey {self.name} {self.prefix}...>'


# Phase 1 Complete Models

class UserCart(db.Model):
    """Cart persistence for logged-in users."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    cart_data = db.Column(db.JSON, default=dict)  # {product_id: quantity}
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('cart', uselist=False))

    def __repr__(self):
        return f'<UserCart user_id={self.user_id}>'


class InventoryLock(db.Model):
    """Soft-lock inventory during checkout to prevent overselling."""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    session_id = db.Column(db.String(64), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')
    order = db.relationship('Order')

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f'<InventoryLock product_id={self.product_id} qty={self.quantity}>'


class Subscription(db.Model):
    """Stripe subscription tracking for recurring payments."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    stripe_customer_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, past_due, canceled, trialing
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='subscriptions')
    product = db.relationship('Product', backref='subscriptions')

    def __repr__(self):
        return f'<Subscription {self.stripe_subscription_id} {self.status}>'


class Category(db.Model):
    """Product categories with hierarchical support."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class ProductVariant(db.Model):
    """Product variants for size/color options with variant-level inventory."""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Large / Blue"
    price_adjustment = db.Column(db.Integer, default=0)  # Cents to add/subtract from base price
    inventory_count = db.Column(db.Integer, default=0)
    attributes = db.Column(db.JSON, default=dict)  # {"size": "L", "color": "Blue"}
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref='variants')

    def get_price(self):
        """Get variant price (base + adjustment)."""
        return self.product.price + self.price_adjustment

    def __repr__(self):
        return f'<ProductVariant {self.sku} {self.name}>'


class DownloadLog(db.Model):
    """Track all download attempts for digital products."""
    id = db.Column(db.Integer, primary_key=True)
    download_token_id = db.Column(db.Integer, db.ForeignKey('download_token.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_hash = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    download_token = db.relationship('DownloadToken', backref='logs')
    user = db.relationship('User')

    def __repr__(self):
        return f'<DownloadLog token={self.download_token_id}>'


# ============================================================================
# Phase 4: CRM & Lead Management Models
# ============================================================================

class PipelineStage(db.Model):
    """Dynamic pipeline stages for CRM kanban board."""
    __tablename__ = 'pipeline_stage'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    pipeline_name = db.Column(db.String(50), default='default')  # For multiple pipelines support
    order = db.Column(db.Integer, default=0)
    color = db.Column(db.String(7), default='#6c757d')  # Hex color code
    probability = db.Column(db.Integer, default=0)  # 0-100 conversion probability
    auto_actions = db.Column(db.JSON, default=list)  # List of actions to trigger
    is_active = db.Column(db.Boolean, default=True)
    is_won_stage = db.Column(db.Boolean, default=False)  # Triggers won automation
    is_lost_stage = db.Column(db.Boolean, default=False)  # Marks lead as lost
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_pipeline_stage_order', 'pipeline_name', 'order'),
    )

    def __repr__(self):
        return f'<PipelineStage {self.name} ({self.pipeline_name})>'


class LeadNote(db.Model):
    """Timeline notes for leads (ContactFormSubmission or Appointment)."""
    __tablename__ = 'lead_note'
    id = db.Column(db.Integer, primary_key=True)
    lead_type = db.Column(db.String(20), nullable=False)  # 'contact' or 'appointment'
    lead_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('lead_notes', lazy=True))
    
    __table_args__ = (
        Index('idx_lead_note_lead', 'lead_type', 'lead_id'),
        Index('idx_lead_note_created', 'lead_type', 'lead_id', 'created_at'),
    )

    def __repr__(self):
        return f'<LeadNote {self.lead_type}:{self.lead_id} by user {self.user_id}>'


class LeadActivity(db.Model):
    """Auto-logged activities for leads (status changes, emails sent, etc)."""
    __tablename__ = 'lead_activity'
    id = db.Column(db.Integer, primary_key=True)
    lead_type = db.Column(db.String(20), nullable=False)  # 'contact' or 'appointment'
    lead_id = db.Column(db.Integer, nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'status_change', 'email_sent', 'note_added', 'created', 'assigned'
    description = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for system actions
    old_value = db.Column(db.String(100), nullable=True)
    new_value = db.Column(db.String(100), nullable=True)
    extra_data = db.Column(db.JSON, default=dict)  # Additional data (renamed from metadata - reserved in SQLAlchemy)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('lead_activities', lazy=True))
    
    __table_args__ = (
        Index('idx_lead_activity_lead', 'lead_type', 'lead_id'),
        Index('idx_lead_activity_created', 'lead_type', 'lead_id', 'created_at'),
        Index('idx_lead_activity_type', 'activity_type'),
    )

    def __repr__(self):
        return f'<LeadActivity {self.activity_type} on {self.lead_type}:{self.lead_id}>'


class EmailTemplate(db.Model):
    """Email templates for marketing campaigns, transactional emails, and CRM touchpoints."""
    __tablename__ = 'email_template'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    
    # Content - supports both HTML and plain text
    body = db.Column(db.Text, nullable=True)  # Legacy field for CRM templates
    body_html = db.Column(db.Text, nullable=True)  # HTML version for marketing emails
    body_text = db.Column(db.Text, nullable=True)  # Plain text fallback
    
    # Template classification (Phase 15 enhancement)
    template_type = db.Column(db.String(50), default='general')  # general, welcome, follow_up, marketing, transactional, notification
    category = db.Column(db.String(50), nullable=True)  # welcome, newsletter, promotional, order, etc.
    
    # Variable schema for template variables (Phase 15)
    variables_schema = db.Column(db.JSON, default=dict)  # {"first_name": {"default": "Friend", "required": false}}
    
    # Metadata (Phase 15)
    thumbnail_url = db.Column(db.String(500), nullable=True)  # Preview thumbnail
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    created_by = db.relationship('User')
    
    __table_args__ = (
        Index('idx_email_template_type', 'template_type'),
        Index('idx_email_template_active', 'is_active'),
    )

    def render(self, context):
        """Render template with context dict replacing placeholders.
        
        Returns tuple of (subject, body) for legacy or (html, text) for Phase 15.
        """
        schema = self.variables_schema or {}
        
        # Helper to apply substitutions
        def substitute(text):
            if not text:
                return ''
            result = text
            # First apply schema defaults
            for var_name, var_config in schema.items():
                placeholder = '{{' + var_name + '}}'
                value = context.get(var_name, var_config.get('default', ''))
                result = result.replace(placeholder, str(value))
            # Then apply any additional context
            for key, value in context.items():
                placeholder = '{{' + key + '}}'
                result = result.replace(placeholder, str(value))
            return result
        
        rendered_subject = substitute(self.subject)
        
        # Use body_html/body_text if available, otherwise fall back to body
        if self.body_html:
            rendered_html = substitute(self.body_html)
            rendered_text = substitute(self.body_text) if self.body_text else ''
            return rendered_html, rendered_text
        else:
            rendered_body = substitute(self.body)
            return rendered_subject, rendered_body
    
    def render_full(self, context):
        """Render template returning subject, html, and text."""
        schema = self.variables_schema or {}
        
        def substitute(text):
            if not text:
                return ''
            result = text
            for var_name, var_config in schema.items():
                placeholder = '{{' + var_name + '}}'
                value = context.get(var_name, var_config.get('default', ''))
                result = result.replace(placeholder, str(value))
            for key, value in context.items():
                placeholder = '{{' + key + '}}'
                result = result.replace(placeholder, str(value))
            return result
        
        return (
            substitute(self.subject),
            substitute(self.body_html or self.body or ''),
            substitute(self.body_text or '')
        )

    def __repr__(self):
        return f'<EmailTemplate {self.name} ({self.template_type})>'


class LeadScore(db.Model):
    """Lead scoring configuration and history."""
    __tablename__ = 'lead_score'
    id = db.Column(db.Integer, primary_key=True)
    lead_type = db.Column(db.String(20), nullable=False)
    lead_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, default=0)  # Total score
    score_breakdown = db.Column(db.JSON, default=dict)  # {"source": 10, "engagement": 20}
    last_calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_lead_score_lead', 'lead_type', 'lead_id', unique=True),
        Index('idx_lead_score_value', 'score'),
    )

    def __repr__(self):
        return f'<LeadScore {self.lead_type}:{self.lead_id} = {self.score}>'


class LeadScoreRule(db.Model):
    """Rules for automatic lead scoring."""
    __tablename__ = 'lead_score_rule'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'source', 'engagement', 'fit', 'behavior'
    condition_type = db.Column(db.String(50), nullable=False)  # 'source_equals', 'has_phone', 'message_length_gt', etc
    condition_value = db.Column(db.String(100), nullable=True)  # Value to compare
    points = db.Column(db.Integer, nullable=False)  # Points to add/subtract
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LeadScoreRule {self.name}: {self.points} pts>'


class FollowUpReminder(db.Model):
    """Scheduled follow-up reminders for stale leads."""
    __tablename__ = 'follow_up_reminder'
    id = db.Column(db.Integer, primary_key=True)
    lead_type = db.Column(db.String(20), nullable=False)
    lead_id = db.Column(db.Integer, nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    note = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'dismissed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    assigned_to = db.relationship('User', backref=db.backref('follow_up_reminders', lazy=True))
    
    __table_args__ = (
        Index('idx_followup_lead', 'lead_type', 'lead_id'),
        Index('idx_followup_due', 'due_date', 'status'),
        Index('idx_followup_assigned', 'assigned_to_id', 'status'),
    )

    def __repr__(self):
        return f'<FollowUpReminder {self.lead_type}:{self.lead_id} due {self.due_date}>'


# ============================================================================
# Phase 9: API & Integrations Models
# ============================================================================

class Webhook(db.Model):
    """Outbound webhook configuration for external integrations."""
    __tablename__ = 'webhook'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)  # Target URL
    secret = db.Column(db.String(64), nullable=True)  # HMAC signing secret
    events = db.Column(db.JSON, default=list)  # ['lead.created', 'order.created', 'order.updated']
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_triggered_at = db.Column(db.DateTime, nullable=True)
    last_status_code = db.Column(db.Integer, nullable=True)
    failure_count = db.Column(db.Integer, default=0)
    
    # Optional: Link to user who created it
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by = db.relationship('User', backref=db.backref('webhooks', lazy=True))
    
    __table_args__ = (
        Index('idx_webhook_active', 'is_active'),
    )

    def __repr__(self):
        return f'<Webhook {self.name} -> {self.url}>'
    
    def to_dict(self):
        """Convert to dictionary for admin display."""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'events': self.events,
            'is_active': self.is_active,
            'last_triggered_at': self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            'last_status_code': self.last_status_code,
            'failure_count': self.failure_count
        }


# ============================================================================
# Phase 10: Automation & Workflow Models
# ============================================================================

class Workflow(db.Model):
    """Workflow definition for automation rules."""
    __tablename__ = 'workflow'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    trigger_event = db.Column(db.String(100), nullable=False)  # e.g., 'lead.created'
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    steps = db.relationship('WorkflowStep', backref='workflow', lazy='dynamic', order_by='WorkflowStep.order', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Workflow {self.name}>'

class WorkflowStep(db.Model):
    """Individual step in a workflow."""
    __tablename__ = 'workflow_step'
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # e.g., 'send_email', 'create_task'
    config = db.Column(db.JSON, default=dict)  # Configuration for the action
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WorkflowStep {self.action_type} for Workflow {self.workflow_id}>'


# ============================================================================
# Phase 13: Shopify-Killer E-Commerce Models
# ============================================================================

class ProductAttribute(db.Model):
    """Reusable attribute definitions (Size, Color, Material)."""
    __tablename__ = 'product_attribute'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    attribute_type = db.Column(db.String(50), default='select')  # select, color, size, text
    position = db.Column(db.Integer, default=0)
    is_required = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    values = db.relationship('ProductAttributeValue', backref='attribute', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_attr_position', 'position'),
    )
    
    def __repr__(self):
        return f'<ProductAttribute {self.name}>'


class ProductAttributeValue(db.Model):
    """Specific values for attributes (S, M, L, XL for Size)."""
    __tablename__ = 'product_attribute_value'
    id = db.Column(db.Integer, primary_key=True)
    attribute_id = db.Column(db.Integer, db.ForeignKey('product_attribute.id'), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False)
    color_hex = db.Column(db.String(7), nullable=True)  # For color swatches (#FF0000)
    image_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)
    position = db.Column(db.Integer, default=0)
    
    image = db.relationship('Media')
    
    __table_args__ = (
        db.UniqueConstraint('attribute_id', 'slug', name='uq_attr_value_slug'),
        Index('idx_attr_value_attr', 'attribute_id', 'position'),
    )
    
    def __repr__(self):
        return f'<ProductAttributeValue {self.value}>'


class ProductAttributeAssignment(db.Model):
    """Link attributes to products."""
    __tablename__ = 'product_attribute_assignment'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey('product_attribute.id'), nullable=False)
    position = db.Column(db.Integer, default=0)
    
    product = db.relationship('Product', backref=db.backref('attribute_assignments', lazy='dynamic'))
    attribute = db.relationship('ProductAttribute')
    
    __table_args__ = (
        db.UniqueConstraint('product_id', 'attribute_id', name='uq_product_attr'),
    )
    
    def __repr__(self):
        return f'<ProductAttributeAssignment product={self.product_id} attr={self.attribute_id}>'


class Collection(db.Model):
    """Smart or manual product groupings."""
    __tablename__ = 'collection'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    image_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)
    collection_type = db.Column(db.String(20), default='manual')  # manual, smart
    is_published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.String(50), default='manual')  # manual, best_selling, newest, price_asc, price_desc, alpha
    seo_title = db.Column(db.String(200), nullable=True)
    seo_description = db.Column(db.Text, nullable=True)
    show_on_homepage = db.Column(db.Boolean, default=False)
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    image = db.relationship('Media')
    rules = db.relationship('CollectionRule', backref='collection', lazy='dynamic', cascade='all, delete-orphan')
    products = db.relationship('CollectionProduct', backref='collection', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_collection_published', 'is_published'),
        Index('idx_collection_homepage', 'show_on_homepage'),
    )
    
    def __repr__(self):
        return f'<Collection {self.name}>'
    
    def is_active(self):
        """Check if collection is currently active based on date range."""
        now = datetime.utcnow()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return self.is_published


class CollectionRule(db.Model):
    """Auto-population rules for smart collections."""
    __tablename__ = 'collection_rule'
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    field = db.Column(db.String(50), nullable=False)  # category, tag, price, in_stock, product_type
    condition = db.Column(db.String(50), nullable=False)  # equals, not_equals, contains, greater_than, less_than
    value = db.Column(db.String(200), nullable=False)
    
    __table_args__ = (
        Index('idx_collection_rule', 'collection_id'),
    )
    
    def __repr__(self):
        return f'<CollectionRule {self.field} {self.condition} {self.value}>'


class CollectionProduct(db.Model):
    """Manual product assignments with ordering."""
    __tablename__ = 'collection_product'
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    position = db.Column(db.Integer, default=0)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')
    
    __table_args__ = (
        db.UniqueConstraint('collection_id', 'product_id', name='uq_collection_product'),
        Index('idx_collection_product_pos', 'collection_id', 'position'),
    )
    
    def __repr__(self):
        return f'<CollectionProduct collection={self.collection_id} product={self.product_id}>'


class ProductBundle(db.Model):
    """Bundle products together at special pricing."""
    __tablename__ = 'product_bundle'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    bundle_price_cents = db.Column(db.Integer, nullable=True)  # Fixed bundle price, or null for discount-based
    discount_type = db.Column(db.String(20), default='percentage')  # percentage, fixed_amount
    discount_value = db.Column(db.Integer, default=0)  # Percentage or cents off
    image_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    requires_all_items = db.Column(db.Boolean, default=True)
    min_items = db.Column(db.Integer, nullable=True)
    max_items = db.Column(db.Integer, nullable=True)
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    image = db.relationship('Media')
    items = db.relationship('BundleItem', backref='bundle', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ProductBundle {self.name}>'
    
    def get_original_price(self):
        """Calculate total of individual item prices."""
        total = 0
        for item in self.items:
            if item.variant_id and item.variant:
                total += item.variant.get_price() * item.quantity
            elif item.product:
                total += item.product.price * item.quantity
        return total
    
    def get_bundle_price(self):
        """Calculate bundle price after discount."""
        if self.bundle_price_cents:
            return self.bundle_price_cents
        original = self.get_original_price()
        if self.discount_type == 'percentage':
            return int(original * (100 - self.discount_value) / 100)
        else:
            return max(0, original - self.discount_value)
    
    def get_savings(self):
        """Calculate savings from buying bundle."""
        return self.get_original_price() - self.get_bundle_price()


class BundleItem(db.Model):
    """Items included in a bundle."""
    __tablename__ = 'bundle_item'
    id = db.Column(db.Integer, primary_key=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('product_bundle.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    is_optional = db.Column(db.Boolean, default=False)
    is_default_selected = db.Column(db.Boolean, default=True)
    
    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')
    
    __table_args__ = (
        Index('idx_bundle_item', 'bundle_id'),
    )
    
    def __repr__(self):
        return f'<BundleItem bundle={self.bundle_id} product={self.product_id} x{self.quantity}>'


class ProductImage(db.Model):
    """Multiple images per product with positioning."""
    __tablename__ = 'product_image'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    alt_text = db.Column(db.String(255), nullable=True)
    position = db.Column(db.Integer, default=0)
    is_primary = db.Column(db.Boolean, default=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)
    image_type = db.Column(db.String(50), default='photo')  # photo, lifestyle, diagram
    
    product = db.relationship('Product', backref=db.backref('images', lazy='dynamic', order_by='ProductImage.position'))
    media = db.relationship('Media')
    variant = db.relationship('ProductVariant')
    
    __table_args__ = (
        Index('idx_product_image', 'product_id', 'position'),
        Index('idx_product_image_primary', 'product_id', 'is_primary'),
    )
    
    def __repr__(self):
        return f'<ProductImage product={self.product_id} pos={self.position}>'


class Discount(db.Model):
    """Coupon codes and automatic discounts."""
    __tablename__ = 'discount'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=True, index=True)  # Null for automatic discounts
    name = db.Column(db.String(200), nullable=False)
    discount_type = db.Column(db.String(50), nullable=False)  # percentage, fixed_amount, buy_x_get_y, free_shipping
    value = db.Column(db.Integer, nullable=False)  # Percentage (10 = 10%) or cents
    minimum_order_cents = db.Column(db.Integer, default=0)
    maximum_discount_cents = db.Column(db.Integer, nullable=True)  # Cap on savings
    maximum_uses = db.Column(db.Integer, nullable=True)  # Total uses allowed, null = unlimited
    used_count = db.Column(db.Integer, default=0)
    usage_limit_per_customer = db.Column(db.Integer, nullable=True)  # Per-user limit
    applies_to = db.Column(db.String(50), default='all')  # all, specific_products, specific_collections
    applies_to_ids = db.Column(db.JSON, default=list)  # Product or Collection IDs
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_automatic = db.Column(db.Boolean, default=False)  # Auto-apply without code
    combine_with_other_discounts = db.Column(db.Boolean, default=False)
    customer_eligibility = db.Column(db.String(50), default='all')  # all, new_customers, returning_customers
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = db.relationship('User')
    rules = db.relationship('DiscountRule', backref='discount', lazy='dynamic', cascade='all, delete-orphan')
    usages = db.relationship('DiscountUsage', backref='discount', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_discount_code', 'code'),
        Index('idx_discount_active', 'is_active', 'starts_at', 'ends_at'),
        Index('idx_discount_automatic', 'is_automatic', 'is_active'),
    )
    
    def __repr__(self):
        return f'<Discount {self.code or self.name}>'
    
    def is_valid(self, cart_total_cents, user=None):
        """Check if discount is currently valid."""
        now = datetime.utcnow()
        if not self.is_active:
            return False, "Discount is not active"
        if self.starts_at and now < self.starts_at:
            return False, "Discount has not started yet"
        if self.ends_at and now > self.ends_at:
            return False, "Discount has expired"
        if self.maximum_uses and self.used_count >= self.maximum_uses:
            return False, "Discount usage limit reached"
        if cart_total_cents < self.minimum_order_cents:
            return False, f"Minimum order of ${self.minimum_order_cents/100:.2f} required"
        if user and self.usage_limit_per_customer:
            user_uses = self.usages.filter_by(user_id=user.id).count()
            if user_uses >= self.usage_limit_per_customer:
                return False, "You have already used this discount"
        return True, None
    
    def calculate_savings(self, cart_total_cents):
        """Calculate discount amount for given cart total."""
        if self.discount_type == 'percentage':
            savings = int(cart_total_cents * self.value / 100)
        elif self.discount_type == 'fixed_amount':
            savings = self.value
        elif self.discount_type == 'free_shipping':
            return 0  # Handled separately in shipping calculation
        else:
            savings = 0
        
        if self.maximum_discount_cents:
            savings = min(savings, self.maximum_discount_cents)
        return min(savings, cart_total_cents)  # Can't save more than cart total


class DiscountRule(db.Model):
    """Conditions for automatic discount application."""
    __tablename__ = 'discount_rule'
    id = db.Column(db.Integer, primary_key=True)
    discount_id = db.Column(db.Integer, db.ForeignKey('discount.id'), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False)  # min_quantity, min_amount, customer_tag, first_order, specific_product, specific_collection
    condition = db.Column(db.String(50), nullable=False)  # equals, greater_than, less_than, contains
    value = db.Column(db.String(200), nullable=False)
    
    __table_args__ = (
        Index('idx_discount_rule', 'discount_id'),
    )
    
    def __repr__(self):
        return f'<DiscountRule {self.rule_type} {self.condition} {self.value}>'


class DiscountUsage(db.Model):
    """Track discount usage per order/user."""
    __tablename__ = 'discount_usage'
    id = db.Column(db.Integer, primary_key=True)
    discount_id = db.Column(db.Integer, db.ForeignKey('discount.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    amount_saved_cents = db.Column(db.Integer, nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order = db.relationship('Order')
    user = db.relationship('User')
    
    __table_args__ = (
        Index('idx_discount_usage_order', 'order_id'),
        Index('idx_discount_usage_user', 'user_id'),
    )
    
    def __repr__(self):
        return f'<DiscountUsage discount={self.discount_id} order={self.order_id}>'


class GiftCard(db.Model):
    """Gift card with balance tracking."""
    __tablename__ = 'gift_card'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    initial_balance_cents = db.Column(db.Integer, nullable=False)
    current_balance_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), default='usd')
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    recipient_email = db.Column(db.String(120), nullable=True)
    recipient_name = db.Column(db.String(100), nullable=True)
    sender_name = db.Column(db.String(100), nullable=True)
    message = db.Column(db.Text, nullable=True)
    purchased_order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_by = db.relationship('User')
    purchased_order = db.relationship('Order')
    transactions = db.relationship('GiftCardTransaction', backref='gift_card', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_gift_card_code', 'code'),
        Index('idx_gift_card_active', 'is_active'),
    )
    
    def __repr__(self):
        return f'<GiftCard {self.code[:8]}... ${self.current_balance_cents/100:.2f}>'
    
    def is_valid(self):
        """Check if gift card can be used."""
        if not self.is_active:
            return False, "Gift card is not active"
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False, "Gift card has expired"
        if self.current_balance_cents <= 0:
            return False, "Gift card has no remaining balance"
        return True, None
    
    def redeem(self, amount_cents, order_id, note=None):
        """Redeem amount from gift card. Returns amount actually redeemed."""
        redeemed = min(amount_cents, self.current_balance_cents)
        self.current_balance_cents -= redeemed
        
        transaction = GiftCardTransaction(
            gift_card_id=self.id,
            order_id=order_id,
            amount_cents=-redeemed,
            transaction_type='redemption',
            note=note
        )
        db.session.add(transaction)
        return redeemed


class GiftCardTransaction(db.Model):
    """Balance changes: purchases, redemptions, refunds."""
    __tablename__ = 'gift_card_transaction'
    id = db.Column(db.Integer, primary_key=True)
    gift_card_id = db.Column(db.Integer, db.ForeignKey('gift_card.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    amount_cents = db.Column(db.Integer, nullable=False)  # Positive for additions, negative for redemptions
    transaction_type = db.Column(db.String(50), nullable=False)  # purchase, redemption, refund, adjustment, expiry
    note = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order = db.relationship('Order')
    created_by = db.relationship('User')
    
    __table_args__ = (
        Index('idx_gift_card_tx', 'gift_card_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<GiftCardTransaction {self.transaction_type} ${self.amount_cents/100:.2f}>'


class ShippingZone(db.Model):
    """Geographic shipping zones."""
    __tablename__ = 'shipping_zone'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    countries = db.Column(db.JSON, default=list)  # ['US', 'CA']
    states = db.Column(db.JSON, default=list)  # ['US-CA', 'US-NY'] - ISO format
    zip_codes = db.Column(db.JSON, default=list)  # ['90210', '10001']
    is_rest_of_world = db.Column(db.Boolean, default=False)  # Catch-all zone
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    rates = db.relationship('ShippingRate', backref='zone', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ShippingZone {self.name}>'
    
    def matches_address(self, country, state=None, zip_code=None):
        """Check if address matches this zone."""
        if self.is_rest_of_world:
            return True  # Matched as fallback
        if country in self.countries:
            return True
        if state and f"{country}-{state}" in self.states:
            return True
        if zip_code and zip_code in self.zip_codes:
            return True
        return False


class ShippingRate(db.Model):
    """Rates per zone with conditions."""
    __tablename__ = 'shipping_rate'
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('shipping_zone.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # "Standard Shipping", "Express"
    rate_type = db.Column(db.String(50), default='flat')  # flat, weight_based, price_based, free
    price_cents = db.Column(db.Integer, default=0)
    price_per_kg_cents = db.Column(db.Integer, nullable=True)  # For weight-based
    min_weight_grams = db.Column(db.Integer, nullable=True)
    max_weight_grams = db.Column(db.Integer, nullable=True)
    min_order_cents = db.Column(db.Integer, nullable=True)
    max_order_cents = db.Column(db.Integer, nullable=True)
    free_shipping_threshold_cents = db.Column(db.Integer, nullable=True)
    estimated_days_min = db.Column(db.Integer, nullable=True)
    estimated_days_max = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (
        Index('idx_shipping_rate_zone', 'zone_id'),
    )
    
    def __repr__(self):
        return f'<ShippingRate {self.name} ${self.price_cents/100:.2f}>'
    
    def calculate_rate(self, order_total_cents, weight_grams=0):
        """Calculate shipping rate for given order."""
        # Check if free shipping threshold met
        if self.free_shipping_threshold_cents and order_total_cents >= self.free_shipping_threshold_cents:
            return 0
        
        if self.rate_type == 'free':
            return 0
        elif self.rate_type == 'flat':
            return self.price_cents
        elif self.rate_type == 'weight_based' and self.price_per_kg_cents:
            return self.price_cents + int(weight_grams / 1000 * self.price_per_kg_cents)
        elif self.rate_type == 'price_based':
            # Price-based tiers handled by min/max order
            return self.price_cents
        return self.price_cents
    
    def is_applicable(self, order_total_cents, weight_grams=0):
        """Check if this rate applies to the given order."""
        if not self.is_active:
            return False
        if self.min_order_cents and order_total_cents < self.min_order_cents:
            return False
        if self.max_order_cents and order_total_cents > self.max_order_cents:
            return False
        if self.min_weight_grams and weight_grams < self.min_weight_grams:
            return False
        if self.max_weight_grams and weight_grams > self.max_weight_grams:
            return False
        return True


class TaxRate(db.Model):
    """Tax rates by jurisdiction."""
    __tablename__ = 'tax_rate'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # "California Sales Tax"
    rate = db.Column(db.Float, nullable=False)  # 0.0825 = 8.25%
    country = db.Column(db.String(2), nullable=True)  # ISO country code
    state = db.Column(db.String(10), nullable=True)  # State/province code
    zip_code = db.Column(db.String(20), nullable=True)  # Specific zip code
    tax_type = db.Column(db.String(50), default='sales')  # sales, vat, gst
    applies_to_shipping = db.Column(db.Boolean, default=False)
    is_compound = db.Column(db.Boolean, default=False)  # Applied after other taxes
    priority = db.Column(db.Integer, default=0)  # Order of application
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_tax_rate_location', 'country', 'state', 'zip_code'),
        Index('idx_tax_rate_priority', 'priority'),
    )
    
    def __repr__(self):
        return f'<TaxRate {self.name} {self.rate*100:.2f}%>'
    
    def matches_address(self, country, state=None, zip_code=None):
        """Check if tax rate applies to address."""
        if self.zip_code and self.zip_code == zip_code:
            return True
        if self.state and self.state == state and (not self.country or self.country == country):
            return True
        if self.country and self.country == country and not self.state and not self.zip_code:
            return True
        return False


class Wishlist(db.Model):
    """User wishlist/saved items."""
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('wishlist_items', lazy='dynamic'))
    product = db.relationship('Product')
    variant = db.relationship('ProductVariant')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', 'variant_id', name='uq_wishlist_item'),
        Index('idx_wishlist_user', 'user_id'),
    )
    
    def __repr__(self):
        return f'<Wishlist user={self.user_id} product={self.product_id}>'


class RecentlyViewed(db.Model):
    """Track recently viewed products per user/session."""
    __tablename__ = 'recently_viewed'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    session_id = db.Column(db.String(64), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    product = db.relationship('Product')
    
    __table_args__ = (
        Index('idx_recently_viewed_user', 'user_id', 'viewed_at'),
        Index('idx_recently_viewed_session', 'session_id', 'viewed_at'),
    )
    
    def __repr__(self):
        return f'<RecentlyViewed product={self.product_id}>'


class RelatedProduct(db.Model):
    """Cross-sell and up-sell relationships."""
    __tablename__ = 'related_product'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    related_product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False)  # cross_sell, up_sell, accessory, frequently_bought_together
    position = db.Column(db.Integer, default=0)
    is_auto_generated = db.Column(db.Boolean, default=False)  # True if generated by algorithm
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', foreign_keys=[product_id], backref=db.backref('related_products_out', lazy='dynamic'))
    related_product = db.relationship('Product', foreign_keys=[related_product_id])
    
    __table_args__ = (
        db.UniqueConstraint('product_id', 'related_product_id', 'relation_type', name='uq_related_product'),
        Index('idx_related_product', 'product_id', 'relation_type'),
    )
    
    def __repr__(self):
        return f'<RelatedProduct {self.product_id} -> {self.related_product_id} ({self.relation_type})>'


# ============================================================================
# Phase 14: Analytics & Reporting Engine Models
# ============================================================================

class VisitorSession(db.Model):
    """Track visitor sessions with entry/exit pages and engagement metrics."""
    __tablename__ = 'visitor_session'
    id = db.Column(db.Integer, primary_key=True)
    session_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_hash = db.Column(db.String(64), nullable=True)
    
    # Session flow
    entry_page = db.Column(db.String(500), nullable=True)
    exit_page = db.Column(db.String(500), nullable=True)
    pages_viewed = db.Column(db.Integer, default=1)
    duration_seconds = db.Column(db.Integer, nullable=True)
    bounce = db.Column(db.Boolean, default=True)  # True if only 1 page viewed
    
    # Source tracking
    referrer = db.Column(db.String(500), nullable=True)
    utm_source = db.Column(db.String(100), nullable=True)
    utm_medium = db.Column(db.String(100), nullable=True)
    utm_campaign = db.Column(db.String(100), nullable=True)
    
    # Device info
    device_type = db.Column(db.String(20), nullable=True)  # desktop, mobile, tablet
    browser = db.Column(db.String(50), nullable=True)
    os = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('sessions', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_session_started', 'started_at'),
        Index('idx_session_user', 'user_id'),
        Index('idx_session_utm', 'utm_source', 'utm_medium'),
    )
    
    def update_activity(self, page_url):
        """Update session with new page activity."""
        self.pages_viewed += 1
        self.exit_page = page_url
        self.last_activity_at = datetime.utcnow()
        self.bounce = False
        if self.started_at:
            self.duration_seconds = int((datetime.utcnow() - self.started_at).total_seconds())
    
    def end_session(self):
        """Mark session as ended."""
        self.ended_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = int((self.ended_at - self.started_at).total_seconds())
    
    def __repr__(self):
        return f'<VisitorSession {self.session_token[:8]}... pages={self.pages_viewed}>'


class ConversionGoal(db.Model):
    """Define conversion goals for tracking."""
    __tablename__ = 'conversion_goal'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    goal_type = db.Column(db.String(50), nullable=False)  # page_visit, form_submit, purchase, signup, custom
    
    # Goal conditions
    target_path = db.Column(db.String(500), nullable=True)  # URL pattern for page_visit goals
    target_value = db.Column(db.Float, nullable=True)  # Monetary value of conversion
    
    # Tracking settings
    is_active = db.Column(db.Boolean, default=True)
    count_once_per_session = db.Column(db.Boolean, default=True)  # Only count once per session
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    created_by = db.relationship('User')
    conversions = db.relationship('Conversion', backref='goal', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_goal_active', 'is_active'),
        Index('idx_goal_type', 'goal_type'),
    )
    
    def __repr__(self):
        return f'<ConversionGoal {self.name} ({self.goal_type})>'


class Conversion(db.Model):
    """Track individual conversion events."""
    __tablename__ = 'conversion'
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('conversion_goal.id'), nullable=False)
    session_id = db.Column(db.String(64), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Conversion details
    value = db.Column(db.Float, nullable=True)  # Actual conversion value (e.g., order total)
    source = db.Column(db.String(100), nullable=True)  # utm_source at time of conversion
    medium = db.Column(db.String(100), nullable=True)  # utm_medium at time of conversion
    campaign = db.Column(db.String(100), nullable=True)  # utm_campaign at time of conversion
    
    # Attribution
    first_touch_source = db.Column(db.String(100), nullable=True)
    last_touch_source = db.Column(db.String(100), nullable=True)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref=db.backref('conversions', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_conversion_goal_time', 'goal_id', 'timestamp'),
        Index('idx_conversion_session', 'session_id'),
    )
    
    def __repr__(self):
        return f'<Conversion goal={self.goal_id} value={self.value}>'


class Funnel(db.Model):
    """Conversion funnel definition."""
    __tablename__ = 'funnel'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    created_by = db.relationship('User')
    steps = db.relationship('FunnelStep', backref='funnel', lazy='dynamic', 
                           order_by='FunnelStep.step_order', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Funnel {self.name}>'
    
    def calculate_conversion_rates(self, start_date=None, end_date=None):
        """Calculate conversion rates between funnel steps."""
        from sqlalchemy import func
        
        rates = []
        steps = self.steps.order_by(FunnelStep.step_order).all()
        
        for i, step in enumerate(steps):
            query = Conversion.query.filter_by(goal_id=step.goal_id)
            if start_date:
                query = query.filter(Conversion.timestamp >= start_date)
            if end_date:
                query = query.filter(Conversion.timestamp <= end_date)
            
            count = query.count()
            
            if i == 0:
                rate = 100.0
                drop_off = 0
            else:
                prev_count = rates[i-1]['count'] if rates else 0
                rate = (count / prev_count * 100) if prev_count > 0 else 0
                drop_off = prev_count - count
            
            rates.append({
                'step': step,
                'count': count,
                'rate': round(rate, 2),
                'drop_off': drop_off
            })
        
        return rates


class FunnelStep(db.Model):
    """Individual step in a conversion funnel."""
    __tablename__ = 'funnel_step'
    id = db.Column(db.Integer, primary_key=True)
    funnel_id = db.Column(db.Integer, db.ForeignKey('funnel.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('conversion_goal.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Step display name
    step_order = db.Column(db.Integer, nullable=False)  # Position in funnel
    
    goal = db.relationship('ConversionGoal')
    
    __table_args__ = (
        Index('idx_funnelstep_funnel_order', 'funnel_id', 'step_order'),
        db.UniqueConstraint('funnel_id', 'step_order', name='uq_funnel_step_order'),
    )
    
    def __repr__(self):
        return f'<FunnelStep {self.name} (step {self.step_order})>'


class SavedReport(db.Model):
    """User-created saved report configurations."""
    __tablename__ = 'saved_report'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    report_type = db.Column(db.String(50), nullable=False)  # revenue, products, customers, traffic, custom
    
    # Report configuration stored as JSON
    config_json = db.Column(db.JSON, default=dict)  # Filters, groupings, date range, etc.
    
    # Scheduling (optional)
    schedule_cron = db.Column(db.String(50), nullable=True)  # Cron expression for scheduled runs
    last_run_at = db.Column(db.DateTime, nullable=True)
    next_run_at = db.Column(db.DateTime, nullable=True)
    
    # Permissions
    is_public = db.Column(db.Boolean, default=False)  # Visible to all admins
    is_archived = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    created_by = db.relationship('User', backref=db.backref('saved_reports', lazy='dynamic'))
    exports = db.relationship('ReportExport', backref='report', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_report_type', 'report_type'),
        Index('idx_report_created_by', 'created_by_id'),
    )
    
    def __repr__(self):
        return f'<SavedReport {self.name} ({self.report_type})>'


class ReportExport(db.Model):
    """Track generated report exports."""
    __tablename__ = 'report_export'
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('saved_report.id'), nullable=True)  # Nullable for ad-hoc exports
    report_type = db.Column(db.String(50), nullable=False)  # revenue, products, etc.
    
    # Export details
    format = db.Column(db.String(10), nullable=False)  # csv, pdf, xlsx
    file_path = db.Column(db.String(500), nullable=True)  # Path to generated file
    file_size_bytes = db.Column(db.Integer, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text, nullable=True)
    
    # Usage tracking
    download_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime, nullable=True)  # Auto-delete after this date
    
    generated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    generated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    generated_by = db.relationship('User')
    
    __table_args__ = (
        Index('idx_export_status', 'status'),
        Index('idx_export_created', 'created_at'),
    )
    
    def is_expired(self):
        """Check if export has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def increment_download(self):
        """Increment download counter."""
        self.download_count += 1
    
    def __repr__(self):
        return f'<ReportExport {self.format} {self.status}>'


# ============================================================================
# Phase 15: Communication Hub Expansion Models
# ============================================================================


class Audience(db.Model):
    """Dynamic or static email audience segments."""
    __tablename__ = 'audience'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Filter rules for dynamic audiences
    # Format: [{"field": "created_at", "operator": "gte", "value": "30_days_ago"}, ...]
    filter_rules = db.Column(db.JSON, default=list)
    
    is_dynamic = db.Column(db.Boolean, default=True)  # Dynamic recalculates, static uses AudienceMember
    member_count = db.Column(db.Integer, default=0)  # Cached count
    last_calculated_at = db.Column(db.DateTime, nullable=True)
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = db.relationship('User', backref=db.backref('audiences', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_audience_dynamic', 'is_dynamic'),
    )
    
    def __repr__(self):
        return f'<Audience {self.name} ({"dynamic" if self.is_dynamic else "static"})>'


class AudienceMember(db.Model):
    """Static audience membership for non-dynamic segments."""
    __tablename__ = 'audience_member'
    id = db.Column(db.Integer, primary_key=True)
    audience_id = db.Column(db.Integer, db.ForeignKey('audience.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email = db.Column(db.String(120), nullable=False)  # For non-user subscribers
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    audience = db.relationship('Audience', backref=db.backref('members', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('audience_memberships', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('audience_id', 'email', name='uq_audience_member_email'),
        Index('idx_audience_member_audience', 'audience_id'),
    )
    
    def __repr__(self):
        return f'<AudienceMember {self.email} in audience {self.audience_id}>'


class EmailCampaign(db.Model):
    """Email marketing campaign."""
    __tablename__ = 'email_campaign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'), nullable=False)
    audience_id = db.Column(db.Integer, db.ForeignKey('audience.id'), nullable=True)
    
    # Campaign status
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, sending, sent, paused, cancelled
    
    # Scheduling
    scheduled_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # A/B Testing
    subject_line_a = db.Column(db.String(200), nullable=True)  # Override template subject
    subject_line_b = db.Column(db.String(200), nullable=True)  # Variant B
    ab_test_percentage = db.Column(db.Integer, default=0)  # 0 = no A/B test
    
    # Stats (updated by worker)
    sent_count = db.Column(db.Integer, default=0)
    delivered_count = db.Column(db.Integer, default=0)
    open_count = db.Column(db.Integer, default=0)
    unique_open_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    unique_click_count = db.Column(db.Integer, default=0)
    unsubscribe_count = db.Column(db.Integer, default=0)
    bounce_count = db.Column(db.Integer, default=0)
    complaint_count = db.Column(db.Integer, default=0)
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    template = db.relationship('EmailTemplate', backref=db.backref('campaigns', lazy='dynamic'))
    audience = db.relationship('Audience', backref=db.backref('campaigns', lazy='dynamic'))
    created_by = db.relationship('User', backref=db.backref('email_campaigns', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_campaign_status', 'status'),
        Index('idx_campaign_scheduled', 'scheduled_at'),
    )
    
    def open_rate(self):
        """Calculate open rate percentage."""
        if self.sent_count == 0:
            return 0
        return round((self.unique_open_count / self.sent_count) * 100, 2)
    
    def click_rate(self):
        """Calculate click rate percentage."""
        if self.sent_count == 0:
            return 0
        return round((self.unique_click_count / self.sent_count) * 100, 2)
    
    def __repr__(self):
        return f'<EmailCampaign {self.name} ({self.status})>'


class EmailSend(db.Model):
    """Individual email send tracking for deliverability and engagement."""
    __tablename__ = 'email_send'
    id = db.Column(db.Integer, primary_key=True)
    
    # Campaign or transactional
    campaign_id = db.Column(db.Integer, db.ForeignKey('email_campaign.id'), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'), nullable=True)  # For transactional
    
    # Recipient
    recipient_email = db.Column(db.String(120), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Tracking token (used in pixel/links)
    tracking_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # A/B test variant
    variant = db.Column(db.String(1), nullable=True)  # 'A' or 'B'
    
    # Timestamps
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivered_at = db.Column(db.DateTime, nullable=True)
    first_opened_at = db.Column(db.DateTime, nullable=True)
    last_opened_at = db.Column(db.DateTime, nullable=True)
    first_clicked_at = db.Column(db.DateTime, nullable=True)
    
    # Engagement counts
    open_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    
    # Status flags
    bounced = db.Column(db.Boolean, default=False)
    bounce_type = db.Column(db.String(20), nullable=True)  # hard, soft, complaint
    bounce_reason = db.Column(db.Text, nullable=True)
    unsubscribed = db.Column(db.Boolean, default=False)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)
    complained = db.Column(db.Boolean, default=False)  # Spam complaint
    
    campaign = db.relationship('EmailCampaign', backref=db.backref('sends', lazy='dynamic'))
    template = db.relationship('EmailTemplate', backref=db.backref('sends', lazy='dynamic'))
    recipient = db.relationship('User', backref=db.backref('email_sends', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_email_send_campaign', 'campaign_id'),
        Index('idx_email_send_recipient', 'recipient_email'),
        Index('idx_email_send_sent', 'sent_at'),
        Index('idx_email_send_token', 'tracking_token'),
    )
    
    def record_open(self):
        """Record an email open event."""
        now = datetime.utcnow()
        if self.first_opened_at is None:
            self.first_opened_at = now
        self.last_opened_at = now
        self.open_count += 1
    
    def record_click(self):
        """Record a click event."""
        now = datetime.utcnow()
        if self.first_clicked_at is None:
            self.first_clicked_at = now
        self.click_count += 1
    
    def __repr__(self):
        return f'<EmailSend {self.recipient_email} campaign={self.campaign_id}>'


class EmailClickTrack(db.Model):
    """Track individual link clicks for detailed analytics."""
    __tablename__ = 'email_click_track'
    id = db.Column(db.Integer, primary_key=True)
    email_send_id = db.Column(db.Integer, db.ForeignKey('email_send.id'), nullable=False)
    original_url = db.Column(db.String(2000), nullable=False)
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(500), nullable=True)
    ip_hash = db.Column(db.String(64), nullable=True)
    
    email_send = db.relationship('EmailSend', backref=db.backref('click_details', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_click_track_send', 'email_send_id'),
    )
    
    def __repr__(self):
        return f'<EmailClickTrack {self.original_url[:50]}>'


class DripSequence(db.Model):
    """Multi-step email automation sequence (drip campaign)."""
    __tablename__ = 'drip_sequence'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Trigger configuration
    trigger_event = db.Column(db.String(50), nullable=False)  # user_signup, order_placed, form_submit, manual
    trigger_config = db.Column(db.JSON, default=dict)  # Additional trigger criteria
    
    # Steps configuration
    # Format: [{"order": 1, "template_id": 5, "delay_hours": 0}, {"order": 2, "template_id": 6, "delay_hours": 24}, ...]
    steps_config = db.Column(db.JSON, default=list)
    
    is_active = db.Column(db.Boolean, default=False)
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = db.relationship('User', backref=db.backref('drip_sequences', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_drip_sequence_trigger', 'trigger_event'),
        Index('idx_drip_sequence_active', 'is_active'),
    )
    
    def get_step(self, step_order):
        """Get step configuration by order."""
        for step in (self.steps_config or []):
            if step.get('order') == step_order:
                return step
        return None
    
    def __repr__(self):
        return f'<DripSequence {self.name} trigger={self.trigger_event}>'


class SequenceEnrollment(db.Model):
    """Track user progress through a drip sequence."""
    __tablename__ = 'sequence_enrollment'
    id = db.Column(db.Integer, primary_key=True)
    sequence_id = db.Column(db.Integer, db.ForeignKey('drip_sequence.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email = db.Column(db.String(120), nullable=False)  # For non-users
    
    current_step = db.Column(db.Integer, default=0)  # 0 = not started
    next_step_at = db.Column(db.DateTime, nullable=True)  # When to process next step
    
    status = db.Column(db.String(20), default='active')  # active, paused, completed, unsubscribed
    
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Context data passed to templates
    context_data = db.Column(db.JSON, default=dict)
    
    sequence = db.relationship('DripSequence', backref=db.backref('enrollments', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('sequence_enrollments', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_enrollment_sequence', 'sequence_id'),
        Index('idx_enrollment_status', 'status'),
        Index('idx_enrollment_next_step', 'next_step_at'),
    )
    
    def advance_to_next_step(self):
        """Move to the next step in the sequence."""
        seq = self.sequence
        next_order = self.current_step + 1
        next_step = seq.get_step(next_order)
        
        if next_step:
            self.current_step = next_order
            delay_hours = next_step.get('delay_hours', 0)
            self.next_step_at = datetime.utcnow() + timedelta(hours=delay_hours)
        else:
            # Sequence complete
            self.status = 'completed'
            self.completed_at = datetime.utcnow()
            self.next_step_at = None
    
    def __repr__(self):
        return f'<SequenceEnrollment {self.email} step={self.current_step}>'


class PushSubscription(db.Model):
    """Web push notification subscriptions (VAPID)."""
    __tablename__ = 'push_subscription'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Web Push subscription data
    endpoint = db.Column(db.Text, nullable=False)
    p256dh_key = db.Column(db.String(200), nullable=False)  # Public key
    auth_key = db.Column(db.String(50), nullable=False)  # Auth secret
    
    # Device/browser info
    user_agent = db.Column(db.String(500), nullable=True)
    device_name = db.Column(db.String(100), nullable=True)  # User-friendly name
    
    # Category preferences (which notification types to receive)
    categories = db.Column(db.JSON, default=list)  # ['orders', 'messages', 'appointments', 'marketing']
    
    is_active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref=db.backref('push_subscriptions', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_push_sub_user', 'user_id'),
        Index('idx_push_sub_active', 'is_active'),
    )
    
    def to_webpush_dict(self):
        """Convert to format expected by pywebpush."""
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh_key,
                'auth': self.auth_key
            }
        }
    
    def __repr__(self):
        return f'<PushSubscription user={self.user_id} active={self.is_active}>'


class SMSTemplate(db.Model):
    """SMS message templates."""
    __tablename__ = 'sms_template'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    body = db.Column(db.String(1600), nullable=False)  # Max SMS length with segments
    
    # Variable schema
    variables_schema = db.Column(db.JSON, default=dict)
    
    # SMS metrics
    character_count = db.Column(db.Integer, default=0)
    segment_count = db.Column(db.Integer, default=1)  # Number of SMS segments
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = db.relationship('User', backref=db.backref('sms_templates', lazy='dynamic'))
    
    def calculate_segments(self):
        """Calculate number of SMS segments based on character count."""
        length = len(self.body)
        self.character_count = length
        if length <= 160:
            self.segment_count = 1
        else:
            # Multi-part messages use 153 chars per segment
            self.segment_count = (length + 152) // 153
        return self.segment_count
    
    def render(self, context):
        """Render template with variable substitution."""
        body = self.body
        schema = self.variables_schema or {}
        
        for var_name, var_config in schema.items():
            placeholder = '{{' + var_name + '}}'
            value = context.get(var_name, var_config.get('default', ''))
            body = body.replace(placeholder, str(value))
        
        for key, value in context.items():
            placeholder = '{{' + key + '}}'
            body = body.replace(placeholder, str(value))
        
        return body
    
    def __repr__(self):
        return f'<SMSTemplate {self.name} ({self.segment_count} segments)>'


class SMSConsent(db.Model):
    """TCPA-compliant SMS consent tracking."""
    __tablename__ = 'sms_consent'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    phone_number = db.Column(db.String(20), nullable=False, index=True)
    
    # Consent status
    consented = db.Column(db.Boolean, default=False)
    consented_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    
    # Consent source for compliance
    consent_source = db.Column(db.String(100), nullable=True)  # 'checkout', 'settings', 'form', etc.
    consent_text = db.Column(db.Text, nullable=True)  # The actual consent text shown
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    
    # Categories opted into
    categories = db.Column(db.JSON, default=list)  # ['transactional', 'marketing', 'reminders']
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('sms_consents', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_sms_consent_phone', 'phone_number'),
        Index('idx_sms_consent_user', 'user_id'),
    )
    
    def is_valid(self):
        """Check if consent is currently valid."""
        return self.consented and self.revoked_at is None
    
    def revoke(self):
        """Revoke SMS consent."""
        self.consented = False
        self.revoked_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<SMSConsent {self.phone_number} consented={self.consented}>'


class EmailSuppressionList(db.Model):
    """Global email suppression list for bounces, unsubscribes, and complaints."""
    __tablename__ = 'email_suppression_list'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    
    reason = db.Column(db.String(30), nullable=False)  # hard_bounce, unsubscribe, complaint
    source = db.Column(db.String(50), nullable=True)  # campaign_id, manual, etc.
    
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_suppression_reason', 'reason'),
    )
    
    def __repr__(self):
        return f'<EmailSuppressionList {self.email} reason={self.reason}>'


# ============================================================================
# Phase 16: Forms & Data Collection Platform Models
# ============================================================================


class FormDefinition(db.Model):
    """Dynamic form definitions with JSON schema for field configuration."""
    __tablename__ = 'form_definition'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    # Fields schema: JSON array of field definitions
    # Format: [{"name": "email", "type": "email", "label": "Your Email", "required": true, "validation": {...}}, ...]
    fields_schema = db.Column(db.JSON, default=list)
    
    # Form settings
    # Format: {"submit_text": "Submit", "success_message": "Thank you!", "redirect_url": null, "honeypot": true, "rate_limit": 5}
    settings = db.Column(db.JSON, default=dict)
    
    # Multi-page support
    is_multi_page = db.Column(db.Boolean, default=False)
    page_config = db.Column(db.JSON, default=list)  # [{page: 1, title: "Step 1", fields: [...]}, ...]
    
    # Conditional logic
    # Format: [{"condition_field": "type", "operator": "equals", "value": "business", "action": "show", "target_field": "company"}]
    conditional_logic = db.Column(db.JSON, default=list)
    
    is_active = db.Column(db.Boolean, default=True)
    submissions_count = db.Column(db.Integer, default=0)
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = db.relationship('User', backref=db.backref('forms_created', lazy='dynamic'))
    submissions = db.relationship('FormSubmission', backref='form', lazy='dynamic', cascade='all, delete-orphan')
    integrations = db.relationship('FormIntegration', backref='form', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_form_slug', 'slug'),
        Index('idx_form_active', 'is_active'),
    )
    
    def increment_submissions(self):
        """Increment submission counter."""
        self.submissions_count += 1
    
    def get_field(self, field_name):
        """Get field definition by name."""
        for field in (self.fields_schema or []):
            if field.get('name') == field_name:
                return field
        return None
    
    def get_required_fields(self):
        """Get list of required field names."""
        return [f['name'] for f in (self.fields_schema or []) if f.get('required', False)]
    
    def __repr__(self):
        return f'<FormDefinition {self.name} ({self.slug})>'


class FormSubmission(db.Model):
    """Form submission data storage."""
    __tablename__ = 'form_submission'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form_definition.id'), nullable=False)
    
    # Submission data as JSON
    data = db.Column(db.JSON, default=dict)
    
    # Submitter info
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Tracking info
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    
    # UTM params for source tracking
    utm_params = db.Column(db.JSON, default=dict)
    
    # Processing status
    status = db.Column(db.String(20), default='new')  # new, read, processed, archived
    notes = db.Column(db.Text, nullable=True)  # Admin notes
    
    # Spam detection
    is_spam = db.Column(db.Boolean, default=False)
    spam_score = db.Column(db.Float, nullable=True)
    
    # File attachments (if any)
    attachments = db.Column(db.JSON, default=list)  # [{"field": "resume", "path": "...", "filename": "..."}]
    
    submitted_by = db.relationship('User', backref=db.backref('form_submissions', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_submission_form', 'form_id'),
        Index('idx_submission_date', 'submitted_at'),
        Index('idx_submission_status', 'status'),
    )
    
    def mark_as_read(self):
        """Mark submission as read."""
        if self.status == 'new':
            self.status = 'read'
    
    def get_field_value(self, field_name, default=None):
        """Get a specific field value from submission data."""
        return (self.data or {}).get(field_name, default)
    
    def __repr__(self):
        return f'<FormSubmission form={self.form_id} submitted={self.submitted_at}>'


class FormIntegration(db.Model):
    """Integrations triggered on form submission (webhooks, CRM, email)."""
    __tablename__ = 'form_integration'
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('form_definition.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    integration_type = db.Column(db.String(50), nullable=False)  # webhook, crm_lead, email_list, email_notify, slack
    
    # Configuration specific to integration type
    # Webhook: {"url": "...", "method": "POST", "headers": {...}}
    # CRM Lead: {"lead_stage": "new", "field_mapping": {"email": "email", "name": "first_name"}}
    # Email List: {"audience_id": 5, "field_mapping": {...}}
    # Email Notify: {"recipients": ["admin@example.com"], "subject": "New submission"}
    config = db.Column(db.JSON, default=dict)
    
    # Field mapping from form fields to integration fields
    field_mapping = db.Column(db.JSON, default=dict)
    
    is_active = db.Column(db.Boolean, default=True)
    
    # Execution tracking
    last_triggered_at = db.Column(db.DateTime, nullable=True)
    trigger_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_integration_form', 'form_id'),
        Index('idx_integration_type', 'integration_type'),
    )
    
    def record_trigger(self, error=None):
        """Record an integration trigger."""
        self.last_triggered_at = datetime.utcnow()
        self.trigger_count += 1
        self.last_error = error
    
    def __repr__(self):
        return f'<FormIntegration {self.name} ({self.integration_type})>'


class Survey(db.Model):
    """Survey definitions for NPS, CSAT, CES, and custom surveys."""
    __tablename__ = 'survey'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Survey type: nps, csat, ces, custom
    survey_type = db.Column(db.String(20), nullable=False, default='custom')
    
    # Questions schema
    # Format: [{"id": "q1", "type": "rating", "text": "How likely...", "scale": 10, "required": true}, ...]
    questions_schema = db.Column(db.JSON, default=list)
    
    # Trigger configuration
    trigger_event = db.Column(db.String(50), nullable=True)  # order_complete, appointment_complete, manual
    trigger_delay_hours = db.Column(db.Integer, default=0)  # Delay after event
    
    # Display settings
    display_mode = db.Column(db.String(20), default='page')  # page, embed, modal
    thank_you_message = db.Column(db.Text, nullable=True)
    redirect_url = db.Column(db.String(500), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    
    # Stats
    response_count = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, nullable=True)
    
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_by = db.relationship('User', backref=db.backref('surveys_created', lazy='dynamic'))
    responses = db.relationship('SurveyResponse', backref='survey', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_survey_type', 'survey_type'),
        Index('idx_survey_active', 'is_active'),
        Index('idx_survey_trigger', 'trigger_event'),
    )
    
    def calculate_nps(self):
        """Calculate NPS score from responses.
        
        NPS = % Promoters (9-10) - % Detractors (0-6)
        """
        if self.survey_type != 'nps':
            return None
        
        responses = self.responses.all()
        total = len(responses)
        if total == 0:
            return None
        
        promoters = sum(1 for r in responses if r.score and r.score >= 9)
        detractors = sum(1 for r in responses if r.score is not None and r.score <= 6)
        
        return round(((promoters - detractors) / total) * 100, 1)
    
    def __repr__(self):
        return f'<Survey {self.name} ({self.survey_type})>'


class SurveyResponse(db.Model):
    """Individual survey responses."""
    __tablename__ = 'survey_response'
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Response data
    # Format: {"q1": 8, "q2": "Great service!", ...}
    responses = db.Column(db.JSON, default=dict)
    
    # Primary score (NPS 0-10, CSAT 1-5, etc.)
    score = db.Column(db.Integer, nullable=True)
    
    # Classification for NPS
    nps_category = db.Column(db.String(20), nullable=True)  # promoter, passive, detractor
    
    # Metadata
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    
    # Context (what triggered the survey)
    context_type = db.Column(db.String(50), nullable=True)  # order, appointment, etc.
    context_id = db.Column(db.Integer, nullable=True)  # order_id, appointment_id, etc.
    
    user = db.relationship('User', backref=db.backref('survey_responses', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_survey_response_survey', 'survey_id'),
        Index('idx_survey_response_date', 'completed_at'),
        Index('idx_survey_response_score', 'score'),
    )
    
    def classify_nps(self):
        """Classify NPS response as promoter, passive, or detractor."""
        if self.score is None:
            return None
        if self.score >= 9:
            self.nps_category = 'promoter'
        elif self.score >= 7:
            self.nps_category = 'passive'
        else:
            self.nps_category = 'detractor'
        return self.nps_category
    
    def __repr__(self):
        return f'<SurveyResponse survey={self.survey_id} score={self.score}>'


class Review(db.Model):
    """Product reviews with moderation workflow."""
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    
    # What is being reviewed
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)  # For verified purchase
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for anonymous reviews
    
    # Review content
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    title = db.Column(db.String(200), nullable=True)
    body = db.Column(db.Text, nullable=True)
    
    # Moderation
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    moderated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    moderated_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Verified purchase flag
    verified_purchase = db.Column(db.Boolean, default=False)
    
    # Engagement
    helpful_count = db.Column(db.Integer, default=0)
    not_helpful_count = db.Column(db.Integer, default=0)
    
    # Owner/admin response
    response = db.Column(db.Text, nullable=True)
    response_at = db.Column(db.DateTime, nullable=True)
    response_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Media attachments
    images = db.Column(db.JSON, default=list)  # [{"url": "...", "caption": "..."}]
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref=db.backref('reviews', lazy='dynamic'))
    order = db.relationship('Order', backref=db.backref('reviews', lazy='dynamic'))
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('reviews_written', lazy='dynamic'))
    moderated_by = db.relationship('User', foreign_keys=[moderated_by_id])
    response_by = db.relationship('User', foreign_keys=[response_by_id])
    
    __table_args__ = (
        Index('idx_review_product', 'product_id'),
        Index('idx_review_status', 'status'),
        Index('idx_review_rating', 'rating'),
        Index('idx_review_user', 'user_id'),
        db.UniqueConstraint('product_id', 'user_id', name='uq_review_product_user'),  # One review per product per user
    )
    
    def approve(self, moderator_id):
        """Approve the review."""
        self.status = 'approved'
        self.moderated_by_id = moderator_id
        self.moderated_at = datetime.utcnow()
    
    def reject(self, moderator_id, reason=None):
        """Reject the review."""
        self.status = 'rejected'
        self.moderated_by_id = moderator_id
        self.moderated_at = datetime.utcnow()
        self.rejection_reason = reason
    
    def add_response(self, responder_id, response_text):
        """Add owner/admin response to review."""
        self.response = response_text
        self.response_by_id = responder_id
        self.response_at = datetime.utcnow()
    
    def mark_helpful(self, is_helpful=True):
        """Mark review as helpful or not helpful."""
        if is_helpful:
            self.helpful_count += 1
        else:
            self.not_helpful_count += 1
    
    def __repr__(self):
        return f'<Review product={self.product_id} rating={self.rating} status={self.status}>'


class ReviewVote(db.Model):
    """Track user votes on review helpfulness."""
    __tablename__ = 'review_vote'
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_helpful = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    review = db.relationship('Review', backref=db.backref('votes', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('review_votes', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('review_id', 'user_id', name='uq_review_vote_user'),
        Index('idx_review_vote_review', 'review_id'),
    )
    
    def __repr__(self):
        return f'<ReviewVote review={self.review_id} helpful={self.is_helpful}>'


# ============================================================================
# Phase 17: Calendar & Scheduling Powerhouse Models
# ============================================================================

class AppointmentType(db.Model):
    """Configurable appointment types with durations, buffers, and capacity limits."""
    __tablename__ = 'appointment_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Integer, default=60, nullable=False)
    buffer_before = db.Column(db.Integer, default=0)  # Minutes before appointment
    buffer_after = db.Column(db.Integer, default=15)  # Minutes after appointment
    price = db.Column(db.Numeric(10, 2), nullable=True)  # Optional pricing
    color = db.Column(db.String(7), default='#3B82F6')  # Hex color for calendar display
    is_active = db.Column(db.Boolean, default=True)
    max_per_day = db.Column(db.Integer, nullable=True)  # Limit per day per staff
    max_attendees = db.Column(db.Integer, default=1)  # For group appointments
    required_resource_type = db.Column(db.String(50), nullable=True)  # Auto-book resource type
    booking_window_days = db.Column(db.Integer, default=30)  # How far in advance bookings allowed
    min_notice_hours = db.Column(db.Integer, default=24)  # Minimum notice for booking
    confirmation_required = db.Column(db.Boolean, default=True)
    intake_form_id = db.Column(db.Integer, db.ForeignKey('form_definition.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    intake_form = db.relationship('FormDefinition', backref='appointment_types')
    
    __table_args__ = (
        Index('idx_appt_type_active', 'is_active'),
    )
    
    def get_total_duration(self):
        """Get total time blocked including buffers."""
        return self.buffer_before + self.duration_minutes + self.buffer_after
    
    def __repr__(self):
        return f'<AppointmentType {self.name} ({self.duration_minutes}min)>'


class Resource(db.Model):
    """Physical resources (rooms, equipment, vehicles) that can be booked."""
    __tablename__ = 'resource'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # room, equipment, vehicle
    description = db.Column(db.Text, nullable=True)
    capacity = db.Column(db.Integer, default=1)  # How many people/items
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    amenities = db.Column(db.JSON, default=list)  # List of amenities/features
    photo_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)  # Optional pricing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    location = db.relationship('Location', backref='resources')
    photo = db.relationship('Media', foreign_keys=[photo_id])
    
    __table_args__ = (
        Index('idx_resource_type', 'resource_type'),
        Index('idx_resource_active', 'is_active'),
    )
    
    def __repr__(self):
        return f'<Resource {self.name} ({self.resource_type})>'


class ResourceBooking(db.Model):
    """Links resources to time slots, optionally tied to appointments."""
    __tablename__ = 'resource_booking'
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    booked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, cancelled, pending
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    resource = db.relationship('Resource', backref=db.backref('bookings', lazy='dynamic'))
    appointment = db.relationship('Appointment', backref=db.backref('resource_bookings', lazy=True))
    booked_by = db.relationship('User', backref=db.backref('resource_bookings', lazy=True))
    
    __table_args__ = (
        Index('idx_res_booking_resource_time', 'resource_id', 'start_time', 'end_time'),
        Index('idx_res_booking_status', 'status'),
    )
    
    def conflicts_with(self, start, end):
        """Check if this booking conflicts with a time range."""
        return (self.start_time < end) and (self.end_time > start)
    
    def __repr__(self):
        return f'<ResourceBooking {self.resource_id} {self.start_time}-{self.end_time}>'


class Waitlist(db.Model):
    """Track customers waiting for appointment slots."""
    __tablename__ = 'waitlist'
    id = db.Column(db.Integer, primary_key=True)
    appointment_type_id = db.Column(db.Integer, db.ForeignKey('appointment_type.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    # Guest info (if no user account)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    # Preferences
    preferred_date = db.Column(db.Date, nullable=True)  # Specific date or null for any
    preferred_time_range = db.Column(db.String(20), default='any')  # morning, afternoon, evening, any
    preferred_staff_id = db.Column(db.Integer, db.ForeignKey('estimator.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    # Status tracking
    status = db.Column(db.String(20), default='waiting')  # waiting, offered, booked, expired, cancelled
    priority = db.Column(db.Integer, default=0)  # Higher = higher priority
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    offered_at = db.Column(db.DateTime, nullable=True)
    offer_expires_at = db.Column(db.DateTime, nullable=True)
    booked_appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)
    
    # Relationships
    appointment_type = db.relationship('AppointmentType', backref=db.backref('waitlist_entries', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('waitlist_entries', lazy=True))
    preferred_staff = db.relationship('Estimator', backref=db.backref('waitlist_preferences', lazy=True))
    booked_appointment = db.relationship('Appointment', backref=db.backref('waitlist_entry', uselist=False))
    
    __table_args__ = (
        Index('idx_waitlist_status', 'status'),
        Index('idx_waitlist_type_status', 'appointment_type_id', 'status'),
        Index('idx_waitlist_created', 'created_at'),
    )
    
    def is_offer_expired(self):
        """Check if the current offer has expired."""
        if self.offer_expires_at and self.status == 'offered':
            return datetime.utcnow() > self.offer_expires_at
        return False
    
    def make_offer(self, expires_hours=24):
        """Mark entry as offered with expiration."""
        self.status = 'offered'
        self.offered_at = datetime.utcnow()
        self.offer_expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    
    def __repr__(self):
        return f'<Waitlist {self.email} for type={self.appointment_type_id} status={self.status}>'


class BookingPolicy(db.Model):
    """Booking policies attached to appointment types."""
    __tablename__ = 'booking_policy'
    id = db.Column(db.Integer, primary_key=True)
    appointment_type_id = db.Column(db.Integer, db.ForeignKey('appointment_type.id'), nullable=False, unique=True)
    # Cancellation policy
    cancellation_allowed = db.Column(db.Boolean, default=True)
    cancellation_hours = db.Column(db.Integer, default=24)  # Hours before for free cancellation
    cancellation_fee = db.Column(db.Numeric(10, 2), default=0)  # Fee for late cancellation
    # No-show policy
    no_show_fee = db.Column(db.Numeric(10, 2), default=0)
    no_show_penalty_type = db.Column(db.String(20), default='none')  # none, fee, block
    # Deposit/prepayment
    deposit_required = db.Column(db.Boolean, default=False)
    deposit_amount = db.Column(db.Numeric(10, 2), nullable=True)
    deposit_percentage = db.Column(db.Integer, nullable=True)  # Alternative to fixed amount
    # Reschedule policy
    max_reschedules = db.Column(db.Integer, default=2)
    reschedule_hours = db.Column(db.Integer, default=24)  # Hours before for free reschedule
    # Reminders
    reminder_1_hours = db.Column(db.Integer, default=168)  # 1 week = 168 hours
    reminder_2_hours = db.Column(db.Integer, default=24)  # 1 day
    reminder_3_hours = db.Column(db.Integer, default=1)  # 1 hour
    send_confirmation = db.Column(db.Boolean, default=True)
    send_reminders = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointment_type = db.relationship('AppointmentType', backref=db.backref('policy', uselist=False))
    
    def can_cancel(self, appointment_datetime):
        """Check if cancellation is allowed based on time remaining."""
        if not self.cancellation_allowed:
            return False, "Cancellations not allowed for this appointment type"
        hours_until = (appointment_datetime - datetime.utcnow()).total_seconds() / 3600
        if hours_until < self.cancellation_hours:
            return False, f"Must cancel at least {self.cancellation_hours} hours in advance"
        return True, None
    
    def get_cancellation_fee(self, appointment_datetime):
        """Calculate cancellation fee based on timing."""
        hours_until = (appointment_datetime - datetime.utcnow()).total_seconds() / 3600
        if hours_until >= self.cancellation_hours:
            return 0
        return float(self.cancellation_fee or 0)
    
    def __repr__(self):
        return f'<BookingPolicy for type={self.appointment_type_id}>'


class AppointmentAttendee(db.Model):
    """Track multiple attendees for group appointments."""
    __tablename__ = 'appointment_attendee'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    # Guest info
    email = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    # Status
    status = db.Column(db.String(20), default='confirmed')  # confirmed, cancelled, no_show
    checked_in_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    appointment = db.relationship('Appointment', backref=db.backref('attendees', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('appointment_attendances', lazy=True))
    
    __table_args__ = (
        Index('idx_attendee_appointment', 'appointment_id'),
        Index('idx_attendee_status', 'status'),
    )
    
    def __repr__(self):
        return f'<AppointmentAttendee {self.email} for appt={self.appointment_id}>'


class CheckInToken(db.Model):
    """QR code tokens for appointment check-in."""
    __tablename__ = 'checkin_token'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False, unique=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    appointment = db.relationship('Appointment', backref=db.backref('checkin_token', uselist=False))
    
    def is_valid(self):
        """Check if token is still valid."""
        if self.used_at:
            return False
        return datetime.utcnow() < self.expires_at
    
    @staticmethod
    def generate_token():
        """Generate a unique check-in token."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def __repr__(self):
        return f'<CheckInToken for appt={self.appointment_id}>'


# ============================================================================
# Phase 25: Advanced Infrastructure Models
# ============================================================================

class Backup(db.Model):
    """Track backup history and status."""
    __tablename__ = 'backup'
    id = db.Column(db.Integer, primary_key=True)
    backup_type = db.Column(db.String(20), nullable=False)  # database, media, full
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, failed
    file_path = db.Column(db.String(500), nullable=True)
    file_size_bytes = db.Column(db.BigInteger, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('backup_schedule.id'), nullable=True)
    checksum = db.Column(db.String(64), nullable=True)  # SHA-256 for integrity
    encrypted = db.Column(db.Boolean, default=False)
    storage_location = db.Column(db.String(50), default='local')  # local, s3, azure
    
    # Relationships
    created_by = db.relationship('User', backref='created_backups')
    
    __table_args__ = (
        Index('idx_backup_type_status', 'backup_type', 'status'),
        Index('idx_backup_started', 'started_at'),
    )
    
    def __repr__(self):
        return f'<Backup {self.backup_type} status={self.status}>'


class BackupSchedule(db.Model):
    """Scheduled backup configuration."""
    __tablename__ = 'backup_schedule'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    backup_type = db.Column(db.String(20), nullable=False)  # database, media, full
    frequency = db.Column(db.String(20), nullable=False)  # hourly, daily, weekly, monthly
    retention_days = db.Column(db.Integer, default=30)
    storage_location = db.Column(db.String(50), default='local')  # local, s3, azure
    encryption_enabled = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    last_run_at = db.Column(db.DateTime, nullable=True)
    next_run_at = db.Column(db.DateTime, nullable=True)
    cron_expression = db.Column(db.String(100), nullable=True)  # Optional custom cron
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    backups = db.relationship('Backup', backref='schedule', lazy='dynamic')
    
    def __repr__(self):
        return f'<BackupSchedule {self.name} {self.frequency}>'


class FeatureFlag(db.Model):
    """Feature flags for gradual rollout."""
    __tablename__ = 'feature_flag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_enabled = db.Column(db.Boolean, default=False)
    rollout_percentage = db.Column(db.Integer, default=0)  # 0-100
    user_whitelist = db.Column(db.JSON, default=list)  # List of user IDs
    user_blacklist = db.Column(db.JSON, default=list)
    segment_ids = db.Column(db.JSON, default=list)  # Target specific segments
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    created_by = db.relationship('User', backref='created_feature_flags')
    
    __table_args__ = (
        Index('idx_feature_flag_name', 'name'),
    )
    
    def is_active_for_user(self, user_id):
        """Check if feature is active for a specific user."""
        if not self.is_enabled:
            return False
        if self.starts_at and datetime.utcnow() < self.starts_at:
            return False
        if self.ends_at and datetime.utcnow() > self.ends_at:
            return False
        if user_id in (self.user_blacklist or []):
            return False
        if user_id in (self.user_whitelist or []):
            return True
        if self.rollout_percentage >= 100:
            return True
        if self.rollout_percentage <= 0:
            return False
        # Deterministic rollout based on user ID
        return (hash(f"{self.name}-{user_id}") % 100) < self.rollout_percentage
    
    def __repr__(self):
        return f'<FeatureFlag {self.name} enabled={self.is_enabled}>'


class DeploymentLog(db.Model):
    """Track deployment history."""
    __tablename__ = 'deployment_log'
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), nullable=False)
    environment = db.Column(db.String(20), nullable=False)  # staging, production
    deployed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, success, failed, rolled_back
    notes = db.Column(db.Text, nullable=True)
    rollback_version = db.Column(db.String(50), nullable=True)  # Previous version for rollback
    commit_sha = db.Column(db.String(40), nullable=True)
    migration_ran = db.Column(db.Boolean, default=False)
    
    deployed_by = db.relationship('User', backref='deployments')
    
    __table_args__ = (
        Index('idx_deployment_env_status', 'environment', 'status'),
        Index('idx_deployment_started', 'started_at'),
    )
    
    def __repr__(self):
        return f'<DeploymentLog {self.version} to {self.environment}>'


# ============================================================================
# Phase 26: System-Wide Feature Polish Models
# ============================================================================

class PostView(db.Model):
    """Track post views with deduplication."""
    __tablename__ = 'post_view'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    session_id = db.Column(db.String(64), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_hash = db.Column(db.String(64), nullable=True)  # Hashed for privacy
    user_agent = db.Column(db.String(255), nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    post = db.relationship('Post', backref=db.backref('views', lazy='dynamic'))
    user = db.relationship('User', backref='post_views')
    
    __table_args__ = (
        Index('idx_postview_post_viewed', 'post_id', 'viewed_at'),
        Index('idx_postview_session', 'session_id'),
    )
    
    def __repr__(self):
        return f'<PostView post={self.post_id}>'


class WebhookDelivery(db.Model):
    """Webhook delivery attempts with audit trail."""
    __tablename__ = 'webhook_delivery'
    id = db.Column(db.Integer, primary_key=True)
    webhook_id = db.Column(db.Integer, db.ForeignKey('webhook.id'), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    payload_hash = db.Column(db.String(64), nullable=True)
    idempotency_key = db.Column(db.String(64), unique=True, nullable=False)
    attempt_count = db.Column(db.Integer, default=1)
    max_attempts = db.Column(db.Integer, default=5)
    status_code = db.Column(db.Integer, nullable=True)
    response_body = db.Column(db.Text, nullable=True)
    request_body = db.Column(db.Text, nullable=True)
    signature = db.Column(db.String(128), nullable=True)  # HMAC signature
    delivered_at = db.Column(db.DateTime, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)
    next_retry_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration_ms = db.Column(db.Integer, nullable=True)
    
    webhook = db.relationship('Webhook', backref=db.backref('deliveries', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_webhook_delivery_status', 'webhook_id', 'status_code'),
        Index('idx_webhook_delivery_retry', 'next_retry_at'),
        Index('idx_webhook_delivery_idempotency', 'idempotency_key'),
    )
    
    def __repr__(self):
        return f'<WebhookDelivery {self.event_type} attempts={self.attempt_count}>'


# ============================================================================
# Phase 28: Unified Security & OWASP Compliance Models
# ============================================================================

class LoginAttempt(db.Model):
    """Track login attempts for security."""
    __tablename__ = 'login_attempt'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(255), nullable=True)
    success = db.Column(db.Boolean, default=False)
    failure_reason = db.Column(db.String(100), nullable=True)  # wrong_password, account_locked, mfa_failed
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(100), nullable=True)  # GeoIP location
    device_fingerprint = db.Column(db.String(64), nullable=True)
    
    user = db.relationship('User', backref='login_attempts')
    
    __table_args__ = (
        Index('idx_login_attempt_email_ip', 'email', 'ip_address'),
        Index('idx_login_attempt_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<LoginAttempt {self.email} success={self.success}>'


class IPBlacklist(db.Model):
    """Blocked IP addresses."""
    __tablename__ = 'ip_blacklist'
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False, index=True)
    reason = db.Column(db.String(255), nullable=True)
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Null = permanent
    blocked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    auto_blocked = db.Column(db.Boolean, default=False)  # True if automatic
    failed_attempts = db.Column(db.Integer, default=0)
    
    blocked_by = db.relationship('User', backref='blocked_ips')
    
    def is_active(self):
        """Check if block is still active."""
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at
    
    def __repr__(self):
        return f'<IPBlacklist {self.ip_address}>'


class UserMFA(db.Model):
    """MFA configuration per user."""
    __tablename__ = 'user_mfa'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mfa_type = db.Column(db.String(20), nullable=False)  # totp, sms, email
    secret_encrypted = db.Column(db.Text, nullable=True)  # Encrypted TOTP secret
    backup_codes_encrypted = db.Column(db.Text, nullable=True)  # Encrypted JSON list
    is_enabled = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('mfa_settings', lazy=True))
    
    __table_args__ = (
        Index('idx_user_mfa_user_type', 'user_id', 'mfa_type'),
    )
    
    def __repr__(self):
        return f'<UserMFA user={self.user_id} type={self.mfa_type}>'


class MFAChallenge(db.Model):
    """Pending MFA verification."""
    __tablename__ = 'mfa_challenge'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_type = db.Column(db.String(20), nullable=False)  # totp, sms, email, backup
    token_hash = db.Column(db.String(128), nullable=True)  # For SMS/email codes
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=3)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    
    user = db.relationship('User', backref='mfa_challenges')
    
    __table_args__ = (
        Index('idx_mfa_challenge_user', 'user_id', 'created_at'),
    )
    
    def is_valid(self):
        """Check if challenge is still valid."""
        if self.verified_at:
            return False
        if self.attempts >= self.max_attempts:
            return False
        return datetime.utcnow() < self.expires_at
    
    def __repr__(self):
        return f'<MFAChallenge user={self.user_id} type={self.challenge_type}>'


class PasswordHistory(db.Model):
    """Previous password hashes for reuse prevention."""
    __tablename__ = 'password_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='password_history')
    
    __table_args__ = (
        Index('idx_password_history_user', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<PasswordHistory user={self.user_id}>'


# ============================================================================
# Phase 29: Compliance & Legal Tools Models
# ============================================================================

class ConsentRecord(db.Model):
    """Track all consent grants/withdrawals for GDPR/CCPA compliance."""
    __tablename__ = 'consent_record'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    session_id = db.Column(db.String(64), nullable=True)
    consent_type = db.Column(db.String(50), nullable=False)  # analytics, marketing, necessary, functional
    granted = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    consent_source = db.Column(db.String(50), default='cookie_banner')  # cookie_banner, settings, registration
    policy_version = db.Column(db.String(20), nullable=True)  # Version of privacy policy
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='consent_records')
    
    __table_args__ = (
        Index('idx_consent_user_type', 'user_id', 'consent_type'),
        Index('idx_consent_session', 'session_id'),
    )
    
    def __repr__(self):
        return f'<ConsentRecord {self.consent_type} granted={self.granted}>'


class DataExportRequest(db.Model):
    """GDPR data export requests."""
    __tablename__ = 'data_export_request'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, ready, downloaded, expired
    file_path = db.Column(db.String(500), nullable=True)
    file_format = db.Column(db.String(10), default='json')  # json, csv
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processing_started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    downloaded_at = db.Column(db.DateTime, nullable=True)
    download_count = db.Column(db.Integer, default=0)
    file_size_bytes = db.Column(db.BigInteger, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    user = db.relationship('User', backref='data_export_requests')
    
    __table_args__ = (
        Index('idx_export_user_status', 'user_id', 'status'),
    )
    
    def __repr__(self):
        return f'<DataExportRequest user={self.user_id} status={self.status}>'


class RetentionPolicy(db.Model):
    """Data retention policies by type."""
    __tablename__ = 'retention_policy'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    data_type = db.Column(db.String(50), nullable=False)  # audit_logs, session_data, analytics, etc.
    table_name = db.Column(db.String(100), nullable=True)  # Target database table
    retention_days = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), default='delete')  # delete, anonymize, archive
    is_active = db.Column(db.Boolean, default=True)
    last_executed_at = db.Column(db.DateTime, nullable=True)
    execution_interval_hours = db.Column(db.Integer, default=24)  # How often to run
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    created_by = db.relationship('User', backref='created_retention_policies')
    
    def __repr__(self):
        return f'<RetentionPolicy {self.name} {self.retention_days} days>'


class DataRetentionLog(db.Model):
    """Log of retention policy executions."""
    __tablename__ = 'data_retention_log'
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('retention_policy.id'), nullable=False)
    records_processed = db.Column(db.Integer, default=0)
    records_deleted = db.Column(db.Integer, default=0)
    records_anonymized = db.Column(db.Integer, default=0)
    records_archived = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='success')  # success, partial, failed
    error_message = db.Column(db.Text, nullable=True)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration_seconds = db.Column(db.Float, nullable=True)
    
    policy = db.relationship('RetentionPolicy', backref=db.backref('execution_logs', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_retention_log_policy', 'policy_id', 'executed_at'),
    )
    
    def __repr__(self):
        return f'<DataRetentionLog policy={self.policy_id} deleted={self.records_deleted}>'

# ============================================================================
# Phase 23: Support Ticketing System
# ============================================================================

class SupportTicket(db.Model):
    """Customer support tickets for issue tracking and resolution."""
    __tablename__ = 'support_ticket'
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)  # Auto-generated TKT-XXXXXX
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, waiting, resolved, closed
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    category = db.Column(db.String(50), nullable=True)  # billing, technical, general, feature_request
    
    # Customer info (either logged-in user or guest)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email = db.Column(db.String(120), nullable=True)  # For non-logged-in users
    name = db.Column(db.String(100), nullable=True)  # Guest name
    
    # Staff assignment
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    first_response_at = db.Column(db.DateTime, nullable=True)  # SLA tracking
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    # Satisfaction
    satisfaction_rating = db.Column(db.Integer, nullable=True)  # 1-5
    satisfaction_comment = db.Column(db.Text, nullable=True)
    
    # Related entities
    related_order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    related_appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('support_tickets', lazy='dynamic'))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref=db.backref('assigned_tickets', lazy='dynamic'))
    
    __table_args__ = (
        Index('idx_ticket_status', 'status'),
        Index('idx_ticket_priority', 'priority'),
        Index('idx_ticket_user', 'user_id'),
        Index('idx_ticket_assigned', 'assigned_to_id'),
        Index('idx_ticket_created', 'created_at'),
    )

    @staticmethod
    def generate_ticket_number():
        """Generate unique ticket number like TKT-000001."""
        import random
        import string
        while True:
            number = ''.join(random.choices(string.digits, k=6))
            ticket_num = f'TKT-{number}'
            existing = SupportTicket.query.filter_by(ticket_number=ticket_num).first()
            if not existing:
                return ticket_num
    
    def get_customer_display_name(self):
        """Return display name for the ticket creator."""
        if self.user:
            return f"{self.user.first_name or ''} {self.user.last_name or ''}".strip() or self.user.username
        return self.name or self.email or 'Anonymous'
    
    def get_customer_email(self):
        """Return customer email for notifications."""
        if self.user:
            return self.user.email
        return self.email

    def __repr__(self):
        return f'<SupportTicket {self.ticket_number} - {self.status}>'


class TicketReply(db.Model):
    """Replies/messages within a support ticket."""
    __tablename__ = 'ticket_reply'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Null for customer guest replies
    
    content = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)  # Staff-only internal notes
    is_from_customer = db.Column(db.Boolean, default=True)  # True if customer, False if staff
    
    # Attachments (link to Media)
    attachment_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket = db.relationship('SupportTicket', backref=db.backref('replies', lazy='dynamic', order_by='TicketReply.created_at'))
    user = db.relationship('User', backref=db.backref('ticket_replies', lazy=True))
    attachment = db.relationship('Media')
    
    __table_args__ = (
        Index('idx_reply_ticket', 'ticket_id', 'created_at'),
    )

    def __repr__(self):
        return f'<TicketReply {self.id} on ticket {self.ticket_id}>'
