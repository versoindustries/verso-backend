"""
Phase 28: Security Headers Module

Implements OWASP-recommended security headers including CSP, HSTS, and more.
"""

from flask import Flask, Response


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    
    Implements OWASP-recommended security headers:
    - Content-Security-Policy
    - Strict-Transport-Security
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """
    
    def __init__(self, app=None):
        self.app = app
        self.headers = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize security headers with Flask app."""
        self.app = app
        
        # Build CSP
        csp = self._build_csp(app)
        
        # Configure headers based on environment
        is_production = app.config.get('ENV') == 'production'
        
        self.headers = {
            # Content Security Policy
            'Content-Security-Policy': csp,
            
            # HTTP Strict Transport Security
            # Only enable in production with HTTPS
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains' if is_production else None,
            
            # Prevent clickjacking
            'X-Frame-Options': app.config.get('X_FRAME_OPTIONS', 'SAMEORIGIN'),
            
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # XSS Protection (legacy, but still useful)
            'X-XSS-Protection': '1; mode=block',
            
            # Referrer Policy
            'Referrer-Policy': app.config.get('REFERRER_POLICY', 'strict-origin-when-cross-origin'),
            
            # Permissions Policy (replaces Feature-Policy)
            'Permissions-Policy': self._build_permissions_policy(app),
            
            # Cross-Origin Policies
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Embedder-Policy': app.config.get('COEP', 'require-corp') if is_production else None,
            
            # Cache Control for sensitive pages
            # Individual routes can override this
            'Cache-Control': 'no-store, no-cache, must-revalidate, private',
        }
        
        # Register after_request handler
        app.after_request(self._add_security_headers)
    
    def _build_csp(self, app: Flask) -> str:
        """Build Content-Security-Policy header."""
        # Get custom CSP directives from config
        custom_csp = app.config.get('CSP_DIRECTIVES', {})
        
        # Default CSP directives
        default_directives = {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust based on needs
            'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
            'img-src': "'self' data: blob: https:",
            'font-src': "'self' data: https://fonts.gstatic.com",
            'connect-src': "'self'",
            'frame-src': "'self'",
            'object-src': "'none'",
            'base-uri': "'self'",
            'form-action': "'self'",
            'frame-ancestors': "'self'",
            'upgrade-insecure-requests': '',
        }
        
        # Merge with custom directives
        directives = {**default_directives, **custom_csp}
        
        # Build CSP string
        csp_parts = []
        for directive, value in directives.items():
            if value:
                csp_parts.append(f"{directive} {value}")
            else:
                csp_parts.append(directive)
        
        return '; '.join(csp_parts)
    
    def _build_permissions_policy(self, app: Flask) -> str:
        """Build Permissions-Policy header."""
        # Get custom permissions from config
        custom_permissions = app.config.get('PERMISSIONS_POLICY', {})
        
        # Default restrictive permissions
        default_permissions = {
            'accelerometer': '()',
            'camera': '()',
            'geolocation': '()',
            'gyroscope': '()',
            'magnetometer': '()',
            'microphone': '()',
            'payment': '()',
            'usb': '()',
            'fullscreen': '(self)',
            'autoplay': '(self)',
        }
        
        # Merge with custom permissions
        permissions = {**default_permissions, **custom_permissions}
        
        # Build string
        return ', '.join(f"{k}={v}" for k, v in permissions.items())
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        for header, value in self.headers.items():
            if value and header not in response.headers:
                response.headers[header] = value
        
        return response
    
    def add_nonce(self, response: Response, nonce: str) -> Response:
        """
        Add a nonce to CSP for inline scripts.
        
        Usage:
            nonce = secrets.token_urlsafe(16)
            g.csp_nonce = nonce
            # In template: <script nonce="{{ g.csp_nonce }}">...</script>
        """
        if 'Content-Security-Policy' in response.headers:
            csp = response.headers['Content-Security-Policy']
            # Replace 'unsafe-inline' with nonce
            csp = csp.replace("'unsafe-inline'", f"'nonce-{nonce}'")
            response.headers['Content-Security-Policy'] = csp
        
        return response


