"""
Base module for models package.

Contains shared imports, utilities, and the database instance.
All model files should import from this module.
"""
from datetime import datetime, timedelta
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
import flask
from flask import current_app
import enum
from app.extensions import bcrypt
import sqlalchemy
from app.database import db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_utils import ChoiceType
import json
from sqlalchemy import JSON, event, Index
from sqlalchemy.sql import func
from sqlalchemy.ext.mutable import MutableList
import pytz

# Re-export db for convenience
__all__ = [
    'db', 'datetime', 'timedelta', 'UserMixin', 'URLSafeTimedSerializer',
    'flask', 'current_app', 'enum', 'bcrypt', 'sqlalchemy', 'SQLAlchemyError',
    'ChoiceType', 'json', 'JSON', 'event', 'Index', 'func', 'MutableList', 'pytz'
]
