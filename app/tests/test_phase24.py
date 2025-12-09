"""
Phase 24: Observability & Monitoring - Test Suite

Tests for:
- Health check endpoints
- Metrics endpoint
- Correlation ID middleware
- Structured logging
- Sensitive data masking
"""

import pytest
import json
import re
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestHealthEndpoints:
    """Tests for /health, /ready, /live endpoints."""
    
    def test_live_endpoint_returns_200(self, client):
        """Liveness probe should always return 200."""
        response = client.get('/live')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['alive'] is True
        assert 'timestamp' in data
        assert 'pid' in data
    
    def test_ready_endpoint_with_database(self, client):
        """Readiness probe should check database connectivity."""
        response = client.get('/ready')
        
        # Should return 200 if database is connected
        assert response.status_code in [200, 503]
        
        data = response.get_json()
        assert 'ready' in data
        assert 'timestamp' in data
    
    def test_health_endpoint_structure(self, client):
        """Health endpoint should return comprehensive status."""
        response = client.get('/health')
        
        assert response.status_code in [200, 503]
        
        data = response.get_json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'checks' in data
        
        # Should include all component checks
        checks = data['checks']
        assert 'database' in checks
        assert 'workers' in checks
        assert 'cache' in checks
        assert 'mail' in checks
    
    def test_health_endpoint_database_check(self, client):
        """Health endpoint database check should have status field."""
        response = client.get('/health')
        data = response.get_json()
        
        db_check = data['checks']['database']
        assert 'status' in db_check
        assert db_check['status'] in ['ok', 'error']


class TestMetricsEndpoint:
    """Tests for /metrics Prometheus endpoint."""
    
    def test_metrics_endpoint_returns_prometheus_format(self, client):
        """Metrics endpoint should return Prometheus text format."""
        response = client.get('/metrics')
        
        assert response.status_code == 200
        assert response.content_type.startswith('text/plain')
        
        content = response.data.decode('utf-8')
        
        # Should contain standard metric markers
        assert '# HELP' in content or '# TYPE' in content
    
    def test_metrics_contains_business_metrics(self, client):
        """Metrics should include business-level counters."""
        response = client.get('/metrics')
        content = response.data.decode('utf-8')
        
        # Should contain business metrics
        assert 'business_' in content or 'verso_' in content
    
    def test_metrics_token_protection(self, client, app):
        """Metrics endpoint should be protectable via token."""
        import os
        
        # Set metrics token
        with patch.dict(os.environ, {'METRICS_TOKEN': 'secret_token'}):
            # Without token should fail
            response = client.get('/metrics')
            assert response.status_code == 401
            
            # With wrong token should fail
            response = client.get('/metrics', headers={
                'Authorization': 'Bearer wrong_token'
            })
            assert response.status_code == 403
            
            # With correct token should succeed
            response = client.get('/metrics', headers={
                'Authorization': 'Bearer secret_token'
            })
            assert response.status_code == 200


class TestCorrelationId:
    """Tests for request correlation ID middleware."""
    
    def test_response_has_request_id_header(self, client):
        """Response should include X-Request-ID header."""
        response = client.get('/health')
        
        assert 'X-Request-ID' in response.headers
        
        # Should be a valid UUID format
        request_id = response.headers['X-Request-ID']
        assert len(request_id) > 0
    
    def test_client_provided_request_id_is_echoed(self, client):
        """Client-provided X-Request-ID should be echoed back."""
        custom_id = 'custom-request-id-12345'
        
        response = client.get('/health', headers={
            'X-Request-ID': custom_id
        })
        
        assert response.headers.get('X-Request-ID') == custom_id


class TestSensitiveDataMasking:
    """Tests for sensitive data masking in logs."""
    
    def test_password_is_masked(self):
        """Passwords should be masked in log output."""
        from app.modules.logging_config import mask_sensitive_data
        
        # Various password formats
        test_cases = [
            ('password=secret123', '[REDACTED]'),
            ('"password": "secret123"', '[REDACTED]'),
            ("'password': 'secret123'", '[REDACTED]'),
        ]
        
        for input_text, expected_marker in test_cases:
            result = mask_sensitive_data(input_text)
            assert 'secret123' not in result, f"Password not masked in: {input_text}"
            assert expected_marker in result
    
    def test_api_key_is_masked(self):
        """API keys should be masked."""
        from app.modules.logging_config import mask_sensitive_data
        
        text = 'api_key=sk_live_abcd1234'
        result = mask_sensitive_data(text)
        
        assert 'sk_live_abcd1234' not in result
        assert '[REDACTED]' in result
    
    def test_token_is_masked(self):
        """Tokens should be masked."""
        from app.modules.logging_config import mask_sensitive_data
        
        text = 'token=eyJhbGciOiJIUzI1NiJ9.payload.signature'
        result = mask_sensitive_data(text)
        
        assert 'eyJhbGciOiJIUzI1NiJ9' not in result
        assert '[REDACTED]' in result
    
    def test_authorization_header_is_masked(self):
        """Authorization headers should be masked."""
        from app.modules.logging_config import mask_sensitive_data
        
        text = 'Authorization: Bearer secret_bearer_token'
        result = mask_sensitive_data(text)
        
        assert 'secret_bearer_token' not in result
        assert '[REDACTED]' in result
    
    def test_credit_card_is_partially_masked(self):
        """Credit card numbers should be partially masked."""
        from app.modules.logging_config import mask_sensitive_data
        
        text = 'Card: 4111-1111-1111-1234'
        result = mask_sensitive_data(text)
        
        # Last 4 digits should be masked
        assert '1234' not in result
        # First digits should remain for identification
        assert '4111' in result


