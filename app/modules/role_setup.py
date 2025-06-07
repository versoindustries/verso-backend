# ideal-sniffle/app/modules/role_setup.py

from app.models import Role
from app.database import db

def create_roles():
    """Create default roles."""
    roles = ['admin', 'user', 'commercial']  # Add other roles as needed
    for name in roles:
        if not Role.query.filter_by(name=name).first():
            new_role = Role(name=name)
            db.session.add(new_role)
    db.session.commit()

