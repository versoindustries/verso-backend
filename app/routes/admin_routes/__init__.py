"""
Admin Routes Package

Admin dashboard routes requiring authentication and elevated permissions.
All routes should use @login_required and @role_required decorators.
"""

# Re-export admin route blueprints from main routes folder
# This allows future migration to move files here while maintaining compatibility

# Admin blueprints (imported when needed):
# - admin.admin
# - analytics.analytics_bp
# - automation.automation_bp
# - availability.availability_bp
# - backup.backup_bp
# - booking_admin.booking_admin_bp
# - calendar.calendar_bp
# - category_admin.category_admin_bp
# - crm.crm_bp
# - ecommerce_admin.ecommerce_admin_bp
# - email_admin.email_admin_bp
# - email_tracking.email_tracking_bp
# - forms_admin.forms_admin_bp
# - media_admin.media_admin_bp
# - messaging.messaging_bp
# - notifications.notifications_bp
# - observability.observability_bp
# - orders_admin.orders_admin_bp
# - push.push_bp
# - reports.reports_bp
# - reports_admin.reports_admin_bp
# - scheduling.scheduling_bp
# - setup.setup_bp
# - shop_admin.shop_admin_bp
# - sms_admin.sms_admin_bp
# - subscriptions.subscriptions_bp
# - support.support_bp (admin parts)
# - tasks_admin.tasks_admin_bp
# - theme.theme_bp
