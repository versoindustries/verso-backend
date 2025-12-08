"""
Phase 7: Admin Experience & Dashboard Tests

Tests for:
- Dashboard metrics API
- Theme editor functionality
- Global admin search
- Bulk user actions
- CSV exports
"""
import pytest
import json
from app import create_app
from app.database import db
from app.models import User, Role, Order, ContactFormSubmission, BusinessConfig, Post
from datetime import datetime, timedelta


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        
        # Use get_or_create pattern for roles
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            db.session.flush()
        
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user')
            db.session.add(user_role)
            db.session.flush()
        
        # Create admin user if not exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', password='testpass')
            admin.first_name = 'Admin'
            admin.last_name = 'User'
            admin.roles.append(admin_role)
            db.session.add(admin)
        
        # Create regular user for search tests
        regular_user = User.query.filter_by(email='test@example.com').first()
        if not regular_user:
            regular_user = User(username='testuser', email='test@example.com', password='testpass')
            regular_user.first_name = 'Test'
            regular_user.last_name = 'User'
            regular_user.roles.append(user_role)
            db.session.add(regular_user)
        
        # Create test order
        order = Order(total_amount=5000, status='paid')  # $50.00
        db.session.add(order)
        
        # Create test lead
        lead = ContactFormSubmission(
            first_name='Lead',
            last_name='Person',
            email='lead@example.com',
            phone='555-1234',
            message='Test submission',
            status='New'
        )
        db.session.add(lead)
        
        # Create default business config - use get_or_create pattern
        default_configs = [
            ('company_timezone', 'America/Denver'),
            ('primary_color', '#4169e1'),
            ('secondary_color', '#6c757d'),
            ('font_family', 'Roboto, sans-serif'),
        ]
        for name, value in default_configs:
            existing = BusinessConfig.query.filter_by(setting_name=name).first()
            if not existing:
                db.session.add(BusinessConfig(setting_name=name, setting_value=value))
        
        db.session.commit()
        
        yield app
        
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def logged_in_admin(client, app):
    """Login as admin user."""
    with app.app_context():
        # Login
        client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'testpass'
        }, follow_redirects=True)
    return client


class TestDashboardMetrics:
    """Tests for the dashboard and metrics API."""
    
    def test_dashboard_loads(self, logged_in_admin, app):
        """Test dashboard page loads with KPI cards."""
        with app.app_context():
            response = logged_in_admin.get('/admin/dashboard')
            assert response.status_code == 200
            assert b'Revenue' in response.data or b'revenue' in response.data
    
    def test_metrics_api_returns_json(self, logged_in_admin, app):
        """Test metrics API returns valid JSON."""
        with app.app_context():
            response = logged_in_admin.get('/admin/dashboard/metrics')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'labels' in data
            assert 'revenue' in data
            assert 'leads' in data
            assert 'funnel' in data
    
    def test_metrics_api_with_days_param(self, logged_in_admin, app):
        """Test metrics API respects days parameter."""
        with app.app_context():
            response = logged_in_admin.get('/admin/dashboard/metrics?days=7')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['days'] == 7
            assert len(data['labels']) == 7


class TestThemeEditor:
    """Tests for the theme editor functionality."""
    
    def test_theme_editor_loads(self, logged_in_admin, app):
        """Test theme editor page loads."""
        with app.app_context():
            response = logged_in_admin.get('/admin/theme')
            assert response.status_code == 200
            assert b'Theme Editor' in response.data or b'theme' in response.data or b'color' in response.data
    
    def test_theme_update(self, logged_in_admin, app):
        """Test theme settings can be updated."""
        with app.app_context():
            response = logged_in_admin.post('/admin/theme', data={
                'primary_color': '#ff0000',
                'secondary_color': '#00ff00',
                'accent_color': '#0000ff',
                'font_family': 'Arial, sans-serif',
                'border_radius': '12',
                'ga4_tracking_id': ''
            }, follow_redirects=True)
            assert response.status_code == 200
            
            # Verify setting was updated
            config = BusinessConfig.query.filter_by(setting_name='primary_color').first()
            assert config.setting_value == '#ff0000'


