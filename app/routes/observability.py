"""
Phase 24: Observability & Monitoring - Observability Routes

Provides:
- GET /health - Health check with component status
- GET /ready - Readiness probe for load balancers
- GET /live - Liveness probe for container orchestration
- GET /metrics - Prometheus-compatible metrics endpoint
- Admin metrics dashboard
"""

import time
import os
import platform
from datetime import datetime, timezone, timedelta
from functools import wraps
from collections import defaultdict
from threading import Lock

from flask import Blueprint, jsonify, request, render_template, current_app, g
from flask_login import login_required, current_user

try:
    from app.modules.decorators import role_required
except ImportError:
    def role_required(role):
        def decorator(f):
            return f
        return decorator

# ============================================================================
# Metrics Collection
# ============================================================================

class MetricsCollector:
    """
    Simple in-memory metrics collector.
    
    Collects:
    - Request counts by method, path, status
    - Request duration histograms
    - Database query counts and durations
    - Worker task counts
    - Business metrics (orders, leads, appointments)
    """
    
    def __init__(self):
        self._lock = Lock()
        self._start_time = time.time()
        
        # Request metrics
        self._request_count = defaultdict(int)  # {(method, path, status): count}
        self._request_duration = defaultdict(list)  # {(method, path): [durations]}
        
        # Database metrics
        self._query_count = 0
        self._query_duration_total = 0.0
        self._slow_queries = 0
        
        # Worker metrics
        self._task_count = defaultdict(int)  # {(task_name, status): count}
        self._task_duration = defaultdict(list)
        
        # Cache metrics
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_uptime(self):
        """Get application uptime in seconds."""
        return time.time() - self._start_time
    
    def record_request(self, method, path, status, duration):
        """Record a completed HTTP request."""
        with self._lock:
            # Normalize path to reduce cardinality
            normalized_path = self._normalize_path(path)
            self._request_count[(method, normalized_path, status)] += 1
            
            # Keep last 1000 durations per endpoint
            durations = self._request_duration[(method, normalized_path)]
            durations.append(duration)
            if len(durations) > 1000:
                self._request_duration[(method, normalized_path)] = durations[-1000:]
    
    def record_query(self, duration):
        """Record a database query."""
        with self._lock:
            self._query_count += 1
            self._query_duration_total += duration
            if duration > 0.5:  # Slow query threshold
                self._slow_queries += 1
    
    def record_task(self, task_name, status, duration=None):
        """Record a background task completion."""
        with self._lock:
            self._task_count[(task_name, status)] += 1
            if duration is not None:
                self._task_duration[task_name].append(duration)
    
    def record_cache_hit(self):
        """Record a cache hit."""
        with self._lock:
            self._cache_hits += 1
    
    def record_cache_miss(self):
        """Record a cache miss."""
        with self._lock:
            self._cache_misses += 1
    
    def _normalize_path(self, path):
        """Normalize path to reduce metric cardinality."""
        # Replace numeric IDs with placeholder
        import re
        normalized = re.sub(r'/\d+', '/{id}', path)
        # Truncate long paths
        if len(normalized) > 50:
            normalized = normalized[:50] + '...'
        return normalized
    
    def get_request_stats(self):
        """Get request statistics."""
        with self._lock:
            total = sum(self._request_count.values())
            errors = sum(v for (m, p, s), v in self._request_count.items() if s >= 400)
            
            # Calculate average duration
            all_durations = []
            for durations in self._request_duration.values():
                all_durations.extend(durations)
            
            avg_duration = sum(all_durations) / len(all_durations) if all_durations else 0
            
            return {
                'total': total,
                'errors': errors,
                'error_rate': errors / total if total > 0 else 0,
                'avg_duration_ms': round(avg_duration * 1000, 2)
            }
    
    def get_db_stats(self):
        """Get database statistics."""
        with self._lock:
            return {
                'total_queries': self._query_count,
                'total_duration': round(self._query_duration_total, 3),
                'slow_queries': self._slow_queries,
                'avg_duration_ms': round(
                    (self._query_duration_total / self._query_count * 1000) 
                    if self._query_count > 0 else 0, 2
                )
            }
    
    def get_prometheus_metrics(self):
        """Generate Prometheus-compatible metrics output."""
        lines = []
        
        # Application info
        lines.append('# HELP verso_info Application information')
        lines.append('# TYPE verso_info gauge')
        lines.append(f'verso_info{{version="{current_app.config.get("VERSION", "unknown")}"}} 1')
        
        # Uptime
        lines.append('# HELP verso_uptime_seconds Application uptime in seconds')
        lines.append('# TYPE verso_uptime_seconds counter')
        lines.append(f'verso_uptime_seconds {self.get_uptime():.0f}')
        
        # Request total
        lines.append('# HELP http_requests_total Total HTTP requests')
        lines.append('# TYPE http_requests_total counter')
        with self._lock:
            for (method, path, status), count in self._request_count.items():
                path_escaped = path.replace('"', '\\"')
                lines.append(
                    f'http_requests_total{{method="{method}",path="{path_escaped}",status="{status}"}} {count}'
                )
        
        # Request duration histogram
        lines.append('# HELP http_request_duration_seconds HTTP request duration')
        lines.append('# TYPE http_request_duration_seconds histogram')
        with self._lock:
            for (method, path), durations in self._request_duration.items():
                if durations:
                    path_escaped = path.replace('"', '\\"')
                    # Create histogram buckets
                    buckets = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
                    for bucket in buckets:
                        count = sum(1 for d in durations if d <= bucket)
                        lines.append(
                            f'http_request_duration_seconds_bucket{{method="{method}",path="{path_escaped}",le="{bucket}"}} {count}'
                        )
                    lines.append(
                        f'http_request_duration_seconds_bucket{{method="{method}",path="{path_escaped}",le="+Inf"}} {len(durations)}'
                    )
                    lines.append(
                        f'http_request_duration_seconds_sum{{method="{method}",path="{path_escaped}"}} {sum(durations):.3f}'
                    )
                    lines.append(
                        f'http_request_duration_seconds_count{{method="{method}",path="{path_escaped}"}} {len(durations)}'
                    )
        
        # Database metrics
        lines.append('# HELP db_queries_total Total database queries')
        lines.append('# TYPE db_queries_total counter')
        lines.append(f'db_queries_total {self._query_count}')
        
        lines.append('# HELP db_query_seconds_total Total database query time')
        lines.append('# TYPE db_query_seconds_total counter')
        lines.append(f'db_query_seconds_total {self._query_duration_total:.3f}')
        
        lines.append('# HELP db_slow_queries_total Slow database queries')
        lines.append('# TYPE db_slow_queries_total counter')
        lines.append(f'db_slow_queries_total {self._slow_queries}')
        
        # Worker metrics
        lines.append('# HELP worker_tasks_total Total background tasks')
        lines.append('# TYPE worker_tasks_total counter')
        with self._lock:
            for (task_name, status), count in self._task_count.items():
                lines.append(f'worker_tasks_total{{task="{task_name}",status="{status}"}} {count}')
        
        # Cache metrics
        lines.append('# HELP cache_hits_total Cache hits')
        lines.append('# TYPE cache_hits_total counter')
        lines.append(f'cache_hits_total {self._cache_hits}')
        
        lines.append('# HELP cache_misses_total Cache misses')
        lines.append('# TYPE cache_misses_total counter')
        lines.append(f'cache_misses_total {self._cache_misses}')
        
        return '\n'.join(lines)