class CORSManager:
    """
    Manage Cross-Origin Resource Sharing (CORS) headers.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.allowed_origins = []
        self.allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        self.allowed_headers = ['Content-Type', 'Authorization', 'X-Requested-With']
        self.expose_headers = []
        self.max_age = 86400
        self.credentials = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize CORS with Flask app."""
        self.app = app
        
        # Load configuration
        self.allowed_origins = app.config.get('CORS_ORIGINS', ['*'])
        self.allowed_methods = app.config.get('CORS_METHODS', self.allowed_methods)
        self.allowed_headers = app.config.get('CORS_HEADERS', self.allowed_headers)
        self.expose_headers = app.config.get('CORS_EXPOSE_HEADERS', [])
        self.max_age = app.config.get('CORS_MAX_AGE', 86400)
        self.credentials = app.config.get('CORS_CREDENTIALS', False)
        
        # Register handlers
        app.after_request(self._add_cors_headers)
    
    def _add_cors_headers(self, response: Response) -> Response:
        """Add CORS headers to response."""
        from flask import request
        
        origin = request.headers.get('Origin')
        
        if not origin:
            return response
        
        # Check if origin is allowed
        if '*' in self.allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin if self.credentials else '*'
        elif origin in self.allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            return response
        
        # Add other CORS headers
        response.headers['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
        
        if self.expose_headers:
            response.headers['Access-Control-Expose-Headers'] = ', '.join(self.expose_headers)
        
        response.headers['Access-Control-Max-Age'] = str(self.max_age)
        
        if self.credentials:
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response


class CookieSecurityManager:
    """
    Manage secure cookie settings.
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Configure secure cookie settings."""
        is_production = app.config.get('ENV') == 'production'
        
        # Session cookie settings
        app.config.setdefault('SESSION_COOKIE_SECURE', is_production)
        app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
        app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
        
        # Use __Host- prefix in production for extra security
        if is_production and app.config.get('USE_HOST_COOKIE_PREFIX', False):
            app.config['SESSION_COOKIE_NAME'] = '__Host-session'
        
        # Remember me cookie settings
        app.config.setdefault('REMEMBER_COOKIE_SECURE', is_production)
        app.config.setdefault('REMEMBER_COOKIE_HTTPONLY', True)
        app.config.setdefault('REMEMBER_COOKIE_SAMESITE', 'Lax')


def validate_environment_secrets(app: Flask) -> list:
    """
    Validate that required secrets are properly configured.
    
    Returns:
        List of warnings/errors
    """
    warnings = []
    
    # Check SECRET_KEY
    secret_key = app.config.get('SECRET_KEY', '')
    if not secret_key or secret_key == 'dev' or len(secret_key) < 24:
        warnings.append("SECRET_KEY should be at least 24 characters and random")
    
    # Check for default/dev values
    dangerous_values = ['dev', 'development', 'test', 'password', '12345']
    
    for key in ['SECRET_KEY', 'SECURITY_PASSWORD_SALT']:
        value = app.config.get(key, '')
        if value.lower() in dangerous_values:
            warnings.append(f"{key} appears to be using a default/dev value")
    
    # Check database URL
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'sqlite' in db_url and app.config.get('ENV') == 'production':
        warnings.append("Using SQLite in production is not recommended")
    
    # Check for hardcoded credentials in database URL
    if '@' in db_url and ':' in db_url:
        if 'password' in db_url.lower() or 'admin' in db_url.lower():
            warnings.append("Database URL may contain hardcoded credentials")
    
    return warnings


# Global instances
security_headers = SecurityHeadersMiddleware()
cors_manager = CORSManager()
cookie_security = CookieSecurityManager()
