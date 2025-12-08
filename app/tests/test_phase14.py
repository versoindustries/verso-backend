"""
Phase 14: Analytics & Reporting Engine Tests

Tests for the enhanced analytics platform, conversion tracking,
financial reports, and export functionality.
"""

import pytest
from datetime import datetime, timedelta
from flask import url_for
from app import create_app, db
from app.models import (
    User, Role, PageView, VisitorSession, ConversionGoal, 
    Conversion, Funnel, FunnelStep, SavedReport, ReportExport,
    Order, Product
)


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create admin role and user
        admin_role = Role(name='admin')
        db.session.add(admin_role)
        db.session.commit()
        
        admin_user = User(
            username='testadmin',
            email='admin@test.com',
            password='password',
            confirmed=True
        )
        admin_user.roles.append(admin_role)
        db.session.add(admin_user)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def logged_in_admin(client, app):
    """Login as admin user."""
    with app.app_context():
        user = User.query.filter_by(email='admin@test.com').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


# ============================================================================
# PageView Model Tests
# ============================================================================

class TestPageViewModel:
    """Tests for the enhanced PageView model."""
    
    def test_create_pageview_with_utm(self, app):
        """Test creating a page view with UTM parameters."""
        with app.app_context():
            pv = PageView(
                url='/test-page',
                session_id='test-session-123',
                utm_source='google',
                utm_medium='cpc',
                utm_campaign='summer_sale',
                device_type='desktop',
                browser='Chrome',
                os='Windows'
            )
            db.session.add(pv)
            db.session.commit()
            
            assert pv.id is not None
            assert pv.utm_source == 'google'
            assert pv.utm_medium == 'cpc'
            assert pv.device_type == 'desktop'
    
    def test_pageview_user_relationship(self, app):
        """Test page view linked to user."""
        with app.app_context():
            user = User.query.first()
            pv = PageView(
                url='/dashboard',
                user_id=user.id,
                session_id='user-session-456'
            )
            db.session.add(pv)
            db.session.commit()
            
            assert pv.user.email == 'admin@test.com'
            assert user.page_views.count() >= 1


# ============================================================================
# VisitorSession Model Tests
# ============================================================================

class TestVisitorSessionModel:
    """Tests for visitor session tracking."""
    
    def test_create_session(self, app):
        """Test creating a new visitor session."""
        with app.app_context():
            session = VisitorSession(
                session_token='unique-token-abc123',
                ip_hash='hashed-ip-12345',
                entry_page='/home',
                exit_page='/home',
                utm_source='newsletter',
                device_type='mobile',
                browser='Safari',
                os='iOS'
            )
            db.session.add(session)
            db.session.commit()
            
            assert session.id is not None
            assert session.bounce is True  # Default is true
            assert session.pages_viewed == 1
    
    def test_update_session_activity(self, app):
        """Test updating session with additional page views."""
        with app.app_context():
            session = VisitorSession(
                session_token='update-test-token',
                entry_page='/page1',
                exit_page='/page1'
            )
            db.session.add(session)
            db.session.commit()
            
            # Simulate viewing another page
            session.update_activity('/page2')
            db.session.commit()
            
            assert session.pages_viewed == 2
            assert session.exit_page == '/page2'
            assert session.bounce is False
    
    def test_end_session(self, app):
        """Test ending a session records duration."""
        with app.app_context():
            session = VisitorSession(
                session_token='end-test-token',
                entry_page='/start',
                started_at=datetime.utcnow() - timedelta(minutes=5)
            )
            db.session.add(session)
            db.session.commit()
            
            session.end_session()
            db.session.commit()
            
            assert session.ended_at is not None
            assert session.duration_seconds >= 300  # At least 5 minutes


# ============================================================================
# ConversionGoal Tests
# ============================================================================

