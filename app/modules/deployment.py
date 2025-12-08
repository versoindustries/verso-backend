"""
Phase 25: Deployment Utilities Module

Provides feature flags, deployment management, and blue-green deployment support.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from functools import wraps

from flask import current_app, g, request


class FeatureFlagManager:
    """
    Manage feature flags for gradual rollout and A/B testing.
    
    Usage:
        feature_flags = FeatureFlagManager()
        
        if feature_flags.is_enabled('new_checkout', user_id=current_user.id):
            # Show new checkout
        else:
            # Show old checkout
    """
    
    def __init__(self, app=None):
        self.app = app
        self._cache = {}
        self._cache_ttl = 60  # seconds
        self._last_cache_update = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        self._cache_ttl = app.config.get('FEATURE_FLAG_CACHE_TTL', 60)
    
    def _refresh_cache(self):
        """Refresh feature flag cache from database."""
        from app.models import FeatureFlag
        
        now = datetime.utcnow()
        if (self._last_cache_update and 
            (now - self._last_cache_update).seconds < self._cache_ttl):
            return
        
        flags = FeatureFlag.query.all()
        self._cache = {flag.name: flag for flag in flags}
        self._last_cache_update = now
    
    def is_enabled(self, flag_name: str, user_id: Optional[int] = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            user_id: Optional user ID for per-user rollout
        
        Returns:
            True if feature is enabled for this context
        """
        self._refresh_cache()
        
        flag = self._cache.get(flag_name)
        if not flag:
            return False
        
        if user_id:
            return flag.is_active_for_user(user_id)
        
        return flag.is_enabled
    
    def get_flag(self, flag_name: str) -> Optional[Dict[str, Any]]:
        """Get feature flag details."""
        self._refresh_cache()
        
        flag = self._cache.get(flag_name)
        if not flag:
            return None
        
        return {
            'name': flag.name,
            'description': flag.description,
            'is_enabled': flag.is_enabled,
            'rollout_percentage': flag.rollout_percentage,
            'starts_at': flag.starts_at.isoformat() if flag.starts_at else None,
            'ends_at': flag.ends_at.isoformat() if flag.ends_at else None,
        }
    
    def set_flag(self, flag_name: str, enabled: bool, 
                 rollout_percentage: int = 100,
                 description: str = None) -> bool:
        """
        Create or update a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            enabled: Whether the flag is enabled
            rollout_percentage: Percentage of users to enable for (0-100)
            description: Optional description
        
        Returns:
            True if successful
        """
        from app.models import FeatureFlag
        from app.database import db
        
        flag = FeatureFlag.query.filter_by(name=flag_name).first()
        
        if not flag:
            flag = FeatureFlag(name=flag_name)
            db.session.add(flag)
        
        flag.is_enabled = enabled
        flag.rollout_percentage = min(100, max(0, rollout_percentage))
        if description:
            flag.description = description
        
        db.session.commit()
        
        # Invalidate cache
        self._last_cache_update = None
        
        return True
    
    def delete_flag(self, flag_name: str) -> bool:
        """Delete a feature flag."""
        from app.models import FeatureFlag
        from app.database import db
        
        flag = FeatureFlag.query.filter_by(name=flag_name).first()
        if flag:
            db.session.delete(flag)
            db.session.commit()
            self._last_cache_update = None
            return True
        return False
    
    def list_flags(self) -> List[Dict[str, Any]]:
        """List all feature flags."""
        from app.models import FeatureFlag
        
        flags = FeatureFlag.query.order_by(FeatureFlag.name).all()
        return [self.get_flag(flag.name) for flag in flags]
    
    def invalidate_cache(self):
        """Force cache invalidation."""
        self._last_cache_update = None
        self._cache = {}


