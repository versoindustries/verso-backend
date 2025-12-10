"""
Models Package

This package provides a modular organization for database models.
All models are re-exported from the original models.py to maintain
backward compatibility with existing imports.

Usage:
    from app.models import User, Product, Order
    
The models are organized into domain modules for future migration:
    - user.py: User, Role
    - scheduling.py: Appointment, Availability, Service
    - ecommerce.py: Product, Order, Cart, Discount
    - crm.py: Pipeline, Contact
    - blog.py: Post, Comment, Tag
    - messaging.py: Channel, Message, Notification
    - analytics.py: PageView, VisitorSession, ReportExport
    - forms.py: FormDefinition, FormSubmission
    - infrastructure.py: Task, Media, Workflow
"""

# For backward compatibility, re-export everything from the original models.py
# This allows gradual migration while keeping existing imports working
# pylint: disable=wildcard-import,unused-wildcard-import
from app.models_legacy import *
from app.models_legacy import user_roles, post_tags, post_authors, channel_members

# Also re-export the db instance for convenience
from app.database import db
