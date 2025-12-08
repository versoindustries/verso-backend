# Testing Guide

This guide covers the testing infrastructure, conventions, and best practices for Verso-Backend.

## Overview

Verso-Backend uses **pytest** as the testing framework with the following test categories:

| Category | Description | Location |
|----------|-------------|----------|
| Unit Tests | Test individual functions/methods | `app/tests/test_*.py` |
| Integration Tests | Test component interactions | `tests/integration/` |
| API Tests | Test REST API endpoints | `tests/test_api.py` |
| E2E Tests | Full user flow tests | `tests/e2e/` |

## Quick Start

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-flask

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth.py

# Run tests matching a pattern
pytest -k "test_login"

# Run with verbose output
pytest -v
```

## Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = app/tests tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
filterwarnings =
    ignore::DeprecationWarning
```

### conftest.py

The main test fixtures are defined in `app/tests/conftest.py`:

```python
import pytest
from app import create_app
from app.database import db as _db
from app.models import User, Role

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    return app

@pytest.fixture(scope='session')
def db(app):
    """Create database for testing."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    session = db.session
    yield session
    
    session.rollback()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def auth_client(client, test_user):
    """Create authenticated test client."""
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'password123'
    })
    return client

@pytest.fixture
def test_user(session):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        password='password123'
    )
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def admin_user(session):
    """Create an admin user."""
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin')
        session.add(admin_role)
    
    user = User(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )
    user.roles.append(admin_role)
    session.add(user)
    session.commit()
    return user
```

## Writing Tests

### Model Tests

Test model validations, relationships, and methods:

```python
import pytest
from app.models import Product, Category

class TestProductModel:
    """Tests for Product model."""
    
    def test_create_product(self, session):
        """Test creating a product."""
        product = Product(
            name='Test Product',
            price=1999,
            sku='TEST-001'
        )
        session.add(product)
        session.commit()
        
        assert product.id is not None
        assert product.slug == 'test-product'
    
    def test_product_slug_generation(self, session):
        """Test automatic slug generation."""
        product = Product(name='My Awesome Product', price=999)
        session.add(product)
        session.commit()
        
        assert product.slug == 'my-awesome-product'
    
    def test_product_category_relationship(self, session):
        """Test product-category relationship."""
        category = Category(name='Electronics')
        product = Product(
            name='Laptop',
            price=99999,
            category=category
        )
        session.add(product)
        session.commit()
        
        assert product.category.name == 'Electronics'
        assert product in category.products
    
    def test_product_price_in_dollars(self, session):
        """Test price conversion property."""
        product = Product(name='Item', price=1999)
        assert product.price_dollars == 19.99
```

### Route Tests

Test Flask routes with the test client:

```python
import pytest
from flask import url_for

class TestAuthRoutes:
    """Tests for authentication routes."""
    
    def test_login_page_loads(self, client):
        """Test login page renders correctly."""
        response = client.get('/auth/login')
        
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid' in response.data
    
    def test_protected_route_requires_login(self, client):
        """Test that protected routes require authentication."""
        response = client.get('/admin/dashboard')
        
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_admin_route_requires_role(self, auth_client, test_user):
        """Test that admin routes require admin role."""
        response = auth_client.get('/admin/users')
        
        assert response.status_code == 403


class TestShopRoutes:
    """Tests for shop routes."""
    
    def test_product_listing(self, client, sample_products):
        """Test product listing page."""
        response = client.get('/shop')
        
        assert response.status_code == 200
        for product in sample_products:
            assert product.name.encode() in response.data
    
    def test_product_detail(self, client, sample_product):
        """Test product detail page."""
        response = client.get(f'/shop/product/{sample_product.slug}')
        
        assert response.status_code == 200
        assert sample_product.name.encode() in response.data
    
    def test_add_to_cart(self, client, sample_product):
        """Test adding product to cart."""
        response = client.post('/cart/add', data={
            'product_id': sample_product.id,
            'quantity': 2
        })
        
        assert response.status_code == 200
        # Verify cart contents
        cart_response = client.get('/cart')
        assert sample_product.name.encode() in cart_response.data
```

### API Tests

Test REST API endpoints:

```python
import pytest
import json

class TestAPIEndpoints:
    """Tests for REST API."""
    
    @pytest.fixture
    def api_key(self, session):
        """Create an API key for testing."""
        from app.models import ApiKey
        key = ApiKey(
            name='Test Key',
            key='sk_test_123456',
            scopes=['read:products', 'read:orders']
        )
        session.add(key)
        session.commit()
        return key
    
    def test_api_requires_auth(self, client):
        """Test API requires authentication."""
        response = client.get('/api/v1/products')
        
        assert response.status_code == 401
    
    def test_get_products(self, client, api_key, sample_products):
        """Test getting products via API."""
        response = client.get(
            '/api/v1/products',
            headers={'Authorization': f'Bearer {api_key.key}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == len(sample_products)
    
    def test_get_product_by_id(self, client, api_key, sample_product):
        """Test getting single product."""
        response = client.get(
            f'/api/v1/products/{sample_product.id}',
            headers={'Authorization': f'Bearer {api_key.key}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == sample_product.name
    
    def test_insufficient_scope(self, client, api_key):
        """Test API rejects requests without required scope."""
        response = client.post(
            '/api/v1/products',
            headers={'Authorization': f'Bearer {api_key.key}'},
            json={'name': 'New Product', 'price': 999}
        )
        
        assert response.status_code == 403
```

### Integration Tests

Test component interactions:

```python
import pytest

class TestCheckoutFlow:
    """Integration tests for checkout flow."""
    
    def test_complete_checkout(
        self, 
        client, 
        test_user, 
        sample_product,
        mock_stripe
    ):
        """Test complete checkout flow."""
        # Login
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'password123'
        })
        
        # Add to cart
        client.post('/cart/add', data={
            'product_id': sample_product.id,
            'quantity': 1
        })
        
        # Start checkout
        response = client.post('/checkout/start', data={
            'shipping_address': '123 Test St',
            'shipping_city': 'Test City',
            'shipping_zip': '12345'
        })
        
        assert response.status_code == 302
        
        # Verify order created
        from app.models import Order
        order = Order.query.filter_by(user_id=test_user.id).first()
        assert order is not None
        assert order.status == 'pending'
```

## Mocking

### Mocking External Services

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_stripe():
    """Mock Stripe API."""
    with patch('stripe.checkout.Session.create') as mock:
        mock.return_value = Mock(
            id='cs_test_123',
            url='https://checkout.stripe.com/...'
        )
        yield mock

@pytest.fixture
def mock_email():
    """Mock email sending."""
    with patch('app.modules.email.send_email') as mock:
        yield mock

def test_checkout_creates_stripe_session(client, auth_client, mock_stripe):
    """Test that checkout creates Stripe session."""
    response = auth_client.post('/checkout/create-session')
    
    mock_stripe.assert_called_once()
    assert response.status_code == 302
```

### Mocking Database Queries

```python
from unittest.mock import patch, MagicMock

def test_dashboard_with_many_orders(client, admin_client):
    """Test dashboard performance with many orders."""
    mock_orders = [MagicMock(total=i*100) for i in range(1000)]
    
    with patch('app.models.Order.query') as mock_query:
        mock_query.filter_by.return_value.all.return_value = mock_orders
        
        response = admin_client.get('/admin/dashboard')
        
        assert response.status_code == 200
```

## Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.slow
def test_generate_large_report():
    """Test that takes a long time."""
    ...

@pytest.mark.integration
def test_full_order_flow():
    """Integration test."""
    ...

@pytest.mark.e2e
def test_user_registration_to_purchase():
    """End-to-end test."""
    ...

@pytest.mark.parametrize("status,expected", [
    ("pending", False),
    ("paid", True),
    ("shipped", True),
])
def test_order_is_paid(status, expected):
    """Parametrized test."""
    ...
```

Run tests by marker:

```bash
# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run everything except e2e
pytest -m "not e2e"
```

## Coverage

### Generating Coverage Reports

```bash
# Terminal report
pytest --cov=app

# HTML report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# XML report (for CI)
pytest --cov=app --cov-report=xml

# Fail if coverage below threshold
pytest --cov=app --cov-fail-under=70
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = app
omit = 
    app/tests/*
    app/__init__.py
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:

[html]
directory = htmlcov
```

## CI Integration

Tests run automatically in GitHub Actions:

```yaml
# .github/workflows/ci.yml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Best Practices

### Do's

- ✅ Write tests for all new features
- ✅ Use descriptive test names
- ✅ One assertion per test (when practical)
- ✅ Use fixtures for common setup
- ✅ Test edge cases and error conditions
- ✅ Keep tests independent
- ✅ Use parametrize for similar tests

### Don'ts

- ❌ Don't test implementation details
- ❌ Don't share state between tests
- ❌ Don't use production database
- ❌ Don't ignore flaky tests
- ❌ Don't skip writing tests for "simple" code

## Troubleshooting

### Common Issues

**Tests fail with database errors:**
```bash
# Reset test database
flask db downgrade base
flask db upgrade
```

**Import errors:**
```bash
# Ensure app is installed in development mode
pip install -e .
```

**Fixtures not found:**
```bash
# Check conftest.py is in tests directory
# Verify pytest can find it
pytest --fixtures
```

---

*Last Updated: December 2024*
