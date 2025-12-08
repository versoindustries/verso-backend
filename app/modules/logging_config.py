"""
Phase 24: Observability & Monitoring - Structured Logging Configuration

Provides:
- JSON structured logging with correlation IDs
- Request/response logging middleware
- Sensitive data masking
- Log level configuration
- Error context enrichment
"""

import logging
import json
import re
import uuid
import time
import traceback
from datetime import datetime, timezone
from functools import wraps
from flask import g, request, has_request_context


# ============================================================================
# Sensitive Data Patterns
# ============================================================================

SENSITIVE_PATTERNS = [
    # Passwords
    (re.compile(r'(["\']?password["\']?\s*[=:]\s*)["\']?[^"\'&\s]+["\']?', re.I), r'\1"[REDACTED]"'),
    (re.compile(r'(["\']?passwd["\']?\s*[=:]\s*)["\']?[^"\'&\s]+["\']?', re.I), r'\1"[REDACTED]"'),
    (re.compile(r'(["\']?pwd["\']?\s*[=:]\s*)["\']?[^"\'&\s]+["\']?', re.I), r'\1"[REDACTED]"'),
    # API keys and tokens
    (re.compile(r'(["\']?api[_-]?key["\']?\s*[=:]\s*)["\']?[^"\'&\s]+["\']?', re.I), r'\1"[REDACTED]"'),
    (re.compile(r'(["\']?token["\']?\s*[=:]\s*)["\']?[A-Za-z0-9_\-\.]+["\']?', re.I), r'\1"[REDACTED]"'),
    (re.compile(r'(["\']?secret["\']?\s*[=:]\s*)["\']?[^"\'&\s]+["\']?', re.I), r'\1"[REDACTED]"'),
    (re.compile(r'(["\']?auth["\']?\s*[=:]\s*)["\']?[^"\'&\s]+["\']?', re.I), r'\1"[REDACTED]"'),
    # Authorization header
    (re.compile(r'(Authorization:\s*)(Bearer\s+)?[A-Za-z0-9_\-\.]+', re.I), r'\1[REDACTED]'),
    # Credit card numbers (basic pattern)
    (re.compile(r'\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?)\d{4}\b'), r'\1****'),
    # SSN pattern
    (re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'), '[SSN-REDACTED]'),
    # Email addresses (partial redaction for privacy)
    (re.compile(r'([a-zA-Z0-9._%+-]{2})[a-zA-Z0-9._%+-]*(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'), r'\1***\2'),
]


def mask_sensitive_data(text):
    """
    Mask sensitive data in log messages.
    
    Args:
        text: String that may contain sensitive data
        
    Returns:
        String with sensitive data masked
    """
    if not isinstance(text, str):
        text = str(text)
    
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    
    return text


# ============================================================================
# JSON Formatter
# ============================================================================

class StructuredJsonFormatter(logging.Formatter):
    """
    JSON log formatter with structured output.
    
    Produces logs in format:
    {
        "timestamp": "2024-01-01T12:00:00.000000Z",
        "level": "INFO",
        "logger": "app.routes.auth",
        "message": "User logged in",
        "request_id": "abc-123",
        "request": { ... },  # if in request context
        "extra": { ... },    # any extra fields
        "exception": "..."   # if exception info present
    }
    """
    
    def __init__(self, include_request=True, mask_sensitive=True):
        super().__init__()
        self.include_request = include_request
        self.mask_sensitive = mask_sensitive
    
    def format(self, record):
        # Base log structure
        log_obj = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': self._mask(record.getMessage()),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add correlation/request ID if available
        request_id = getattr(record, 'request_id', None)
        if not request_id and has_request_context():
            request_id = getattr(g, 'request_id', None)
        if request_id:
            log_obj['request_id'] = request_id
        
        # Add request context if in request and enabled
        if self.include_request and has_request_context():
            log_obj['request'] = {
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
            }
            # Add user if authenticated
            try:
                from flask_login import current_user
                if current_user and current_user.is_authenticated:
                    log_obj['request']['user_id'] = current_user.id
            except:
                pass
        
        # Add any extra fields
        extra = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                          'message', 'request_id', 'taskName']:
                if not key.startswith('_'):
                    extra[key] = value
        
        if extra:
            log_obj['extra'] = extra
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self._mask(self.formatException(record.exc_info))
        
        return json.dumps(log_obj, default=str)
    
    def _mask(self, text):
        """Mask sensitive data if enabled."""
        if self.mask_sensitive:
            return mask_sensitive_data(text)
        return text


class ReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    Includes color coding for terminals that support it.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m',
    }
    
    def __init__(self, use_colors=True, mask_sensitive=True):
        super().__init__()
        self.use_colors = use_colors
        self.mask_sensitive = mask_sensitive
    
    def format(self, record):
        # Get request ID if available
        request_id = ''
        if has_request_context():
            rid = getattr(g, 'request_id', None)
            if rid:
                request_id = f'[{rid[:8]}] '
        
        # Build message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        
        if self.use_colors:
            color = self.COLORS.get(level, '')
            reset = self.COLORS['RESET']
            level_str = f'{color}{level:8s}{reset}'
        else:
            level_str = f'{level:8s}'
        
        message = mask_sensitive_data(record.getMessage()) if self.mask_sensitive else record.getMessage()
        
        base = f'{timestamp} {level_str} {request_id}{record.name}: {message}'
        
        # Add exception if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            if self.mask_sensitive:
                exc_text = mask_sensitive_data(exc_text)
            base = f'{base}\n{exc_text}'
        
        return base


