from flask import flash, redirect, url_for
from flask_login import UserMixin, LoginManager, current_user
from functools import wraps
from app.database import db
from app.models import User
from app import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('admin'):
            flash('You do not have permission to view this page.', 'warning')
            return redirect(url_for('auth.login'))  # Replace 'auth.login' with the appropriate route for login
        return f(*args, **kwargs)
    return decorated_function
