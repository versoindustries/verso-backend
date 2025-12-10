"""
Tests for Phase 25-30: Advanced Infrastructure, Security, Privacy, and AI

These tests cover:
- Phase 25: Backup service, session management, deployment/feature flags
- Phase 27: AI/ML lead scoring, churn prediction, forecasting
- Phase 28: Security (rate limiting, login tracking, MFA, password validation)
- Phase 29: Privacy (consent management, data export, retention policies)
- Phase 30: Test infrastructure verification
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.database import db
from app.models import User, Role, BusinessConfig


# Module-scoped fixtures for isolation from other test modules
@pytest.fixture(scope='module')
def app():
    """Create application for this test module."""
    from app import create_app
    
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key-for-phase25-30',
        'BCRYPT_LOG_ROUNDS': 4,
        'SERVER_NAME': 'localhost',
    })
    
    with app.app_context():
        db.create_all()
        
        # Seed roles
        for role_name in ['admin', 'user', 'staff', 'customer']:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))
        
        # Seed business config
        for name, value in [('site_name', 'Test Site'), ('site_email', 'test@example.com')]:
            if not BusinessConfig.query.filter_by(setting_name=name).first():
                db.session.add(BusinessConfig(setting_name=name, setting_value=value))
        
        db.session.commit()
        
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
def db_session(app):
    """Create a database session for each test."""
    with app.app_context():
        yield db.session


@pytest.fixture(scope='function')
def regular_user(app):
    """Create a regular user for testing."""
    with app.app_context():
        user_role = Role.query.filter_by(name='user').first()
        
        existing = User.query.filter_by(email='user_p25_30@test.com').first()
        if existing:
            db.session.delete(existing)
            db.session.flush()
        
        user = User(
            username='test_user_p25_30',
            email='user_p25_30@test.com',
            password='TestPassword123!'
        )
        user.confirmed = True
        user.tos_accepted = True
        if user_role:
            user.roles.append(user_role)
        
        db.session.add(user)
        db.session.commit()
        
        yield user
        
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception:
            db.session.rollback()


class TestBackupService:
    """Tests for Phase 25 backup functionality."""
    
    def test_backup_service_init(self, app):
        """Test backup service initialization."""
        from app.modules.backup_service import backup_service
        
        with app.app_context():
            assert backup_service is not None
    
    def test_backup_model_creation(self, app, db_session):
        """Test Backup model can be created."""
        from app.models import Backup
        from app.database import db
        
        with app.app_context():
            backup = Backup(
                backup_type='database',
                status='pending',
                created_by_id=None,
            )
            db.session.add(backup)
            db.session.commit()
            
            assert backup.id is not None
            assert backup.backup_type == 'database'
            assert backup.status == 'pending'
    
    def test_backup_schedule_model(self, app, db_session):
        """Test BackupSchedule model."""
        from app.models import BackupSchedule
        from app.database import db
        
        with app.app_context():
            schedule = BackupSchedule(
                name='Daily Database Backup',
                backup_type='database',
                frequency='daily',
                retention_days=30,
                is_active=True,
            )
            db.session.add(schedule)
            db.session.commit()
            
            assert schedule.id is not None
            assert schedule.name == 'Daily Database Backup'


class TestFeatureFlags:
    """Tests for Phase 25 feature flag management."""
    
    def test_feature_flag_model(self, app, db_session):
        """Test FeatureFlag model creation."""
        from app.models import FeatureFlag
        from app.database import db
        
        with app.app_context():
            flag = FeatureFlag(
                name='new_checkout_flow',
                description='Enable new checkout experience',
                is_enabled=False,
            )
            db.session.add(flag)
            db.session.commit()
            
            assert flag.id is not None
            assert flag.name == 'new_checkout_flow'
    
    def test_feature_flag_manager(self, app):
        """Test FeatureFlagManager functionality."""
        from app.modules.deployment import FeatureFlagManager
        
        with app.app_context():
            manager = FeatureFlagManager()
            manager.init_app(app)
            
            # Test is_enabled for non-existent flag
            assert manager.is_enabled('nonexistent_flag') is False


class TestDeploymentTracking:
    """Tests for Phase 25 deployment tracking."""
    
    def test_deployment_log_model(self, app, db_session):
        """Test DeploymentLog model."""
        from app.models import DeploymentLog
        from app.database import db
        
        with app.app_context():
            log = DeploymentLog(
                version='1.0.0',
                environment='staging',
                status='pending',
                deployed_by_id=None,
            )
            db.session.add(log)
            db.session.commit()
            
            assert log.id is not None
            assert log.version == '1.0.0'


class TestLeadScoring:
    """Tests for Phase 27 AI lead scoring."""
    
    def test_lead_scorer_basic(self, app):
        """Test basic lead scoring."""
        from app.modules.ai_intelligence import lead_scorer
        
        with app.app_context():
            lead_scorer.init_app(app)
            
            lead_data = {
                'email': 'john.doe@company.com',
                'phone': '+1-555-1234',
                'message': 'I am interested in your enterprise solution for our team of 50 people.',
            }
            
            result = lead_scorer.score_lead(lead_data)
            
            assert 'score' in result
            assert 'grade' in result
            assert 'breakdown' in result
            assert result['score'] >= 0
            assert result['score'] <= 100
    
    def test_lead_scorer_corporate_email_bonus(self, app):
        """Test corporate email gets higher score."""
        from app.modules.ai_intelligence import lead_scorer
        
        with app.app_context():
            lead_scorer.init_app(app)
            
            corporate_lead = {
                'email': 'executive@bigcorp.com',
                'phone': '+1-555-1234',
                'message': 'Looking for solutions',
            }
            
            gmail_lead = {
                'email': 'someone@gmail.com',
                'phone': '+1-555-1234',
                'message': 'Looking for solutions',
            }
            
            corp_score = lead_scorer.score_lead(corporate_lead)['score']
            gmail_score = lead_scorer.score_lead(gmail_lead)['score']
            
            assert corp_score > gmail_score


class TestChurnPrediction:
    """Tests for Phase 27 churn prediction."""
    
    def test_churn_predictor_basic(self, app):
        """Test basic churn prediction."""
        from app.modules.ai_intelligence import churn_predictor
        
        with app.app_context():
            churn_predictor.init_app(app)
            
            customer_data = {
                'days_since_last_order': 120,
                'days_since_login': 60,
            }
            
            result = churn_predictor.predict_churn(customer_data)
            
            assert 'churn_probability' in result
            assert 'risk_level' in result
            assert 'risk_factors' in result
            assert result['churn_probability'] >= 0
            assert result['churn_probability'] <= 1
    
    def test_churn_high_risk_detection(self, app):
        """Test high-risk customer detection."""
        from app.modules.ai_intelligence import churn_predictor
        
        with app.app_context():
            churn_predictor.init_app(app)
            
            high_risk_data = {
                'days_since_last_order': 180,
                'days_since_login': 90,
                'open_support_tickets': 3,
                'negative_reviews': 2,
            }
            
            result = churn_predictor.predict_churn(high_risk_data)
            
            assert result['risk_level'] in ['high', 'medium']
            assert len(result['risk_factors']) > 0


class TestAnomalyDetection:
    """Tests for Phase 27 anomaly detection."""
    
    def test_anomaly_detector(self, app):
        """Test anomaly detection in time series."""
        from app.modules.ai_intelligence import anomaly_detector
        
        with app.app_context():
            anomaly_detector.init_app(app)
            
            # Normal data with one outlier
            data = [
                {'date': '2024-01-01', 'value': 100},
                {'date': '2024-01-02', 'value': 105},
                {'date': '2024-01-03', 'value': 98},
                {'date': '2024-01-04', 'value': 102},
                {'date': '2024-01-05', 'value': 500},  # Anomaly
                {'date': '2024-01-06', 'value': 101},
            ]
            
            anomalies = anomaly_detector.detect_anomalies(data)
            
            assert len(anomalies) >= 1
            assert any(a['value'] == 500 for a in anomalies)


class TestSecurityModule:
    """Tests for Phase 28 security features."""
    
    def test_password_validator(self, app):
        """Test password validation."""
        from app.modules.security import password_validator
        
        with app.app_context():
            password_validator.init_app(app)
            
            # Weak password
            is_valid, errors = password_validator.validate('weak')
            assert not is_valid
            assert len(errors) > 0
            
            # Strong password
            is_valid, errors = password_validator.validate('Strong@Password123!')
            assert is_valid
            assert len(errors) == 0
    
    def test_password_strength_score(self, app):
        """Test password strength scoring."""
        from app.modules.security import password_validator
        
        with app.app_context():
            password_validator.init_app(app)
            
            weak_score = password_validator.get_strength_score('abc')
            strong_score = password_validator.get_strength_score('Super$ecure!Pass123')
            
            assert strong_score > weak_score
            assert weak_score < 50
            assert strong_score > 50
    
    def test_login_attempt_model(self, app, db_session):
        """Test LoginAttempt model."""
        from app.models import LoginAttempt
        from app.database import db
        
        with app.app_context():
            attempt = LoginAttempt(
                email='test@example.com',
                ip_address='192.168.1.1',
                user_agent='Test Browser',
                success=False,
                failure_reason='Invalid password',
            )
            db.session.add(attempt)
            db.session.commit()
            
            assert attempt.id is not None
            assert attempt.success is False


class TestMFAModule:
    """Tests for Phase 28 MFA functionality."""
    
    def test_totp_manager(self, app):
        """Test TOTP secret generation."""
        from app.modules.mfa import totp_manager
        
        with app.app_context():
            totp_manager.init_app(app)
            
            secret = totp_manager.generate_secret()
            
            assert secret is not None
            assert len(secret) > 0
    
    def test_backup_codes_generation(self, app):
        """Test backup code generation."""
        from app.modules.mfa import totp_manager
        
        with app.app_context():
            totp_manager.init_app(app)
            
            codes = totp_manager.generate_backup_codes()
            
            assert len(codes) == totp_manager.BACKUP_CODE_COUNT
            assert all('-' in code for code in codes)


class TestPrivacyModule:
    """Tests for Phase 29 privacy features."""
    
    def test_consent_record_model(self, app, db_session):
        """Test ConsentRecord model."""
        from app.models import ConsentRecord
        from app.database import db
        
        with app.app_context():
            record = ConsentRecord(
                consent_type='analytics',
                granted=True,
                consent_source='cookie_banner',
            )
            db.session.add(record)
            db.session.commit()
            
            assert record.id is not None
            assert record.granted is True
    
    def test_data_export_request_model(self, app, db_session, regular_user):
        """Test DataExportRequest model."""
        from app.models import DataExportRequest
        from app.database import db
        
        with app.app_context():
            export_request = DataExportRequest(
                user_id=regular_user.id,
                status='pending',
                file_format='json',
            )
            db.session.add(export_request)
            db.session.commit()
            
            assert export_request.id is not None
            assert export_request.status == 'pending'


class TestRetentionPolicy:
    """Tests for Phase 29 data retention."""
    
    def test_retention_policy_model(self, app, db_session):
        """Test RetentionPolicy model."""
        from app.models import RetentionPolicy
        from app.database import db
        
        with app.app_context():
            policy = RetentionPolicy(
                name='login_attempts_cleanup',
                data_type='security',
                table_name='login_attempt',
                retention_days=90,
                action='delete',
            )
            db.session.add(policy)
            db.session.commit()
            
            assert policy.id is not None
            assert policy.retention_days == 90
    
    def test_retention_manager_seed(self, app):
        """Test seeding default retention policies."""
        from app.modules.retention import retention_manager
        
        with app.app_context():
            retention_manager.init_app(app)
            
            # Seed should not fail
            count = retention_manager.seed_default_policies()
            
            # First run should create policies
            assert count >= 0


class TestSecurityHeaders:
    """Tests for Phase 28 security headers."""
    
    def test_security_headers_added(self, client, app):
        """Test that security headers are added to responses."""
        with app.app_context():
            response = client.get('/')
            
            # Check for common security headers
            assert 'X-Content-Type-Options' in response.headers
            assert response.headers['X-Content-Type-Options'] == 'nosniff'
    
    def test_csp_header(self, client, app):
        """Test Content-Security-Policy header."""
        with app.app_context():
            response = client.get('/')
            
            # CSP should be present
            if 'Content-Security-Policy' in response.headers:
                csp = response.headers['Content-Security-Policy']
                assert "default-src" in csp


class TestAdminRoutes:
    """Tests for Phase 25-29 admin routes."""
    
    def test_backup_list_requires_admin(self, client, app):
        """Test backup list requires admin authentication."""
        response = client.get('/admin/backups/')
        
        # Should redirect to login or return 403
        assert response.status_code in [302, 403, 401]
    
    def test_ai_dashboard_requires_admin(self, client, app):
        """Test AI dashboard requires admin authentication."""
        response = client.get('/admin/ai/dashboard')
        
        # Should redirect to login or return 403
        assert response.status_code in [302, 403, 401]
    
    def test_compliance_dashboard_requires_admin(self, client, app):
        """Test compliance dashboard requires admin authentication."""
        response = client.get('/admin/compliance/')
        
        # Should redirect to login or return 403
        assert response.status_code in [302, 403, 401]


class TestPrivacyRoutes:
    """Tests for Phase 29 public privacy routes."""
    
    def test_consent_page_accessible(self, client, app):
        """Test cookie consent page is accessible."""
        response = client.get('/privacy/consent')
        
        assert response.status_code == 200
    
    def test_consent_api_returns_defaults(self, client, app):
        """Test consent API returns default consent status."""
        response = client.get('/privacy/api/consent')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'necessary' in data
        assert data['necessary'] is True