# ============================================================================
# Correlation ID Middleware
# ============================================================================

def generate_request_id():
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def init_correlation_id(app):
    """
    Initialize correlation ID middleware.
    
    Sets up before_request and after_request hooks to:
    - Generate or accept X-Request-ID header
    - Store in flask.g for logging
    - Echo back in response headers
    """
    
    @app.before_request
    def set_request_id():
        # Accept from client or generate new
        g.request_id = request.headers.get('X-Request-ID') or generate_request_id()
        g.request_start_time = time.time()
    
    @app.after_request
    def add_request_id_header(response):
        # Echo request ID back to client
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        return response


# ============================================================================
# Request Logging Middleware
# ============================================================================

def init_request_logging(app, logger=None):
    """
    Initialize request/response logging middleware.
    
    Logs:
    - Request: method, path, user, IP
    - Response: status, duration
    - Errors: full context on 5xx responses
    """
    if logger is None:
        logger = logging.getLogger('http')
    
    @app.after_request
    def log_request(response):
        if hasattr(g, 'request_start_time'):
            duration = time.time() - g.request_start_time
        else:
            duration = 0
        
        # Skip logging static files and health checks
        if request.path.startswith('/static') or request.path in ['/health', '/ready', '/live']:
            return response
        
        # Build log message
        status = response.status_code
        method = request.method
        path = request.path
        
        # Get user info if available
        user_id = None
        try:
            from flask_login import current_user
            if current_user and current_user.is_authenticated:
                user_id = current_user.id
        except:
            pass
        
        log_data = {
            'method': method,
            'path': path,
            'status': status,
            'duration_ms': round(duration * 1000, 2),
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string[:100] if request.user_agent else None,
        }
        
        if user_id:
            log_data['user_id'] = user_id
        
        # Log at appropriate level
        if status >= 500:
            logger.error(f'{method} {path} {status}', extra=log_data)
        elif status >= 400:
            logger.warning(f'{method} {path} {status}', extra=log_data)
        else:
            logger.info(f'{method} {path} {status}', extra=log_data)
        
        return response


# ============================================================================
# Logger Configuration
# ============================================================================

def setup_structured_logging(app, log_format='auto', log_level=None):
    """
    Configure structured logging for the Flask application.
    
    Args:
        app: Flask application instance
        log_format: 'json', 'text', or 'auto' (json in production)
        log_level: Logging level (default: DEBUG in debug mode, INFO otherwise)
    """
    import os
    
    # Determine log format
    if log_format == 'auto':
        log_format = os.environ.get('LOG_FORMAT', 'text' if app.debug else 'json')
    
    # Determine log level
    if log_level is None:
        log_level = os.environ.get('LOG_LEVEL', 'DEBUG' if app.debug else 'INFO')
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create handler
    handler = logging.StreamHandler()
    
    if log_format == 'json':
        handler.setFormatter(StructuredJsonFormatter(
            include_request=True,
            mask_sensitive=True
        ))
    else:
        handler.setFormatter(ReadableFormatter(
            use_colors=True,
            mask_sensitive=True
        ))
    
    handler.setLevel(level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers = []
    root_logger.addHandler(handler)
    
    # Configure Flask app logger
    app.logger.handlers = []
    app.logger.addHandler(handler)
    app.logger.setLevel(level)
    
    # Configure common loggers
    for logger_name in ['werkzeug', 'sqlalchemy.engine', 'http', 'worker']:
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.addHandler(handler)
        logger.setLevel(level)
    
    # Reduce SQLAlchemy noise unless debugging
    if log_level != 'DEBUG':
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    app.logger.info(f'Logging configured: format={log_format}, level={log_level}')


# ============================================================================
# Logging Context Manager
# ============================================================================

class LogContext:
    """
    Context manager for adding extra fields to log records.
    
    Usage:
        with LogContext(user_id=123, order_id=456):
            logger.info("Processing order")  # Will include user_id and order_id
    """
    
    def __init__(self, **kwargs):
        self.extra = kwargs
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        extra = self.extra
        def factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in extra.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(factory)
        return self
    
    def __exit__(self, *args):
        logging.setLogRecordFactory(self.old_factory)


def log_with_context(logger, level, message, **extra):
    """
    Log a message with extra context fields.
    
    Args:
        logger: Logger instance
        level: Log level (e.g., 'info', 'error')
        message: Log message
        **extra: Additional fields to include
    """
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra=extra)


# ============================================================================
# Error Logging Helpers
# ============================================================================

def log_exception(logger, message, exc_info=True, **extra):
    """
    Log an exception with full context.
    
    Args:
        logger: Logger instance
        message: Error message
        exc_info: Include traceback (default True)
        **extra: Additional context fields
    """
    # Add request context if available
    if has_request_context():
        extra.setdefault('request_method', request.method)
        extra.setdefault('request_path', request.path)
        extra.setdefault('request_ip', request.remote_addr)
        
        # Add safe request data (no passwords)
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                form_data = dict(request.form)
                # Remove known sensitive fields
                for key in ['password', 'password_confirm', 'current_password', 'token']:
                    form_data.pop(key, None)
                extra['request_form'] = form_data
            except:
                pass
    
    logger.error(message, exc_info=exc_info, extra=extra)