# Global metrics collector
metrics_collector = MetricsCollector()


def get_metrics_collector():
    """Get the global metrics collector instance."""
    return metrics_collector


# ============================================================================
# Blueprint Setup
# ============================================================================

observability_bp = Blueprint('observability', __name__)


# ============================================================================
# Health Check Helpers
# ============================================================================

def check_database():
    """Check database connectivity."""
    try:
        from app.database import db
        db.session.execute(db.text('SELECT 1'))
        return {'status': 'ok', 'message': 'Database connection successful'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def check_workers():
    """Check worker health."""
    try:
        from app.models import WorkerHeartbeat
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(minutes=2)
        active_workers = WorkerHeartbeat.query.filter(
            WorkerHeartbeat.last_heartbeat >= cutoff
        ).count()
        
        if active_workers > 0:
            return {'status': 'ok', 'active_workers': active_workers}
        else:
            return {'status': 'degraded', 'message': 'No active workers', 'active_workers': 0}
    except Exception as e:
        return {'status': 'unknown', 'message': str(e)}


def check_cache():
    """Check cache health."""
    try:
        from app.modules.cache import cache
        # Try to set and get a test value
        test_key = '_health_check_test'
        cache.set(test_key, 'ok', timeout=10)
        result = cache.get(test_key)
        cache.delete(test_key)
        
        if result == 'ok':
            return {'status': 'ok', 'message': 'Cache operational'}
        else:
            return {'status': 'degraded', 'message': 'Cache read/write failed'}
    except Exception as e:
        return {'status': 'degraded', 'message': str(e)}


def check_mail():
    """Check mail configuration."""
    try:
        mail_server = current_app.config.get('MAIL_SERVER')
        if mail_server:
            return {'status': 'configured', 'server': mail_server}
        else:
            return {'status': 'not_configured'}
    except Exception as e:
        return {'status': 'unknown', 'message': str(e)}


# ============================================================================
# Public Health Endpoints (No Auth Required)
# ============================================================================

@observability_bp.route('/health')
def health():
    """
    Full health check endpoint.
    
    Returns comprehensive health status of all components.
    No authentication required - this is for load balancers and monitoring.
    
    Returns:
        200: All systems operational
        503: One or more critical systems are down
    """
    checks = {
        'database': check_database(),
        'workers': check_workers(),
        'cache': check_cache(),
        'mail': check_mail(),
    }
    
    # Determine overall status
    critical_checks = ['database']  # Only database is critical
    all_ok = all(
        checks.get(name, {}).get('status') == 'ok' 
        for name in critical_checks
    )
    
    # Add system info
    result = {
        'status': 'healthy' if all_ok else 'unhealthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': current_app.config.get('VERSION', 'unknown'),
        'environment': 'development' if current_app.debug else 'production',
        'uptime_seconds': round(metrics_collector.get_uptime()),
        'checks': checks
    }
    
    status_code = 200 if all_ok else 503
    return jsonify(result), status_code


@observability_bp.route('/ready')
def ready():
    """
    Readiness probe for load balancers.
    
    Returns 200 if the application is ready to receive traffic.
    Checks database connectivity as minimum requirement.
    """
    db_status = check_database()
    
    if db_status['status'] == 'ok':
        return jsonify({
            'ready': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    else:
        return jsonify({
            'ready': False,
            'reason': db_status.get('message', 'Database unavailable'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503


@observability_bp.route('/live')
def live():
    """
    Liveness probe for container orchestration.
    
    Returns 200 if the application process is running.
    This is a minimal check - just confirms the process is alive.
    """
    return jsonify({
        'alive': True,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'pid': os.getpid()
    }), 200


# ============================================================================
# Metrics Endpoint (Optional Auth)
# ============================================================================

@observability_bp.route('/metrics')
def metrics():
    """
    Prometheus-compatible metrics endpoint.
    
    Returns metrics in Prometheus text format.
    Optionally protected by METRICS_TOKEN environment variable.
    """
    # Check for optional token protection
    metrics_token = os.environ.get('METRICS_TOKEN')
    if metrics_token:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return 'Missing authorization', 401
        if auth_header[7:] != metrics_token:
            return 'Invalid token', 403
    
    # Add business metrics
    output = metrics_collector.get_prometheus_metrics()
    output += '\n' + get_business_metrics()
    
    return output, 200, {'Content-Type': 'text/plain; charset=utf-8'}


def get_business_metrics():
    """Generate business-specific metrics."""
    lines = []
    
    try:
        from app.models import Order, Lead, Appointment, User, ContactFormSubmission
        
        # Order metrics
        lines.append('# HELP business_orders_total Total orders')
        lines.append('# TYPE business_orders_total gauge')
        total_orders = Order.query.count()
        lines.append(f'business_orders_total {total_orders}')
        
        # Lead/Contact metrics
        lines.append('# HELP business_leads_total Total leads/contacts')
        lines.append('# TYPE business_leads_total gauge')
        total_contacts = ContactFormSubmission.query.count()
        lines.append(f'business_leads_total {total_contacts}')
        
        # Appointment metrics
        lines.append('# HELP business_appointments_total Total appointments')
        lines.append('# TYPE business_appointments_total gauge')
        total_appointments = Appointment.query.count()
        lines.append(f'business_appointments_total {total_appointments}')
        
        # User metrics
        lines.append('# HELP business_users_total Total registered users')
        lines.append('# TYPE business_users_total gauge')
        total_users = User.query.count()
        lines.append(f'business_users_total {total_users}')
        
        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(hours=24)
        
        lines.append('# HELP business_orders_24h Orders in last 24 hours')
        lines.append('# TYPE business_orders_24h gauge')
        recent_orders = Order.query.filter(Order.created_at >= yesterday).count()
        lines.append(f'business_orders_24h {recent_orders}')
        
        lines.append('# HELP business_users_24h New users in last 24 hours')
        lines.append('# TYPE business_users_24h gauge')
        recent_users = User.query.filter(User.created_at >= yesterday).count()
        lines.append(f'business_users_24h {recent_users}')
        
    except Exception as e:
        lines.append(f'# Error getting business metrics: {e}')
    
    return '\n'.join(lines)


# ============================================================================
# Admin Metrics Dashboard
# ============================================================================

@observability_bp.route('/admin/metrics')
@login_required
@role_required('admin')
def admin_metrics():
    """
    Admin dashboard for system metrics.
    
    Shows:
    - System health status
    - Request statistics
    - Database performance
    - Worker status
    - Business KPIs
    """
    # Collect all metrics
    health_data = {
        'database': check_database(),
        'workers': check_workers(),
        'cache': check_cache(),
        'mail': check_mail(),
    }
    
    request_stats = metrics_collector.get_request_stats()
    db_stats = metrics_collector.get_db_stats()
    uptime = metrics_collector.get_uptime()
    
    # Get business stats
    business_stats = {}
    try:
        from app.models import Order, User, Appointment, Task, ContactFormSubmission
        
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)
        
        business_stats = {
            'total_users': User.query.count(),
            'new_users_24h': User.query.filter(User.created_at >= yesterday).count(),
            'total_orders': Order.query.count(),
            'orders_24h': Order.query.filter(Order.created_at >= yesterday).count(),
            'total_appointments': Appointment.query.count(),
            'total_leads': ContactFormSubmission.query.count(),
            'pending_tasks': Task.query.filter_by(status='pending').count(),
        }
    except Exception as e:
        current_app.logger.error(f'Error getting business stats: {e}')
    
    # System info
    system_info = {
        'python_version': platform.python_version(),
        'flask_debug': current_app.debug,
        'environment': 'development' if current_app.debug else 'production',
        'hostname': platform.node(),
        'uptime_hours': round(uptime / 3600, 2),
    }
    
    return render_template(
        'admin/observability/metrics.html',
        health=health_data,
        request_stats=request_stats,
        db_stats=db_stats,
        business_stats=business_stats,
        system_info=system_info,
        now=now
    )


# ============================================================================
# Metrics Middleware Integration
# ============================================================================

def init_metrics_collection(app):
    """
    Initialize metrics collection middleware.
    
    Hooks into request/response cycle to collect metrics.
    """
    
    @app.before_request
    def before_request_metrics():
        g.metrics_start_time = time.time()
    
    @app.after_request
    def after_request_metrics(response):
        if hasattr(g, 'metrics_start_time'):
            duration = time.time() - g.metrics_start_time
            metrics_collector.record_request(
                method=request.method,
                path=request.path,
                status=response.status_code,
                duration=duration
            )
        return response
    
    # Inject RUM script into templates
    @app.context_processor
    def inject_rum_script():
        try:
            from app.modules.advanced_observability import get_rum_script
            return {'rum_script': get_rum_script()}
        except ImportError:
            return {'rum_script': ''}


# ============================================================================
# Grafana Dashboard & Alerting Rules Export
# ============================================================================

@observability_bp.route('/admin/grafana-dashboard')
@login_required
@role_required('admin')
def export_grafana_dashboard():
    """
    Export Grafana dashboard JSON.
    
    Can be imported directly into Grafana.
    """
    try:
        from app.modules.advanced_observability import generate_grafana_dashboard
        dashboard = generate_grafana_dashboard()
        
        response = jsonify(dashboard)
        response.headers['Content-Disposition'] = 'attachment; filename=verso-backend-dashboard.json'
        return response
    except ImportError:
        return jsonify({'error': 'Advanced observability module not available'}), 500


@observability_bp.route('/admin/alerting-rules')
@login_required
@role_required('admin')
def export_alerting_rules():
    """
    Export Prometheus alerting rules YAML.
    
    Can be used with Prometheus Alertmanager.
    """
    try:
        from app.modules.advanced_observability import generate_alerting_rules
        import yaml
        
        rules = generate_alerting_rules()
        yaml_output = yaml.dump(rules, default_flow_style=False, sort_keys=False)
        
        return yaml_output, 200, {
            'Content-Type': 'text/yaml; charset=utf-8',
            'Content-Disposition': 'attachment; filename=verso-backend-alerts.yml'
        }
    except ImportError as e:
        # If yaml not available, return as JSON
        try:
            from app.modules.advanced_observability import generate_alerting_rules
            return jsonify(generate_alerting_rules())
        except ImportError:
            return jsonify({'error': 'Advanced observability module not available'}), 500


@observability_bp.route('/admin/observability-config')
@login_required
@role_required('admin')
def observability_config():
    """
    Show current observability configuration and status.
    """
    config_status = {
        'log_aggregation': {
            'loki': bool(os.environ.get('LOKI_URL')),
            'elasticsearch': bool(os.environ.get('ELASTICSEARCH_URL')),
            'cloudwatch': bool(os.environ.get('CLOUDWATCH_LOG_GROUP')),
        },
        'tracing': {
            'opentelemetry': os.environ.get('OTEL_ENABLED', '').lower() == 'true',
            'endpoint': os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT'),
        },
        'rum': {
            'enabled': os.environ.get('RUM_ENABLED', '').lower() == 'true',
            'provider': os.environ.get('RUM_PROVIDER', 'custom'),
        },
        'error_tracking': {
            'sentry': bool(os.environ.get('SENTRY_DSN')),
        },
        'metrics': {
            'protected': bool(os.environ.get('METRICS_TOKEN')),
        }
    }
    
    return jsonify(config_status)

