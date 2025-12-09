"""
Phase 28: Security Module

Comprehensive security features including rate limiting, account lockout,
IP blacklisting, and security headers.
"""

import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from functools import wraps

from flask import Flask, request, g, current_app, abort
from werkzeug.security import generate_password_hash, check_password_hash


class RateLimiter:
    """
    Rate limiting using Flask-Limiter or in-memory fallback.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.limiter = None
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize rate limiter with Flask app."""
        self.app = app
        
        try:
            from flask_limiter import Limiter
            from flask_limiter.util import get_remote_address
            
            # Configure limiter
            storage_uri = app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
            
            self.limiter = Limiter(
                app=app,
                key_func=get_remote_address,
                default_limits=["1000 per day", "200 per hour"],
                storage_uri=storage_uri,
            )
            
            app.logger.info("Rate limiter initialized")
            
        except ImportError:
            app.logger.warning("Flask-Limiter not installed, rate limiting disabled")
    
    def limit(self, limit_string: str):
        """
        Decorator to apply rate limit to a route.
        
        Usage:
            @rate_limiter.limit("5 per minute")
            def login():
                ...
        """
        if self.limiter:
            return self.limiter.limit(limit_string)
        else:
            # No-op decorator
            def decorator(f):
                return f
            return decorator
    
    def exempt(self, f):
        """Exempt a route from rate limiting."""
        if self.limiter:
            return self.limiter.exempt(f)
        return f


class LoginTracker:
    """
    Track login attempts for security monitoring and account lockout.
    """
    
    # Default lockout settings
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    TRACKING_WINDOW_MINUTES = 30
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
        self.MAX_FAILED_ATTEMPTS = app.config.get('MAX_FAILED_LOGIN_ATTEMPTS', 5)
        self.LOCKOUT_DURATION_MINUTES = app.config.get('ACCOUNT_LOCKOUT_MINUTES', 15)
        self.TRACKING_WINDOW_MINUTES = app.config.get('LOGIN_TRACKING_WINDOW_MINUTES', 30)
    
    def log_attempt(self, email: str, success: bool, 
                    user_id: int = None, failure_reason: str = None) -> None:
        """Log a login attempt."""
        from app.models import LoginAttempt
        from app.database import db
        
        attempt = LoginAttempt(
            email=email.lower(),
            ip_address=self._get_client_ip(),
            user_agent=request.headers.get('User-Agent', '')[:255],
            success=success,
            failure_reason=failure_reason,
            user_id=user_id,
        )
        db.session.add(attempt)
        db.session.commit()
        
        # Check if we need to auto-block the IP
        if not success:
            self._check_auto_block(email)
    
    def is_locked_out(self, email: str) -> Tuple[bool, Optional[datetime]]:
        """
        Check if an account is locked out due to failed attempts.
        
        Returns:
            Tuple of (is_locked, lockout_expires_at)
        """
        from app.models import LoginAttempt
        
        window_start = datetime.utcnow() - timedelta(minutes=self.TRACKING_WINDOW_MINUTES)
        
        failed_attempts = LoginAttempt.query.filter(
            LoginAttempt.email == email.lower(),
            LoginAttempt.success == False,
            LoginAttempt.created_at >= window_start
        ).count()
        
        if failed_attempts >= self.MAX_FAILED_ATTEMPTS:
            # Calculate when lockout expires
            last_attempt = LoginAttempt.query.filter(
                LoginAttempt.email == email.lower(),
                LoginAttempt.success == False,
            ).order_by(LoginAttempt.created_at.desc()).first()
            
            if last_attempt:
                lockout_expires = last_attempt.created_at + timedelta(
                    minutes=self.LOCKOUT_DURATION_MINUTES
                )
                if datetime.utcnow() < lockout_expires:
                    return True, lockout_expires
        
        return False, None
    
    def is_ip_blocked(self, ip: str = None) -> bool:
        """Check if an IP address is blacklisted."""
        from app.models import IPBlacklist
        
        ip = ip or self._get_client_ip()
        
        block = IPBlacklist.query.filter_by(ip_address=ip).first()
        if block and block.is_active():
            return True
        
        return False
    
    def get_recent_attempts(self, email: str = None, 
                           limit: int = 20) -> List[dict]:
        """Get recent login attempts."""
        from app.models import LoginAttempt
        
        query = LoginAttempt.query.order_by(LoginAttempt.created_at.desc())
        
        if email:
            query = query.filter(LoginAttempt.email == email.lower())
        
        attempts = query.limit(limit).all()
        
        return [{
            'id': a.id,
            'email': a.email,
            'ip_address': a.ip_address,
            'success': a.success,
            'failure_reason': a.failure_reason,
            'created_at': a.created_at.isoformat(),
        } for a in attempts]
    
    def clear_lockout(self, email: str) -> None:
        """Clear lockout for an email address."""
        from app.models import LoginAttempt
        from app.database import db
        
        # Delete recent failed attempts
        window_start = datetime.utcnow() - timedelta(minutes=self.TRACKING_WINDOW_MINUTES)
        
        LoginAttempt.query.filter(
            LoginAttempt.email == email.lower(),
            LoginAttempt.success == False,
            LoginAttempt.created_at >= window_start
        ).delete()
        
        db.session.commit()
    
    def _check_auto_block(self, email: str) -> None:
        """Check if IP should be auto-blocked."""
        from app.models import LoginAttempt, IPBlacklist
        from app.database import db
        
        ip = self._get_client_ip()
        window_start = datetime.utcnow() - timedelta(hours=1)
        
        # Count failed attempts from this IP across all accounts
        ip_failed_attempts = LoginAttempt.query.filter(
            LoginAttempt.ip_address == ip,
            LoginAttempt.success == False,
            LoginAttempt.created_at >= window_start
        ).count()
        
        # Auto-block if too many failed attempts from same IP
        if ip_failed_attempts >= self.MAX_FAILED_ATTEMPTS * 3:
            existing = IPBlacklist.query.filter_by(ip_address=ip).first()
            if not existing:
                block = IPBlacklist(
                    ip_address=ip,
                    reason=f"Auto-blocked: {ip_failed_attempts} failed login attempts",
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    auto_blocked=True,
                    failed_attempts=ip_failed_attempts,
                )
                db.session.add(block)
                db.session.commit()
    
    def _get_client_ip(self) -> str:
        """Get client IP address, respecting X-Forwarded-For."""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return request.remote_addr or '0.0.0.0'