class TestConversionGoal:
    """Tests for conversion goals."""
    
    def test_create_goal(self, app):
        """Test creating a conversion goal."""
        with app.app_context():
            goal = ConversionGoal(
                name='Purchase Completed',
                goal_type='purchase',
                target_value=100.00,
                is_active=True
            )
            db.session.add(goal)
            db.session.commit()
            
            assert goal.id is not None
            assert goal.count_once_per_session is True  # Default
    
    def test_create_page_visit_goal(self, app):
        """Test creating a page visit goal with target path."""
        with app.app_context():
            goal = ConversionGoal(
                name='Contact Page Visit',
                goal_type='page_visit',
                target_path='/contact/thank-you'
            )
            db.session.add(goal)
            db.session.commit()
            
            assert goal.target_path == '/contact/thank-you'


# ============================================================================
# Funnel Tests
# ============================================================================

class TestFunnel:
    """Tests for conversion funnels."""
    
    def test_create_funnel_with_steps(self, app):
        """Test creating a funnel with steps."""
        with app.app_context():
            # Create goals first
            goal1 = ConversionGoal(name='Homepage', goal_type='page_visit', target_path='/')
            goal2 = ConversionGoal(name='Add to Cart', goal_type='custom')
            goal3 = ConversionGoal(name='Purchase', goal_type='purchase')
            db.session.add_all([goal1, goal2, goal3])
            db.session.commit()
            
            # Create funnel
            funnel = Funnel(name='Purchase Funnel', description='Track purchase flow')
            db.session.add(funnel)
            db.session.commit()
            
            # Add steps
            step1 = FunnelStep(funnel_id=funnel.id, goal_id=goal1.id, name='View Homepage', step_order=0)
            step2 = FunnelStep(funnel_id=funnel.id, goal_id=goal2.id, name='Add to Cart', step_order=1)
            step3 = FunnelStep(funnel_id=funnel.id, goal_id=goal3.id, name='Complete Purchase', step_order=2)
            db.session.add_all([step1, step2, step3])
            db.session.commit()
            
            assert funnel.steps.count() == 3
            assert funnel.steps.first().name == 'View Homepage'


# ============================================================================
# SavedReport Tests
# ============================================================================

class TestSavedReport:
    """Tests for saved reports."""
    
    def test_create_saved_report(self, app):
        """Test creating a saved report."""
        with app.app_context():
            user = User.query.first()
            report = SavedReport(
                name='Monthly Revenue',
                report_type='revenue',
                config_json={'days': 30, 'limit': 100},
                created_by_id=user.id,
                is_public=True
            )
            db.session.add(report)
            db.session.commit()
            
            assert report.id is not None
            assert report.config_json['days'] == 30
            assert report.is_archived is False


# ============================================================================
# Analytics Routes Tests
# ============================================================================

