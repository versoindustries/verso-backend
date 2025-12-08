from app.models import AuditLog
from app.database import db
from flask import request
import logging

def log_audit_event(user_id, action, target_type=None, target_id=None, details=None, ip_address=None):
    """
    Logs an audit event to the database.
    
    :param user_id: ID of the user performing the action.
    :param action: String describing the action (e.g., 'create_user').
    :param target_type: String describing the target model/entity (e.g., 'User').
    :param target_id: ID of the target entity.
    :param details: Dictionary containing additional details (e.g., form data).
    :param ip_address: IP address of the user. If None, tries to get from request.
    """
    try:
        if ip_address is None and request:
            ip_address = request.remote_addr

        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        # Fallback to application log if DB logging fails
        logging.error(f"Failed to create audit log: {e}")
        db.session.rollback()