class TestJsonFormatter:
    """Tests for JSON log formatter."""
    
    def test_json_formatter_produces_valid_json(self):
        """JSON formatter should produce valid JSON output."""
        from app.modules.logging_config import StructuredJsonFormatter
        import logging
        
        formatter = StructuredJsonFormatter(include_request=False)
        
        # Create a log record
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        
        # Should be valid JSON
        data = json.loads(output)
        
        assert data['level'] == 'INFO'
        assert data['message'] == 'Test message'
        assert data['logger'] == 'test.logger'
        assert 'timestamp' in data
    
    def test_json_formatter_masks_sensitive_data(self):
        """JSON formatter should mask sensitive data."""
        from app.modules.logging_config import StructuredJsonFormatter
        import logging
        
        formatter = StructuredJsonFormatter(mask_sensitive=True, include_request=False)
        
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Login with password=secret123',
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert 'secret123' not in data['message']
        assert '[REDACTED]' in data['message']


class TestMetricsCollector:
    """Tests for in-memory metrics collector."""
    
    def test_record_request(self):
        """Should record HTTP requests with method, path, status, duration."""
        from app.routes.observability import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record_request('GET', '/api/users', 200, 0.150)
        collector.record_request('POST', '/api/users', 201, 0.250)
        collector.record_request('GET', '/api/users', 500, 0.050)
        
        stats = collector.get_request_stats()
        
        assert stats['total'] == 3
        assert stats['errors'] == 1
        assert stats['error_rate'] == 1/3
    
    def test_record_query(self):
        """Should track database queries."""
        from app.routes.observability import MetricsCollector
        
        collector = MetricsCollector()
        
        collector.record_query(0.010)
        collector.record_query(0.020)
        collector.record_query(0.600)  # Slow query
        
        stats = collector.get_db_stats()
        
        assert stats['total_queries'] == 3
        assert stats['slow_queries'] == 1
    
    def test_prometheus_output_format(self):
        """Should generate valid Prometheus format."""
        from app.routes.observability import MetricsCollector
        from flask import Flask
        
        app = Flask(__name__)
        app.config['VERSION'] = '1.0.0'
        
        collector = MetricsCollector()
        collector.record_request('GET', '/test', 200, 0.1)
        
        with app.app_context():
            output = collector.get_prometheus_metrics()
        
        # Check Prometheus format markers
        assert '# HELP' in output
        assert '# TYPE' in output
        
        # Check for expected metrics
        assert 'http_requests_total' in output
        assert 'verso_uptime_seconds' in output


class TestAdminMetricsDashboard:
    """Tests for admin metrics dashboard."""
    
    def test_admin_metrics_requires_auth(self, client):
        """Admin metrics dashboard should require authentication."""
        response = client.get('/admin/metrics')
        
        # Should redirect to login
        assert response.status_code in [302, 401, 403]
    
    def test_admin_metrics_accessible_to_admin(self, client, admin_user, app):
        """Admin users should be able to access metrics dashboard."""
        # admin_user fixture returns user_id directly
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user)
                sess['_fresh'] = True
        
        response = client.get('/admin/metrics')
        
        # Should be accessible
        assert response.status_code == 200


