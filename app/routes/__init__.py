"""
Routes Package - FULLY ORGANIZED

All Flask blueprints are now organized into logical subdirectories.
Blueprints are registered in app/__init__.py.

Directory Structure:
    routes/
    ├── __init__.py          # This file
    ├── public_routes/       # 12 files - Customer-facing routes
    ├── api_routes/          # 4 files - REST API endpoints
    ├── admin_routes/        # 30 files - Admin dashboard routes
    └── employee_routes/     # 3 files - Employee portal routes

Subdirectory Contents
=====================

PUBLIC_ROUTES (12 files - no auth required):
    - main_routes.py    : Homepage, about, contact, services
    - auth.py          : Login, register, password reset
    - blog.py          : Public blog posts, categories, search
    - cart.py          : Shopping cart operations
    - shop.py          : Product catalog, product detail
    - ecommerce.py     : Checkout, order confirmation
    - newsletter.py    : Newsletter subscription
    - pages.py         : CMS pages
    - privacy.py       : GDPR/privacy controls
    - forms.py         : Public form submissions
    - oauth.py         : OAuth integrations
    - media.py         : Media serving

API_ROUTES (4 files - REST endpoints, JSON responses):
    - api.py           : Core API endpoints
    - api_docs.py      : API documentation
    - booking_api.py   : Booking API
    - webhooks.py      : External webhook handlers

ADMIN_ROUTES (30 files - requires admin/manager role):
    - admin.py         : Core admin dashboard
    - ai.py            : AI/ML features
    - analytics.py     : Analytics dashboards
    - automation.py    : Workflow automation
    - availability.py  : Staff availability management
    - backup.py        : System backups
    - booking_admin.py : Booking administration
    - calendar.py      : Calendar management
    - category_admin.py: Category management
    - crm.py           : CRM/Lead management
    - ecommerce_admin.py: E-commerce administration
    - email_admin.py   : Email template/campaign management
    - email_tracking.py: Email analytics
    - forms_admin.py   : Form builder administration
    - media_admin.py   : Media library management
    - messaging.py     : Internal messaging
    - notifications.py : Notification management
    - observability.py : System observability
    - orders_admin.py  : Order management
    - push.py          : Push notification management
    - reports.py       : Report generation
    - reports_admin.py : Saved reports management
    - scheduling.py    : Staff scheduling
    - setup.py         : Initial setup
    - shop_admin.py    : Shop settings
    - sms_admin.py     : SMS template management
    - subscriptions.py : Subscription management
    - support.py       : Ticket administration
    - tasks_admin.py   : Task management
    - theme.py         : Theme editor

EMPLOYEE_ROUTES (3 files - requires login):
    - employee.py      : Employee portal
    - onboarding.py    : User onboarding
    - user.py          : User profile/settings
"""
