"""
Phase 25: Session Manager Module

Redis-backed session storage for horizontal scaling and high availability.
"""

import json
from datetime import timedelta
from typing import Optional
from uuid import uuid4

from flask import Flask
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict


class RedisSession(CallbackDict, SessionMixin):
    """A session implementation backed by Redis."""
    
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class RedisSessionInterface(SessionInterface):
    """
    Session interface that stores sessions in Redis.
    
    This allows for horizontal scaling as sessions are not stored
    in local memory.
    """
    
    serializer = json
    session_class = RedisSession
    
    def __init__(self, redis_client, prefix='session:', expire=timedelta(days=31)):
        """
        Initialize Redis session interface.
        
        Args:
            redis_client: Redis client instance
            prefix: Key prefix for session keys
            expire: Session expiration time
        """
        self.redis = redis_client
        self.prefix = prefix
        self.expire = expire
    
    def generate_sid(self):
        """Generate a new session ID."""
        return str(uuid4())
    
    def get_redis_key(self, sid):
        """Get the Redis key for a session ID."""
        return f"{self.prefix}{sid}"
    
    def open_session(self, app: Flask, request):
        """Open a session, loading from Redis if it exists."""
        sid = request.cookies.get(app.config.get('SESSION_COOKIE_NAME', 'session'))
        
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid, new=True)
        
        val = self.redis.get(self.get_redis_key(sid))
        
        if val is not None:
            try:
                data = self.serializer.loads(val)
                return self.session_class(data, sid=sid)
            except (ValueError, TypeError):
                pass
        
        return self.session_class(sid=sid, new=True)
    
    def save_session(self, app: Flask, session, response):
        """Save session to Redis and set cookie."""
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        
        if not session:
            if session.modified:
                self.redis.delete(self.get_redis_key(session.sid))
                response.delete_cookie(
                    app.config.get('SESSION_COOKIE_NAME', 'session'),
                    domain=domain,
                    path=path
                )
            return
        
        # Get expiration settings
        if isinstance(self.expire, timedelta):
            expire_seconds = int(self.expire.total_seconds())
        else:
            expire_seconds = self.expire
        
        # Serialize and save to Redis
        val = self.serializer.dumps(dict(session))
        self.redis.setex(
            self.get_redis_key(session.sid),
            expire_seconds,
            val
        )
        
        # Set cookie
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        samesite = self.get_cookie_samesite(app)
        
        response.set_cookie(
            app.config.get('SESSION_COOKIE_NAME', 'session'),
            session.sid,
            expires=self.get_expiration_time(app, session),
            httponly=httponly,
            domain=domain,
            path=path,
            secure=secure,
            samesite=samesite
        )


class SessionManager:
    """
    Manages session configuration and Redis connection.
    
    Usage:
        session_manager = SessionManager()
        session_manager.init_app(app)
    """
    
    def __init__(self, app=None):
        self.app = app
        self.redis = None
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize session manager with Flask app."""
        self.app = app
        
        redis_url = app.config.get('SESSION_REDIS_URL')
        
        if redis_url:
            try:
                import redis
                self.redis = redis.from_url(redis_url)
                
                # Configure session interface
                expire_days = app.config.get('SESSION_EXPIRE_DAYS', 31)
                prefix = app.config.get('SESSION_KEY_PREFIX', 'verso:session:')
                
                app.session_interface = RedisSessionInterface(
                    self.redis,
                    prefix=prefix,
                    expire=timedelta(days=expire_days)
                )
                
                app.logger.info("Redis session backend initialized")
            except ImportError:
                app.logger.warning("Redis not installed, using default sessions")
            except Exception as e:
                app.logger.error(f"Failed to connect to Redis: {e}")
    
    def clear_session(self, sid: str):
        """Clear a specific session by ID."""
        if self.redis:
            prefix = self.app.config.get('SESSION_KEY_PREFIX', 'verso:session:')
            self.redis.delete(f"{prefix}{sid}")
    
    def clear_user_sessions(self, user_id: int):
        """
        Clear all sessions for a specific user.
        
        Note: This requires storing user_id in session data.
        """
        if not self.redis:
            return
        
        prefix = self.app.config.get('SESSION_KEY_PREFIX', 'verso:session:')
        pattern = f"{prefix}*"
        
        for key in self.redis.scan_iter(match=pattern):
            try:
                data = self.redis.get(key)
                if data:
                    session_data = json.loads(data)
                    if session_data.get('_user_id') == user_id:
                        self.redis.delete(key)
            except (ValueError, TypeError):
                continue
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        if not self.redis:
            return 0
        
        prefix = self.app.config.get('SESSION_KEY_PREFIX', 'verso:session:')
        pattern = f"{prefix}*"
        
        count = 0
        for _ in self.redis.scan_iter(match=pattern):
            count += 1
        return count
    
    def is_redis_available(self) -> bool:
        """Check if Redis is available."""
        if not self.redis:
            return False
        try:
            self.redis.ping()
            return True
        except Exception:
            return False


# Global instance
session_manager = SessionManager()
