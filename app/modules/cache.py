"""
Phase 23: Performance Optimization - Caching Module

Provides caching utilities for business config, query results, and template fragments.
"""

import logging
from functools import wraps
from flask import current_app
from flask_caching import Cache

logger = logging.getLogger(__name__)

# Initialize cache instance (configured in app factory)
cache = Cache()


def init_cache(app):
    """Initialize the cache with app configuration."""
    cache.init_app(app)
    logger.info(f"Cache initialized with type: {app.config.get('CACHE_TYPE', 'SimpleCache')}")


def cached_business_config():
    """
    Get cached business configuration.
    Caches for 60 seconds to reduce database queries.
    
    Returns:
        dict: Business configuration key-value pairs
    """
    from app.models import BusinessConfig
    
    @cache.memoize(timeout=60)
    def _get_config():
        try:
            configs = BusinessConfig.query.all()
            return {c.setting_name: c.setting_value for c in configs}
        except Exception as e:
            logger.error(f"Error fetching business config: {e}")
            return {}
    
    return _get_config()


def invalidate_business_config():
    """Invalidate the cached business configuration."""
    cache.delete_memoized(cached_business_config)
    logger.info("Business config cache invalidated")


def cache_warmup():
    """
    Warm up critical caches on application startup.
    Called after app initialization.
    """
    try:
        # Pre-cache business config
        config = cached_business_config()
        logger.info(f"Cache warmup complete: {len(config)} config items cached")
    except Exception as e:
        logger.warning(f"Cache warmup failed: {e}")


def cached_query(timeout=300, key_prefix='query'):
    """
    Decorator for caching query results.
    
    Args:
        timeout: Cache timeout in seconds (default 5 minutes)
        key_prefix: Prefix for cache key
    
    Usage:
        @cached_query(timeout=60, key_prefix='users')
        def get_active_users():
            return User.query.filter_by(active=True).all()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result
        
        return wrapper
    return decorator


def clear_all_caches():
    """Clear all cached data. Use with caution."""
    cache.clear()
    logger.info("All caches cleared")


# Template fragment caching helpers
def cache_key_for_template(template_name, **kwargs):
    """
    Generate a cache key for template fragment caching.
    
    Args:
        template_name: Name of the template or fragment
        **kwargs: Variables that affect the fragment (e.g., user_id, page)
    
    Returns:
        str: Cache key
    """
    key_parts = [template_name]
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    return ":".join(key_parts)


def get_cached_fragment(key):
    """Get a cached template fragment."""
    return cache.get(f"fragment:{key}")


def set_cached_fragment(key, content, timeout=300):
    """Set a cached template fragment."""
    cache.set(f"fragment:{key}", content, timeout=timeout)