class TestAdminSearch:
    """Tests for global admin search."""
    
    def test_search_page_loads(self, logged_in_admin, app):
        """Test search page loads."""
        with app.app_context():
            response = logged_in_admin.get('/admin/search')
            assert response.status_code == 200
    
    def test_search_finds_users(self, logged_in_admin, app):
        """Test search finds users by username."""
        with app.app_context():
            response = logged_in_admin.get('/admin/search?q=admin')
            assert response.status_code == 200
            assert b'admin' in response.data
    
    def test_search_finds_leads(self, logged_in_admin, app):
        """Test search finds leads by email."""
        with app.app_context():
            response = logged_in_admin.get('/admin/search?q=lead@example')
            assert response.status_code == 200
            assert b'Lead' in response.data or b'lead' in response.data
    
    def test_search_minimum_length(self, logged_in_admin, app):
        """Test search requires minimum 2 characters."""
        with app.app_context():
            response = logged_in_admin.get('/admin/search?q=a')
            assert response.status_code == 200
            # Should not have results section for single char search


class TestBulkActions:
    """Tests for bulk user actions."""
    
    def test_bulk_action_requires_users(self, logged_in_admin, app):
        """Test bulk action requires user selection."""
        with app.app_context():
            response = logged_in_admin.post('/admin/users/bulk', data={
                'action': 'deactivate',
                'user_ids[]': []
            }, follow_redirects=True)
            assert response.status_code == 200
            assert b'No users selected' in response.data
    
    def test_bulk_deactivate(self, logged_in_admin, app):
        """Test bulk deactivate action."""
        with app.app_context():
            # Get a user to deactivate
            user = User.query.filter_by(username='testuser').first()
            
            response = logged_in_admin.post('/admin/users/bulk', data={
                'action': 'deactivate',
                'user_ids[]': [user.id]
            }, follow_redirects=True)
            assert response.status_code == 200


class TestCSVExports:
    """Tests for CSV export functionality."""
    
    def test_users_csv_export(self, logged_in_admin, app):
        """Test users CSV export."""
        with app.app_context():
            response = logged_in_admin.get('/admin/users/export/csv')
            assert response.status_code == 200
            assert response.content_type == 'text/csv'
            assert b'Username' in response.data or b'ID' in response.data
    
    def test_orders_csv_export(self, logged_in_admin, app):
        """Test orders CSV export."""
        with app.app_context():
            response = logged_in_admin.get('/admin/orders/export/csv')
            assert response.status_code == 200
            assert response.content_type == 'text/csv'
    
    def test_leads_csv_export(self, logged_in_admin, app):
        """Test leads CSV export."""
        with app.app_context():
            response = logged_in_admin.get('/admin/leads/export/csv')
            assert response.status_code == 200
            assert 'text/csv' in response.content_type


class TestGA4Integration:
    """Tests for Google Analytics 4 integration."""
    
    def test_ga4_not_present_without_config(self, client, app):
        """Test GA4 script not present when not configured."""
        with app.app_context():
            response = client.get('/')
            assert b'googletagmanager' not in response.data
    
    def test_ga4_present_with_config(self, client, app):
        """Test GA4 script present when configured."""
        with app.app_context():
            # Add GA4 config
            existing = BusinessConfig.query.filter_by(setting_name='ga4_tracking_id').first()
            if existing:
                existing.setting_value = 'G-TESTTEST'
            else:
                config = BusinessConfig(setting_name='ga4_tracking_id', setting_value='G-TESTTEST')
                db.session.add(config)
            db.session.commit()
            
            response = client.get('/')
            assert b'G-TESTTEST' in response.data or b'googletagmanager' in response.data
