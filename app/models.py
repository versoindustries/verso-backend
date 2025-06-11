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
    first_name = db.Column(db.String(100), nullable=True)  # New field for first name
    last_name = db.Column(db.String(100), nullable=True)  # New field for last name

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

class Appointment(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    preferred_date_time = db.Column(db.DateTime, nullable=False)  # Ensure this is stored as UTC
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    estimator_id = db.Column(db.Integer, db.ForeignKey('estimator.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # UTC by default for created_at
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)  # UTC by default for updated_at

    # Relationships
    estimator = db.relationship('Estimator', backref=db.backref('appointments', lazy=True))
    service = db.relationship('Service', backref=db.backref('appointments', lazy=True))

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

class ContactFormSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    category = db.Column(db.String(100), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    image = db.Column(db.LargeBinary, nullable=True)  # Store image as BLOB
    image_mime_type = db.Column(db.String(50), nullable=True)  # Store MIME type (e.g., image/png)

    # Relationships
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

    __table_args__ = (
        Index('idx_post_slug', 'slug'),  # Index for faster slug lookups
    )

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