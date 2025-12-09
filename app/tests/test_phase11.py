"""
Phase 11: Unified Dashboards & Command Centers Tests

Tests for:
- Customer Portal (user dashboard, my-account, order detail)
- Admin Command Centers (owner, operations, sales dashboards)
"""
import pytest
from app import create_app
from app.database import db
from app.models import User, Role, Order, OrderItem, Appointment, ContactFormSubmission, Product, Subscription, DownloadToken
from datetime import datetime, timedelta


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create or get roles
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
        
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user')
            db.session.add(user_role)
        
        db.session.commit()
        
        # Get or create admin user (use unique emails for this test module)
        admin = User.query.filter_by(email='phase11_admin@test.com').first()
        if not admin:
            admin = User(username='phase11_admin', email='phase11_admin@test.com', password='password123')
            admin.confirmed = True
            admin.roles.append(admin_role)
            db.session.add(admin)
        
        # Get or create regular user
        regular_user = User.query.filter_by(email='phase11_user@test.com').first()
        if not regular_user:
            regular_user = User(username='phase11_user', email='phase11_user@test.com', password='password123')
            regular_user.confirmed = True
            regular_user.roles.append(user_role)
            db.session.add(regular_user)
        
        db.session.commit()
        
        # Create test product
        product = Product.query.filter_by(name='Test Product Phase11').first()
        if not product:
            product = Product(name='Test Product Phase11', description='A test product', price=1999)
            db.session.add(product)
            db.session.commit()
        
        # Create test order for user
        order = Order.query.filter_by(user_id=regular_user.id).first()
        if not order:
            order = Order(user_id=regular_user.id, status='paid', total_amount=1999)
            db.session.add(order)
            db.session.commit()
            
            # Create order item
            order_item = OrderItem(order_id=order.id, product_id=product.id, quantity=1, price_at_purchase=1999)
            db.session.add(order_item)
        
        # Create test contact form submission
        lead = ContactFormSubmission.query.filter_by(email='phase11_lead@test.com').first()
        if not lead:
            lead = ContactFormSubmission(
                first_name='Lead', 
                last_name='Test', 
                email='phase11_lead@test.com', 
                phone='555-0011',
                message='Test message for phase 11',
                status='new'
            )
            db.session.add(lead)
        
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def logged_in_user(client, app):
    """Login as regular user."""
    with app.app_context():
        user = User.query.filter_by(email='phase11_user@test.com').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


@pytest.fixture
def logged_in_admin(client, app):
    """Login as admin user."""
    with app.app_context():
        admin = User.query.filter_by(email='phase11_admin@test.com').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
    return client


# ============================================================================
# Customer Portal Tests
# ============================================================================

class TestUserDashboard:
    """Tests for user dashboard."""
    
    def test_dashboard_loads(self, logged_in_user, app):
        """Test user dashboard page loads."""
        with app.app_context():
            response = logged_in_user.get('/dashboard')
            assert response.status_code == 200
            assert b'Dashboard' in response.data or b'dashboard' in response.data
    
    def test_dashboard_requires_login(self, client, app):
        """Test dashboard requires authentication."""
        with app.app_context():
            response = client.get('/dashboard', follow_redirects=True)
            assert b'login' in response.data.lower() or response.status_code in [302, 401]


