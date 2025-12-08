from app import create_app, db
from app.models import User, Role

app = create_app()
with app.app_context():
    email = "mike@versoindustries.com"
    user = User.query.filter_by(email=email).first()
    admin_role = Role.query.filter_by(name='admin').first()
    
    if not admin_role:
        print("Creating admin role")
        admin_role = Role(name='admin')
        db.session.add(admin_role)
        db.session.commit()
    
    if not user:
        print(f"Creating user {email}")
        # Need to provide a valid username
        user = User(username="mike", email=email, password="password123") 
        user.set_password("password123")
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        print("User created.")
    
    if not user.has_role('admin'):
        print(f"Assigning admin role to {email}")
        user.add_role(admin_role) # Using the add_role method from the model
        db.session.commit()
        print("Admin role assigned.")
    else:
        print(f"User {email} is already an admin.")
