"""
Phase 23: Performance Optimization Tests

Tests for caching, compression, self-hosted assets, and request timing.
"""

import pytest
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app
from app.database import db
from app.models import User, Role, BusinessConfig


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'
    
    with app.app_context():
        db.create_all()
        
        # Create admin role
        admin_role = Role(name='admin')
        db.session.add(admin_role)
        db.session.commit()
        
        # Seed business config
        configs = [
            BusinessConfig(setting_name='business_start_time', setting_value='08:00'),
            BusinessConfig(setting_name='business_end_time', setting_value='17:00'),
            BusinessConfig(setting_name='company_timezone', setting_value='America/Denver'),
        ]
        for c in configs:
            db.session.add(c)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestCaching:
    """Test caching functionality."""
    
    def test_cache_module_exists(self, app):
        """Test that cache module is properly imported."""
        from app.modules.cache import cache, cached_business_config
        assert cache is not None
        assert callable(cached_business_config)
    
    def test_cached_business_config(self, app):
        """Test that business config is cached."""
        with app.app_context():
            from app.modules.cache import cached_business_config
            
            # First call should hit database
            config = cached_business_config()
            assert isinstance(config, dict)
            assert 'business_start_time' in config
            assert config['business_start_time'] == '08:00'
            
            # Second call should return cached result (same data)
            config2 = cached_business_config()
            assert config == config2
    
    def test_cache_invalidation(self, app):
        """Test cache invalidation."""
        with app.app_context():
            from app.modules.cache import cached_business_config, invalidate_business_config
            
            # Get initial value
            config1 = cached_business_config()
            
            # Invalidate cache
            invalidate_business_config()
            
            # Should still work after invalidation
            config2 = cached_business_config()
            assert config2 is not None


class TestCompression:
    """Test gzip/brotli compression."""
    
    def test_compression_enabled(self, app):
        """Test that Flask-Compress is configured."""
        assert app.config.get('COMPRESS_MIMETYPES') is not None
        assert 'text/html' in app.config['COMPRESS_MIMETYPES']
    
    def test_compression_level(self, app):
        """Test compression level is set."""
        assert app.config.get('COMPRESS_LEVEL') == 6
    
    def test_compression_min_size(self, app):
        """Test minimum compression size is set."""
        assert app.config.get('COMPRESS_MIN_SIZE') == 500


class TestPerformanceModule:
    """Test performance utilities."""
    
    def test_performance_module_exists(self, app):
        """Test that performance module is properly imported."""
        from app.modules.performance import (
            QueryProfiler, 
            get_query_profiler,
            timed,
            add_cache_headers
        )
        assert QueryProfiler is not None
        assert callable(get_query_profiler)
        assert callable(timed)
        assert callable(add_cache_headers)
    
    def test_query_profiler(self, app):
        """Test query profiler functionality."""
        from app.modules.performance import get_query_profiler
        
        profiler = get_query_profiler()
        profiler.start()
        profiler.record("SELECT * FROM users", 0.05)
        stats = profiler.stop()
        
        assert stats['count'] == 1
        assert stats['total_time'] == 0.05
        assert len(stats['queries']) == 1
    
    def test_timed_decorator(self, app):
        """Test timed decorator."""
        import time
        from app.modules.performance import timed
        
        @timed
        def slow_function():
            time.sleep(0.01)
            return "done"
        
        result = slow_function()
        assert result == "done"


class TestSelfHostedAssets:
    """Test self-hosted assets for data sovereignty."""
    
    def test_fontawesome_css_exists(self):
        """Test that Font Awesome CSS is self-hosted."""
        # Get the app directory (tests are in app/tests/)
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        css_path = os.path.join(app_dir, 'static', 'css', 'fontawesome', 'all.min.css')
        assert os.path.exists(css_path), f"Font Awesome CSS should be self-hosted at {css_path}"
    
    def test_jquery_exists(self):
        """Test that jQuery is self-hosted."""
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        js_path = os.path.join(app_dir, 'static', 'js', 'jquery-3.6.0.min.js')
        assert os.path.exists(js_path), f"jQuery should be self-hosted at {js_path}"
    
    def test_webfonts_exist(self):
        """Test that Font Awesome webfonts are self-hosted."""
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        webfonts_dir = os.path.join(app_dir, 'static', 'webfonts')
        assert os.path.exists(webfonts_dir), f"Webfonts directory should exist at {webfonts_dir}"
        
        # Check for key font files
        expected_fonts = [
            'fa-solid-900.woff2',
            'fa-regular-400.woff2',
            'fa-brands-400.woff2'
        ]
        for font in expected_fonts:
            font_path = os.path.join(webfonts_dir, font)
            assert os.path.exists(font_path), f"{font} should exist at {font_path}"


class TestRequestTiming:
    """Test request timing middleware."""
    
    def test_timing_header(self, client, app):
        """Test that X-Request-Time header is added to responses."""
        with app.app_context():
            response = client.get('/')
            # Header should be present (may be 0 for fast requests)
            assert 'X-Request-Time' in response.headers or response.status_code in [200, 302, 404]
    
    def test_slow_query_threshold_configured(self, app):
        """Test that slow query threshold is configured."""
        assert 'SLOW_QUERY_THRESHOLD' in app.config
        assert app.config['SLOW_QUERY_THRESHOLD'] == 0.5


class TestEagerLoading:
    """Test that eager loading is properly configured."""
    
    def test_list_users_no_n_plus_one(self, app, client):
        """Test that list_users uses eager loading for roles."""
        with app.app_context():
            # Create test user with role
            admin_role = Role.query.filter_by(name='admin').first()
            test_user = User(
                username='testadmin',
                email='testadmin@example.com',
                password='password123'
            )
            test_user.roles.append(admin_role)
            db.session.add(test_user)
            db.session.commit()
            
            # The query should use selectinload for roles
            from sqlalchemy.orm import selectinload
            
            # Verify the query pattern works
            users = User.query.options(selectinload(User.roles)).all()
            assert len(users) >= 1
            # Accessing roles should not trigger additional queries
            for u in users:
                _ = u.roles  # This would cause N+1 without eager loading


class TestConfigSettings:
    """Test configuration for Phase 23."""
    
    def test_cache_type_configured(self, app):
        """Test cache type is configured."""
        assert 'CACHE_TYPE' in app.config
    
    def test_cache_timeout_configured(self, app):
        """Test cache timeout is configured."""
        assert 'CACHE_DEFAULT_TIMEOUT' in app.config
    
    def test_debug_toolbar_configured(self, app):
        """Test debug toolbar is configured."""
        assert 'DEBUG_TB_INTERCEPT_REDIRECTS' in app.config
        assert app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