def feature_flag_required(flag_name: str, fallback_view=None):
    """
    Decorator to require a feature flag for a route.
    
    Usage:
        @app.route('/new-feature')
        @feature_flag_required('new_feature')
        def new_feature():
            return 'New feature page'
    
    Args:
        flag_name: Name of the required feature flag
        fallback_view: Optional fallback function if flag is disabled
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = getattr(g, 'user_id', None)
            if hasattr(g, 'current_user') and g.current_user:
                user_id = g.current_user.id
            
            if feature_flags.is_enabled(flag_name, user_id=user_id):
                return f(*args, **kwargs)
            
            if fallback_view:
                return fallback_view(*args, **kwargs)
            
            from flask import abort
            abort(404)
        
        return decorated_function
    return decorator


class DeploymentManager:
    """
    Manage deployments and track deployment history.
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
    
    def log_deployment(self, version: str, environment: str, 
                       user_id: int = None, notes: str = None,
                       commit_sha: str = None) -> int:
        """
        Log a deployment event.
        
        Returns:
            Deployment log ID
        """
        from app.models import DeploymentLog
        from app.database import db
        
        # Get previous successful deployment for rollback reference
        previous = DeploymentLog.query.filter_by(
            environment=environment,
            status='success'
        ).order_by(DeploymentLog.started_at.desc()).first()
        
        deployment = DeploymentLog(
            version=version,
            environment=environment,
            deployed_by_id=user_id,
            notes=notes,
            commit_sha=commit_sha,
            rollback_version=previous.version if previous else None,
        )
        db.session.add(deployment)
        db.session.commit()
        
        return deployment.id
    
    def complete_deployment(self, deployment_id: int, success: bool = True,
                           migration_ran: bool = False) -> bool:
        """Mark a deployment as complete."""
        from app.models import DeploymentLog
        from app.database import db
        
        deployment = DeploymentLog.query.get(deployment_id)
        if not deployment:
            return False
        
        deployment.completed_at = datetime.utcnow()
        deployment.status = 'success' if success else 'failed'
        deployment.migration_ran = migration_ran
        
        db.session.commit()
        return True
    
    def rollback(self, environment: str, user_id: int = None) -> Optional[str]:
        """
        Initiate a rollback to the previous version.
        
        Returns:
            Version rolled back to, or None if no rollback available
        """
        from app.models import DeploymentLog
        from app.database import db
        
        # Get current deployment
        current = DeploymentLog.query.filter_by(
            environment=environment,
            status='success'
        ).order_by(DeploymentLog.started_at.desc()).first()
        
        if not current or not current.rollback_version:
            return None
        
        # Mark current as rolled back
        current.status = 'rolled_back'
        
        # Log rollback as new deployment
        rollback_deployment = DeploymentLog(
            version=current.rollback_version,
            environment=environment,
            deployed_by_id=user_id,
            notes=f"Rollback from {current.version}",
            status='success',
            completed_at=datetime.utcnow(),
        )
        db.session.add(rollback_deployment)
        db.session.commit()
        
        return current.rollback_version
    
    def get_deployment_history(self, environment: str = None, 
                               limit: int = 20) -> List[Dict[str, Any]]:
        """Get deployment history."""
        from app.models import DeploymentLog
        
        query = DeploymentLog.query.order_by(DeploymentLog.started_at.desc())
        if environment:
            query = query.filter_by(environment=environment)
        
        deployments = query.limit(limit).all()
        
        return [{
            'id': d.id,
            'version': d.version,
            'environment': d.environment,
            'status': d.status,
            'started_at': d.started_at.isoformat() if d.started_at else None,
            'completed_at': d.completed_at.isoformat() if d.completed_at else None,
            'deployed_by': d.deployed_by.username if d.deployed_by else None,
            'notes': d.notes,
            'commit_sha': d.commit_sha,
            'rollback_version': d.rollback_version,
            'migration_ran': d.migration_ran,
        } for d in deployments]
    
    def get_current_version(self, environment: str = 'production') -> Optional[str]:
        """Get current deployed version for an environment."""
        from app.models import DeploymentLog
        
        deployment = DeploymentLog.query.filter_by(
            environment=environment,
            status='success'
        ).order_by(DeploymentLog.started_at.desc()).first()
        
        return deployment.version if deployment else None


class HealthChecker:
    """
    Enhanced health check utilities for deployment verification.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.checks = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
    
    def register_check(self, name: str, check_func):
        """
        Register a health check function.
        
        Args:
            name: Name of the check
            check_func: Function that returns (success: bool, message: str)
        """
        self.checks[name] = check_func
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {
            'status': 'healthy',
            'checks': {},
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        all_passed = True
        
        for name, check_func in self.checks.items():
            try:
                success, message = check_func()
                results['checks'][name] = {
                    'status': 'pass' if success else 'fail',
                    'message': message,
                }
                if not success:
                    all_passed = False
            except Exception as e:
                results['checks'][name] = {
                    'status': 'error',
                    'message': str(e),
                }
                all_passed = False
        
        results['status'] = 'healthy' if all_passed else 'unhealthy'
        return results
    
    def check_database(self) -> tuple:
        """Check database connectivity."""
        from app.database import db
        try:
            db.session.execute(db.text('SELECT 1'))
            return True, 'Database connection OK'
        except Exception as e:
            return False, f'Database error: {str(e)}'
    
    def check_memory(self) -> tuple:
        """Check available system memory."""
        try:
            import os
            # Get memory info from /proc/meminfo on Linux
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    lines = f.readlines()
                    mem_info = {}
                    for line in lines:
                        parts = line.split(':')
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value = parts[1].strip().split()[0]
                            mem_info[key] = int(value)
                    
                    total_kb = mem_info.get('MemTotal', 0)
                    available_kb = mem_info.get('MemAvailable', mem_info.get('MemFree', 0))
                    available_mb = available_kb / 1024
                    
                    if available_mb > 256:  # More than 256MB available
                        return True, f'Memory OK: {available_mb:.0f} MB available'
                    return False, f'Low memory: {available_mb:.0f} MB available'
            return True, 'Memory check not available on this platform'
        except Exception as e:
            return False, f'Memory check error: {str(e)}'
    
    def check_disk_space(self, min_gb: float = 1.0) -> tuple:
        """Check available disk space."""
        import shutil
        total, used, free = shutil.disk_usage('/')
        free_gb = free / (1024 ** 3)
        if free_gb >= min_gb:
            return True, f'Disk space: {free_gb:.2f} GB free'
        return False, f'Low disk space: {free_gb:.2f} GB free (min: {min_gb} GB)'


# Global instances
feature_flags = FeatureFlagManager()
deployment_manager = DeploymentManager()
health_checker = HealthChecker()
