from app import create_app, db
from app.models import User, Role, ApiKey
import secrets

app = create_app()

with app.app_context():
    print("Creating tables...")
    db.create_all()
    
    print("Creating admin role...")
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin')
        db.session.add(admin_role)
    
    db.session.commit() # Commit to get ID
    
    print("Creating admin user...")
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', password='password')
        admin.roles.append(admin_role)
        db.session.add(admin)
        db.session.commit()
    
    print("Creating API key...")
    # Clean up old keys if re-running (optional)
    
    key_val = "sk_live_1234567890abcdef"
    # Check by hash requires hashing, simpler to check by name
    key = ApiKey.query.filter_by(name='Dev Key').first()
    if not key:
        key = ApiKey(name='Dev Key', scopes=['read:leads', 'write:leads', 'read:orders', 'write:orders', 'read:products', 'write:products', 'admin:webhooks'])
        key.set_key(key_val)
        key.user_id = admin.id
        db.session.add(key)
        db.session.commit()
    
    print(f"Seeding complete. API Key: {key_val}")