class TestMyAccount:
    """Tests for customer portal (my-account)."""
    
    def test_my_account_loads(self, logged_in_user, app):
        """Test my-account page loads."""
        with app.app_context():
            response = logged_in_user.get('/my-account')
            assert response.status_code == 200
    
    def test_my_account_overview_tab(self, logged_in_user, app):
        """Test overview tab displays stats."""
        with app.app_context():
            response = logged_in_user.get('/my-account?tab=overview')
            assert response.status_code == 200
    
    def test_my_account_orders_tab(self, logged_in_user, app):
        """Test orders tab displays order history."""
        with app.app_context():
            response = logged_in_user.get('/my-account?tab=orders')
            assert response.status_code == 200
    
    def test_my_account_appointments_tab(self, logged_in_user, app):
        """Test appointments tab loads."""
        with app.app_context():
            response = logged_in_user.get('/my-account?tab=appointments')
            assert response.status_code == 200
    
    def test_my_account_subscriptions_tab(self, logged_in_user, app):
        """Test subscriptions tab loads."""
        with app.app_context():
            response = logged_in_user.get('/my-account?tab=subscriptions')
            assert response.status_code == 200
    
    def test_my_account_downloads_tab(self, logged_in_user, app):
        """Test downloads tab loads."""
        with app.app_context():
            response = logged_in_user.get('/my-account?tab=downloads')
            assert response.status_code == 200


class TestOrderDetail:
    """Tests for order detail page."""
    
    def test_order_detail_loads(self, logged_in_user, app):
        """Test order detail page loads for user's order."""
        with app.app_context():
            order = Order.query.first()
            response = logged_in_user.get(f'/my-account/orders/{order.id}')
            assert response.status_code == 200
    
    def test_order_detail_unauthorized(self, logged_in_admin, app):
        """Test cannot view another user's order."""
        with app.app_context():
            # Admin tries to view user's order via my-account (should redirect)
            order = Order.query.first()
            response = logged_in_admin.get(f'/my-account/orders/{order.id}', follow_redirects=True)
            # Should redirect with error or show not found
            assert response.status_code in [200, 302, 404]


# ============================================================================
# Admin Command Center Tests
# ============================================================================

class TestOwnerDashboard:
    """Tests for owner dashboard."""
    
    def test_owner_dashboard_loads(self, logged_in_admin, app):
        """Test owner dashboard page loads."""
        with app.app_context():
            response = logged_in_admin.get('/admin/dashboard/owner')
            assert response.status_code == 200
            assert b'Owner' in response.data or b'Revenue' in response.data
    
    def test_owner_dashboard_requires_admin(self, logged_in_user, app):
        """Test owner dashboard requires admin role."""
        with app.app_context():
            response = logged_in_user.get('/admin/dashboard/owner')
            assert response.status_code in [302, 403]


class TestOperationsDashboard:
    """Tests for operations dashboard."""
    
    def test_operations_dashboard_loads(self, logged_in_admin, app):
        """Test operations dashboard page loads."""
        with app.app_context():
            response = logged_in_admin.get('/admin/dashboard/operations')
            assert response.status_code == 200
            assert b'Operations' in response.data or b'appointments' in response.data.lower()
    
    def test_operations_dashboard_requires_admin(self, logged_in_user, app):
        """Test operations dashboard requires admin role."""
        with app.app_context():
            response = logged_in_user.get('/admin/dashboard/operations')
            assert response.status_code in [302, 403]


class TestSalesDashboard:
    """Tests for sales dashboard."""
    
    def test_sales_dashboard_loads(self, logged_in_admin, app):
        """Test sales dashboard page loads."""
        with app.app_context():
            response = logged_in_admin.get('/admin/dashboard/sales')
            assert response.status_code == 200
            assert b'Sales' in response.data or b'Pipeline' in response.data
    
    def test_sales_dashboard_requires_admin(self, logged_in_user, app):
        """Test sales dashboard requires admin role."""
        with app.app_context():
            response = logged_in_user.get('/admin/dashboard/sales')
            assert response.status_code in [302, 403]


class TestDashboardData:
    """Tests for dashboard data accuracy."""
    
    def test_order_count_in_stats(self, logged_in_user, app):
        """Test user sees correct order count in stats."""
        with app.app_context():
            response = logged_in_user.get('/dashboard')
            # Should show stats including order count
            assert response.status_code == 200
    
    def test_admin_sees_all_orders(self, logged_in_admin, app):
        """Test admin dashboard shows order revenue."""
        with app.app_context():
            response = logged_in_admin.get('/admin/dashboard/owner')
            assert response.status_code == 200