class TestAnalyticsRoutes:
    """Tests for analytics routes."""
    
    def test_dashboard_accessible(self, logged_in_admin, app):
        """Test analytics dashboard is accessible to admin."""
        with app.app_context():
            response = logged_in_admin.get('/admin/analytics/')
            assert response.status_code == 200
    
    def test_traffic_page(self, logged_in_admin, app):
        """Test traffic analysis page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/analytics/traffic')
            assert response.status_code == 200
    
    def test_visitors_page(self, logged_in_admin, app):
        """Test visitors page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/analytics/visitors')
            assert response.status_code == 200
    
    def test_sessions_page(self, logged_in_admin, app):
        """Test sessions page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/analytics/sessions')
            assert response.status_code == 200
    
    def test_goals_page(self, logged_in_admin, app):
        """Test goals listing page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/analytics/goals')
            assert response.status_code == 200
    
    def test_funnels_page(self, logged_in_admin, app):
        """Test funnels listing page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/analytics/funnels')
            assert response.status_code == 200
    
    def test_create_goal(self, logged_in_admin, app):
        """Test creating a conversion goal."""
        with app.app_context():
            response = logged_in_admin.post('/admin/analytics/goals/new', data={
                'name': 'Test Goal',
                'goal_type': 'page_visit',
                'target_path': '/thank-you',
                'target_value': '50',
                'count_once_per_session': 'on'
            }, follow_redirects=True)
            assert response.status_code == 200
            
            goal = ConversionGoal.query.filter_by(name='Test Goal').first()
            assert goal is not None
    
    def test_daily_traffic_api(self, logged_in_admin, app):
        """Test daily traffic API endpoint."""
        with app.app_context():
            response = logged_in_admin.get('/admin/analytics/api/daily_traffic')
            assert response.status_code == 200
            data = response.get_json()
            assert 'labels' in data
            assert 'page_views' in data


# ============================================================================
# Reports Routes Tests
# ============================================================================

class TestReportsRoutes:
    """Tests for reports routes."""
    
    def test_revenue_page(self, logged_in_admin, app):
        """Test revenue report page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/reports/revenue')
            assert response.status_code == 200
    
    def test_products_page(self, logged_in_admin, app):
        """Test products report page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/reports/products')
            assert response.status_code == 200
    
    def test_customers_page(self, logged_in_admin, app):
        """Test customers report page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/reports/customers')
            assert response.status_code == 200
    
    def test_tax_page(self, logged_in_admin, app):
        """Test tax report page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/reports/tax')
            assert response.status_code == 200
    
    def test_saved_reports_page(self, logged_in_admin, app):
        """Test saved reports page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/reports/saved')
            assert response.status_code == 200
    
    def test_report_builder_page(self, logged_in_admin, app):
        """Test report builder page."""
        with app.app_context():
            response = logged_in_admin.get('/admin/reports/builder')
            assert response.status_code == 200
    
    def test_create_saved_report(self, logged_in_admin, app):
        """Test creating a saved report."""
        with app.app_context():
            response = logged_in_admin.post('/admin/reports/saved/new', data={
                'name': 'Test Report',
                'report_type': 'revenue',
                'description': 'Test description',
                'days': '30',
                'limit': '100'
            }, follow_redirects=True)
            assert response.status_code == 200
            
            report = SavedReport.query.filter_by(name='Test Report').first()
            assert report is not None
    
    def test_export_csv(self, logged_in_admin, app):
        """Test CSV export."""
        with app.app_context():
            response = logged_in_admin.get('/admin/reports/export/revenue/csv?days=30')
            assert response.status_code == 200
            assert 'text/csv' in response.content_type


# ============================================================================
# Reporting Module Tests
# ============================================================================

class TestReportingModule:
    """Tests for reporting module functions."""
    
    def test_parse_user_agent(self, app):
        """Test user agent parsing."""
        from app.modules.reporting import parse_user_agent
        
        # Desktop Chrome
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        result = parse_user_agent(ua)
        assert result['device_type'] == 'desktop'
        assert result['browser'] == 'Chrome'
        assert result['os'] == 'Windows'
        
        # Mobile Safari
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        result = parse_user_agent(ua)
        assert result['device_type'] == 'mobile'
        assert result['os'] == 'iOS'
    
    def test_get_date_range_presets(self, app):
        """Test date range presets."""
        from app.modules.reporting import get_date_range_presets
        
        with app.app_context():
            presets = get_date_range_presets()
            assert 'today' in presets
            assert 'last_7_days' in presets
            assert 'last_30_days' in presets
            assert 'this_month' in presets
            
            # Verify dates are valid
            start, end = presets['last_7_days']
            assert start < end
    
    def test_export_to_csv(self, app):
        """Test CSV export function."""
        from app.modules.reporting import export_to_csv
        
        with app.app_context():
            data = [
                {'name': 'Product A', 'revenue': 100.0},
                {'name': 'Product B', 'revenue': 200.0}
            ]
            headers = ['name', 'revenue']
            
            output = export_to_csv(data, headers)
            csv_content = output.getvalue()
            
            assert 'name,revenue' in csv_content
            assert 'Product A' in csv_content
            assert '100.0' in csv_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
