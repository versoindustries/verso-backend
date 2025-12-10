# app/modules/auth_manager.py
"""Authentication and role-based access control utilities for the Flask application.

This module provides functions and decorators for managing user authentication
and restricting access to routes based on user roles, integrating with Flask-Login
and the User model. It includes decorators for admin and blogger roles, ensuring
secure access control aligned with OWASP guidelines.
"""

from flask import flash, redirect, url_for
from flask_login import UserMixin, LoginManager, current_user
from functools import wraps
from app.database import db
from app.models import User
from app import login_manager, current_app

@login_manager.user_loader
def load_user(user_id):
    """Load a user from the database by ID for Flask-Login.

    Args:
        user_id (str): The ID of the user to load.

    Returns:
        User: The User object, or None if not found.
    """
    return User.query.get(int(user_id))

def admin_required(f):
    """Decorator to restrict access to routes for admin users only.

    Redirects unauthenticated or non-admin users to the login page with a warning.

    Args:
        f (function): The view function to decorate.

    Returns:
        function: The decorated function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('admin'):
            current_app.logger.warning(
                f"Unauthorized access attempt to admin route by user: {current_user.username if current_user.is_authenticated else 'anonymous'}"
            )
            flash('You do not have permission to view this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def blogger_required(f):
    """Decorator to restrict access to routes for blogger users only.

    Redirects unauthenticated or non-blogger users to the login page with a warning.

    Args:
        f (function): The view function to decorate.

    Returns:
        function: The decorated function.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('blogger'):
            current_app.logger.warning(
                f"Unauthorized access attempt to blogger route by user: {current_user.username if current_user.is_authenticated else 'anonymous'}"
            )
            flash('You do not have permission to view this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*required_roles):
    """Decorator to restrict access to routes for users with any of the specified roles.
    
    Usage:
        @role_required('admin', 'manager')
        def some_route():
            ...

    Args:
        *required_roles: Variable number of role names (strings).

    Returns:
        function: The decorated function.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if not any(current_user.has_role(role) for role in required_roles):
                current_app.logger.warning(
                    f"Unauthorized access attempt by user {current_user.username}: "
                    f"required roles {required_roles}, has roles {[r.name for r in current_user.roles]}"
                )
                flash('You do not have permission to view this page.', 'warning')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator