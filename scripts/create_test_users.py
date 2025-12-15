#!/usr/bin/env python3
"""
Create test users for DM and messaging testing.
Usage: flask shell < scripts/create_test_users.py
Or run directly: python scripts/create_test_users.py
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db
from app.models import User, Role

def create_test_users():
    """Create test users with various roles for messaging testing."""
    app = create_app()
    
    with app.app_context():
        # Get roles
        admin_role = Role.query.filter_by(name='admin').first()
        manager_role = Role.query.filter_by(name='manager').first()
        employee_role = Role.query.filter_by(name='employee').first()
        user_role = Role.query.filter_by(name='user').first()
        
        test_users = [
            {
                'username': 'test_alice',
                'email': 'alice@test.com',
                'password': 'TestPass123!',
                'roles': [employee_role] if employee_role else []
            },
            {
                'username': 'test_bob',
                'email': 'bob@test.com',
                'password': 'TestPass123!',
                'roles': [manager_role] if manager_role else []
            },
            {
                'username': 'test_charlie',
                'email': 'charlie@test.com',
                'password': 'TestPass123!',
                'roles': [user_role] if user_role else []
            }
        ]
        
        created = []
        for user_data in test_users:
            existing = User.query.filter(
                (User.username == user_data['username']) | 
                (User.email == user_data['email'])
            ).first()
            
            if existing:
                print(f"User {user_data['username']} already exists, skipping...")
                continue
            
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password']
            )
            user.confirmed = True
            user.tos_accepted = True
            
            for role in user_data['roles']:
                if role:
                    user.roles.append(role)
            
            db.session.add(user)
            created.append(user_data['username'])
        
        db.session.commit()
        
        if created:
            print(f"\n✓ Created {len(created)} test users: {', '.join(created)}")
            print("\nTest user credentials:")
            for user_data in test_users:
                if user_data['username'] in created:
                    print(f"  - {user_data['username']}: {user_data['email']} / {user_data['password']}")
        else:
            print("\nNo new users created (all already exist).")
        
        print("\nExisting test users in system:")
        for u in User.query.filter(User.username.like('test_%')).all():
            roles = [r.name for r in u.roles]
            print(f"  - {u.username} ({u.email}) - roles: {roles}")

if __name__ == '__main__':
    create_test_users()