class TestAdvancedObservability:
    """Tests for advanced observability features."""
    
    def test_grafana_dashboard_generation(self):
        """Should generate valid Grafana dashboard JSON."""
        from app.modules.advanced_observability import generate_grafana_dashboard
        
        dashboard = generate_grafana_dashboard()
        
        assert 'title' in dashboard
        assert dashboard['title'] == 'Verso Backend Dashboard'
        assert 'panels' in dashboard
        assert len(dashboard['panels']) > 0
        
        # Check for expected panels
        panel_titles = [p.get('title') for p in dashboard['panels']]
        assert 'Request Rate' in panel_titles
        assert 'Error Rate' in panel_titles
    
    def test_alerting_rules_generation(self):
        """Should generate valid Prometheus alerting rules."""
        from app.modules.advanced_observability import generate_alerting_rules
        
        rules = generate_alerting_rules()
        
        assert 'groups' in rules
        assert len(rules['groups']) > 0
        
        group = rules['groups'][0]
        assert group['name'] == 'verso-backend'
        assert 'rules' in group
        
        # Check for critical alerts
        alert_names = [r['alert'] for r in group['rules']]
        assert 'HighErrorRate' in alert_names
        assert 'ServiceDown' in alert_names
    
    def test_rum_script_disabled_by_default(self):
        """RUM script should be empty when disabled."""
        import os
        from unittest.mock import patch
        
        with patch.dict(os.environ, {'RUM_ENABLED': ''}):
            from app.modules.advanced_observability import get_rum_script
            script = get_rum_script()
            assert script == ''
    
    def test_rum_script_custom_enabled(self):
        """Custom RUM script should be generated when enabled."""
        import os
        from unittest.mock import patch
        
        with patch.dict(os.environ, {'RUM_ENABLED': 'true', 'RUM_PROVIDER': 'custom'}):
            # Need to reimport to pick up env changes
            from importlib import reload
            import app.modules.advanced_observability as adv_obs
            reload(adv_obs)
            
            script = adv_obs.get_rum_script()
            assert 'Verso RUM' in script
            assert 'collectPerformance' in script
            assert 'trackErrors' in script
    
    def test_loki_handler_creation(self):
        """LokiHandler should be creatable."""
        from app.modules.advanced_observability import LokiHandler
        
        handler = LokiHandler(url='http://loki:3100/loki/api/v1/push')
        assert handler.url == 'http://loki:3100/loki/api/v1/push'
        assert handler.labels['app'] == 'verso-backend'
    
    def test_elasticsearch_handler_creation(self):
        """ElasticsearchHandler should be creatable."""
        from app.modules.advanced_observability import ElasticsearchHandler
        
        handler = ElasticsearchHandler(url='http://elasticsearch:9200')
        assert handler.url == 'http://elasticsearch:9200'
        assert handler.index_prefix == 'verso-logs'
    
    def test_cloudwatch_handler_creation(self):
        """CloudWatchHandler should be creatable."""
        from app.modules.advanced_observability import CloudWatchHandler
        
        handler = CloudWatchHandler(log_group='test-group')
        assert handler.log_group == 'test-group'
    
    def test_sentry_before_send_filters_sensitive_data(self):
        """Sentry before_send should filter sensitive headers."""
        from app.modules.advanced_observability import _sentry_before_send
        
        event = {
            'request': {
                'headers': {
                    'Authorization': 'Bearer secret_token',
                    'Cookie': 'session=abc123',
                    'Content-Type': 'application/json'
                },
                'data': {
                    'username': 'testuser',
                    'password': 'secretpass'
                }
            }
        }
        
        result = _sentry_before_send(event, {})
        
        assert result['request']['headers']['Authorization'] == '[REDACTED]'
        assert result['request']['headers']['Cookie'] == '[REDACTED]'
        assert result['request']['headers']['Content-Type'] == 'application/json'
        assert result['request']['data']['password'] == '[REDACTED]'
        assert result['request']['data']['username'] == 'testuser'
    
    def test_traced_decorator_without_otel(self):
        """traced decorator should work when OpenTelemetry is not configured."""
        from app.modules.advanced_observability import traced
        
        @traced('test-span')
        def my_function():
            return 'success'
        
        # Should work without error even without OTEL configured
        result = my_function()
        assert result == 'success'


class TestObservabilityConfigEndpoint:
    """Tests for observability configuration endpoint."""
    
    def test_config_endpoint_returns_status(self, client, admin_user, app):
        """Config endpoint should return observability status."""
        # admin_user fixture returns user_id directly
        with app.app_context():
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user)
                sess['_fresh'] = True
        
        response = client.get('/admin/observability-config')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'log_aggregation' in data
        assert 'tracing' in data
        assert 'rum' in data
        assert 'error_tracking' in data
        assert 'metrics' in data


# Pytest fixtures
@pytest.fixture
def app():
    """Create application for testing."""
    from app import create_app
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        from app.database import db
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for the app."""
    return app.test_client()


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing. Returns user_id to avoid DetachedInstanceError."""
    from app.database import db
    from app.models import User, Role
    
    with app.app_context():
        # Create admin role if it doesn't exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
        
        # Create admin user - User __init__ takes (username, email, password)
        user = User(
            username='testadmin',
            email='admin@test.com',
            password='adminpass123'
        )
        user.first_name = 'Test'
        user.last_name = 'Admin'
        user.confirmed = True
        user.tos_accepted = True
        user.roles.append(admin_role)
        db.session.add(user)
        db.session.commit()
        
        # Return user_id to avoid DetachedInstanceError
        return user.id

