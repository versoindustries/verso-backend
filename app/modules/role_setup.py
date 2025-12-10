# ideal-sniffle/app/modules/role_setup.py

from app.models import Role
from app.database import db

def create_roles():
    """Create default roles with proper capitalization.
    
    Role Hierarchy:
    - Owner: Controls all locations, full system access
    - Admin: Full admin access to assigned location(s)
    - Manager: Manage staff, view reports
    - Employee: Staff member with limited access
    - Marketing: Content creation, campaigns
    - User: Regular authenticated user
    - Blogger: Blog content contributor
    - Commercial: Commercial/B2B access
    """
    # Canonical roles with proper capitalization
    roles = [
        'Owner',      # Multi-location owner, highest access
        'Admin',      # Location admin
        'Manager',    # Staff manager
        'Employee',   # Staff member
        'Marketing',  # Marketing/content team
        'User',       # Regular user
        'Blogger',    # Blog contributor
        'Commercial', # B2B/commercial user
    ]
    for name in roles:
        if not Role.query.filter_by(name=name).first():
            new_role = Role(name=name)
            db.session.add(new_role)
    db.session.commit()