class IPBlacklistManager:
    """Manage IP blacklist."""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
    
    def block_ip(self, ip: str, reason: str = None, 
                 expires_hours: int = None, user_id: int = None) -> bool:
        """Block an IP address."""
        from app.models import IPBlacklist
        from app.database import db
        
        existing = IPBlacklist.query.filter_by(ip_address=ip).first()
        if existing:
            existing.reason = reason or existing.reason
            if expires_hours:
                existing.expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            existing.blocked_by_id = user_id
        else:
            block = IPBlacklist(
                ip_address=ip,
                reason=reason,
                expires_at=datetime.utcnow() + timedelta(hours=expires_hours) if expires_hours else None,
                blocked_by_id=user_id,
                auto_blocked=False,
            )
            db.session.add(block)
        
        db.session.commit()
        return True
    
    def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address."""
        from app.models import IPBlacklist
        from app.database import db
        
        block = IPBlacklist.query.filter_by(ip_address=ip).first()
        if block:
            db.session.delete(block)
            db.session.commit()
            return True
        return False
    
    def list_blocked_ips(self, include_expired: bool = False) -> List[dict]:
        """List all blocked IP addresses."""
        from app.models import IPBlacklist
        
        query = IPBlacklist.query.order_by(IPBlacklist.blocked_at.desc())
        
        if not include_expired:
            query = query.filter(
                db.or_(
                    IPBlacklist.expires_at.is_(None),
                    IPBlacklist.expires_at > datetime.utcnow()
                )
            )
        
        blocks = query.all()
        
        return [{
            'id': b.id,
            'ip_address': b.ip_address,
            'reason': b.reason,
            'blocked_at': b.blocked_at.isoformat(),
            'expires_at': b.expires_at.isoformat() if b.expires_at else None,
            'auto_blocked': b.auto_blocked,
            'is_active': b.is_active(),
        } for b in blocks]
    
    def cleanup_expired(self) -> int:
        """Remove expired blocks."""
        from app.models import IPBlacklist
        from app.database import db
        
        deleted = IPBlacklist.query.filter(
            IPBlacklist.expires_at.isnot(None),
            IPBlacklist.expires_at < datetime.utcnow()
        ).delete()
        
        db.session.commit()
        return deleted


class PasswordValidator:
    """
    Password validation with complexity requirements and breach checking.
    """
    
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
        self.MIN_LENGTH = app.config.get('PASSWORD_MIN_LENGTH', 8)
        self.REQUIRE_UPPERCASE = app.config.get('PASSWORD_REQUIRE_UPPERCASE', True)
        self.REQUIRE_LOWERCASE = app.config.get('PASSWORD_REQUIRE_LOWERCASE', True)
        self.REQUIRE_DIGIT = app.config.get('PASSWORD_REQUIRE_DIGIT', True)
        self.REQUIRE_SPECIAL = app.config.get('PASSWORD_REQUIRE_SPECIAL', True)
    
    def validate(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password against complexity requirements.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < self.MIN_LENGTH:
            errors.append(f"Password must be at least {self.MIN_LENGTH} characters")
        
        if self.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.REQUIRE_DIGIT and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.REQUIRE_SPECIAL and not any(c in self.SPECIAL_CHARS for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def check_breach(self, password: str) -> bool:
        """
        Check if password has been exposed in data breaches using HaveIBeenPwned.
        
        Returns:
            True if password is breached, False if safe
        """
        try:
            import requests
            
            # Hash the password with SHA-1
            sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]
            
            # Query the HIBP API (k-anonymity model)
            response = requests.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                timeout=5
            )
            
            if response.status_code == 200:
                # Check if our suffix is in the response
                for line in response.text.splitlines():
                    if line.split(':')[0] == suffix:
                        return True
            
            return False
            
        except Exception:
            # If check fails, don't block the user
            return False
    
    def is_password_reused(self, user_id: int, password: str, 
                          history_count: int = 5) -> bool:
        """Check if password was recently used."""
        from app.models import PasswordHistory
        
        recent_passwords = PasswordHistory.query.filter_by(
            user_id=user_id
        ).order_by(PasswordHistory.created_at.desc()).limit(history_count).all()
        
        for history in recent_passwords:
            if check_password_hash(history.password_hash, password):
                return True
        
        return False
    
    def save_password_history(self, user_id: int, password_hash: str) -> None:
        """Save password to history."""
        from app.models import PasswordHistory
        from app.database import db
        
        history = PasswordHistory(
            user_id=user_id,
            password_hash=password_hash,
        )
        db.session.add(history)
        db.session.commit()
    
    def get_strength_score(self, password: str) -> int:
        """
        Calculate password strength score (0-100).
        """
        score = 0
        
        # Length scoring
        length = len(password)
        if length >= 8:
            score += 20
        if length >= 12:
            score += 10
        if length >= 16:
            score += 10
        
        # Character variety
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            score += 15
        
        # Pattern penalties
        if re.search(r'(.)\1{2,}', password):  # Repeated characters
            score -= 10
        if re.search(r'(012|123|234|345|456|567|678|789)', password):  # Sequential numbers
            score -= 10
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):  # Sequential letters
            score -= 10
        
        return max(0, min(100, score))


def ip_check_required(f):
    """
    Decorator to check if IP is blacklisted before allowing access.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip:
            ip = ip.split(',')[0].strip()
        
        if login_tracker.is_ip_blocked(ip):
            abort(403, description="Access denied")
        
        return f(*args, **kwargs)
    return decorated_function


# Global instances
rate_limiter = RateLimiter()
login_tracker = LoginTracker()
ip_blacklist = IPBlacklistManager()
password_validator = PasswordValidator()
