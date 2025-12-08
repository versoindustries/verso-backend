"""
Phase 30: Pytest Fixtures and Configuration

Common test fixtures and utilities for comprehensive testing.
"""

import os
import tempfile
import pytest
from datetime import datetime, timedelta

# Set testing environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    from app import create_app
    from app.database import db
    
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key-for-testing-only',
        'BCRYPT_LOG_ROUNDS': 4,  # Faster hashing for tests
        'SERVER_NAME': 'localhost',
    })
    
    with app.app_context():
        db.create_all()
        
        # Seed required data
        _seed_test_data(db)
        
        yield app
        
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """Create test client for each test."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create CLI runner for testing CLI commands."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a database session for each test."""
    from app.database import db
    
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Bind session to this connection
        session = db.session
        
        yield session
        
        session.rollback()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def admin_user(app, db_session):
    """Create an admin user for testing."""
    from app.models import User, Role
    from app.database import db
    
    with app.app_context():
        # Get or create admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
        
        # Create admin user
        user = User(
            username='test_admin',
            email='admin@test.com',
            password='TestPassword123!'
        )
        user.confirmed = True
        user.roles.append(admin_role)
        
        db.session.add(user)
        db.session.commit()
        
        yield user
        
        # Cleanup
        db.session.delete(user)
        db.session.commit()


@pytest.fixture(scope='function')
def regular_user(app, db_session):
    """Create a regular user for testing."""
    from app.models import User, Role
    from app.database import db
    
    with app.app_context():
        # Get or create user role
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user')
            db.session.add(user_role)
        
        user = User(
            username='test_user',
            email='user@test.com',
            password='TestPassword123!'
        )
        user.confirmed = True
        user.roles.append(user_role)
        
        db.session.add(user)
        db.session.commit()
        
        yield user
        
        db.session.delete(user)
        db.session.commit()


@pytest.fixture(scope='function')
def authenticated_client(client, regular_user, app):
    """Create an authenticated test client."""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = regular_user.id
            sess['_fresh'] = True
        yield client


@pytest.fixture(scope='function')
def admin_client(client, admin_user, app):
    """Create an admin-authenticated test client."""
    with app.app_context():
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        yield client


@pytest.fixture(scope='function')
def api_key(app, admin_user, db_session):
    """Create an API key for testing."""
    from app.models import ApiKey
    from app.database import db
    import secrets
    
    with app.app_context():
        key = ApiKey(
            name='Test API Key',
            key_hash=secrets.token_urlsafe(32),
            user_id=admin_user.id,
            scopes=['read', 'write'],
            is_active=True,
        )
        db.session.add(key)
        db.session.commit()
        
        yield key
        
        db.session.delete(key)
        db.session.commit()


@pytest.fixture(scope='function')
def sample_product(app, db_session):
    """Create a sample product for testing."""
    from app.models import Product, Category
    from app.database import db
    
    with app.app_context():
        category = Category(name='Test Category', slug='test-category')
        db.session.add(category)
        
        product = Product(
            name='Test Product',
            slug='test-product',
            description='A test product',
            price=1999,  # $19.99
            inventory=100,
            is_active=True,
            category=category,
        )
        db.session.add(product)
        db.session.commit()
        
        yield product
        
        db.session.delete(product)
        db.session.delete(category)
        db.session.commit()


@pytest.fixture(scope='function')
def sample_post(app, admin_user, db_session):
    """Create a sample blog post for testing."""
    from app.models import Post
    from app.database import db
    
    with app.app_context():
        post = Post(
            title='Test Post',
            slug='test-post',
            content='<p>This is test content.</p>',
            author_id=admin_user.id,
            is_published=True,
        )
        db.session.add(post)
        db.session.commit()
        
        yield post
        
        db.session.delete(post)
        db.session.commit()


@pytest.fixture(scope='function')
def sample_lead(app, db_session):
    """Create a sample lead/contact submission for testing."""
    from app.models import ContactFormSubmission
    from app.database import db
    
    with app.app_context():
        lead = ContactFormSubmission(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='555-1234',
            message='Test inquiry message',
        )
        db.session.add(lead)
        db.session.commit()
        
        yield lead
        
        db.session.delete(lead)
        db.session.commit()


def _seed_test_data(db):
    """Seed required data for tests."""
    from app.models import Role, BusinessConfig
    
    # Create default roles
    roles = ['admin', 'user', 'staff', 'customer']
    for role_name in roles:
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(name=role_name))
    
    # Create required BusinessConfig entries
    configs = [
        ('site_name', 'Test Site'),
        ('site_email', 'test@example.com'),
        ('timezone', 'UTC'),
    ]
    for name, value in configs:
        if not BusinessConfig.query.filter_by(setting_name=name).first():
            db.session.add(BusinessConfig(setting_name=name, setting_value=value))
    
    db.session.commit()


# ============================================================================
# Helper Functions
# ============================================================================

def login_user(client, email, password):
    """Helper to login a user."""
    return client.post('/auth/login', data={
        'email': email,
        'password': password,
    }, follow_redirects=True)


def logout_user(client):
    """Helper to logout a user."""
    return client.get('/auth/logout', follow_redirects=True)


def get_csrf_token(client, url='/auth/login'):
    """Extract CSRF token from a page."""
    import re
    response = client.get(url)
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.data.decode())
    return match.group(1) if match else None


def create_test_user(db, username, email, password, roles=None):
    """Helper to create a test user."""
    from app.models import User, Role
    
    user = User(username=username, email=email, password=password)
    user.confirmed = True
    
    if roles:
        for role_name in roles:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                user.roles.append(role)
    
    db.session.add(user)
    db.session.commit()
    return user


def assert_flashes(client, expected_message, expected_category='success'):
    """Assert that a specific flash message was set."""
    with client.session_transaction() as sess:
        flashes = dict(sess.get('_flashes', []))
        assert expected_category in flashes
        assert expected_message in flashes[expected_category]
