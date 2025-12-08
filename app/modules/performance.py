"""
Phase 23: Performance Optimization - Performance Utilities Module

Provides request timing, slow query logging, and query counting for N+1 detection.
"""

import time
import logging
from functools import wraps
from flask import g, request, current_app
from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class QueryProfiler:
    """Tracks SQL query count and duration for N+1 detection."""
    
    def __init__(self):
        self.queries = []
        self.enabled = False
    
    def start(self):
        """Start tracking queries."""
        self.queries = []
        self.enabled = True
    
    def stop(self):
        """Stop tracking and return summary."""
        self.enabled = False
        return {
            'count': len(self.queries),
            'total_time': sum(q['duration'] for q in self.queries),
            'queries': self.queries
        }
    
    def record(self, statement, duration):
        """Record a query execution."""
        if self.enabled:
            self.queries.append({
                'statement': statement[:200],  # Truncate for readability
                'duration': duration
            })


# Global query profiler instance
_query_profiler = QueryProfiler()


def get_query_profiler():
    """Get the global query profiler instance."""
    return _query_profiler


def setup_query_logging(app):
    """
    Set up SQLAlchemy event listeners for query logging.
    Only active in debug mode or when SLOW_QUERY_THRESHOLD is set.
    """
    
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        
        # Record in profiler if enabled
        _query_profiler.record(statement, total)
        
        # Log slow queries
        threshold = app.config.get('SLOW_QUERY_THRESHOLD', 0.5)
        if total > threshold:
            logger.warning(
                f"Slow query ({total:.3f}s): {statement[:100]}..."
            )


def init_request_timing(app):
    """
    Initialize request timing middleware.
    Records request start time and logs slow requests.
    """
    
    @app.before_request
    def start_timer():
        g.request_start_time = time.time()
        # Start query profiler in debug mode
        if app.debug:
            _query_profiler.start()
    
    @app.after_request
    def log_request_timing(response):
        if hasattr(g, 'request_start_time'):
            elapsed = time.time() - g.request_start_time
            
            # Add timing header
            response.headers['X-Request-Time'] = f'{elapsed:.3f}s'
            
            # Log slow requests (over 1 second)
            if elapsed > 1.0:
                logger.warning(
                    f"Slow request ({elapsed:.3f}s): {request.method} {request.path}"
                )
            
            # Log query count in debug mode
            if app.debug:
                stats = _query_profiler.stop()
                if stats['count'] > 10:  # Potential N+1
                    logger.warning(
                        f"High query count ({stats['count']}) for {request.path}"
                    )
        
        return response


def timed(func):
    """
    Decorator to time function execution.
    Logs execution time for functions taking longer than 100ms.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        
        if elapsed > 0.1:  # Log if over 100ms
            logger.info(f"{func.__name__} took {elapsed:.3f}s")
        
        return result
    return wrapper


def add_cache_headers(response, max_age=3600, public=True):
    """
    Add cache control headers to a response.
    
    Args:
        response: Flask response object
        max_age: Cache duration in seconds (default 1 hour)
        public: Whether cache is public or private
    """
    cache_type = 'public' if public else 'private'
    response.headers['Cache-Control'] = f'{cache_type}, max-age={max_age}'
    return response
