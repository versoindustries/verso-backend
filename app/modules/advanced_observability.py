"""
Phase 24: Advanced Observability Features

Provides:
- Log aggregation handlers (ELK/Loki/CloudWatch)
- OpenTelemetry distributed tracing
- Real User Monitoring (RUM) injection
- Sentry error tracking integration
- Grafana dashboard configuration export
"""

import os
import json
import logging
import socket
import time
from datetime import datetime, timezone
from functools import wraps

from flask import g, request, has_request_context, current_app

logger = logging.getLogger(__name__)


# ============================================================================
# Log Aggregation Handlers
# ============================================================================

class LokiHandler(logging.Handler):
    """
    Logging handler that sends logs to Grafana Loki.
    
    Configure via environment variables:
    - LOKI_URL: Loki push API URL (e.g., http://loki:3100/loki/api/v1/push)
    - LOKI_LABELS: Additional labels as JSON (e.g., {"env": "prod"})
    """
    
    def __init__(self, url=None, labels=None):
        super().__init__()
        self.url = url or os.environ.get('LOKI_URL')
        self.labels = labels or {}
        
        # Parse labels from environment
        env_labels = os.environ.get('LOKI_LABELS')
        if env_labels:
            try:
                self.labels.update(json.loads(env_labels))
            except json.JSONDecodeError:
                pass
        
        # Add default labels
        self.labels.setdefault('app', 'verso-backend')
        self.labels.setdefault('hostname', socket.gethostname())
        
        self._batch = []
        self._batch_size = 100
        self._last_flush = time.time()
        self._flush_interval = 5  # seconds
    
    def emit(self, record):
        if not self.url:
            return
        
        try:
            # Format log entry
            timestamp_ns = int(time.time() * 1e9)
            
            log_entry = {
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record),
                'module': record.module,
                'function': record.funcName,
            }
            
            # Add request context if available
            if has_request_context():
                log_entry['request_id'] = getattr(g, 'request_id', None)
                log_entry['path'] = request.path
            
            # Add to batch
            self._batch.append([str(timestamp_ns), json.dumps(log_entry)])
            
            # Flush if batch is full or interval elapsed
            if len(self._batch) >= self._batch_size or \
               time.time() - self._last_flush > self._flush_interval:
                self._flush()
                
        except Exception:
            self.handleError(record)
    
    def _flush(self):
        """Send batched logs to Loki."""
        if not self._batch:
            return
        
        try:
            import requests
            
            # Build Loki push payload
            payload = {
                'streams': [{
                    'stream': self.labels,
                    'values': self._batch
                }]
            }
            
            requests.post(
                self.url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
        except Exception as e:
            # Don't fail the application if Loki is down
            pass
        finally:
            self._batch = []
            self._last_flush = time.time()
    
    def close(self):
        """Flush remaining logs on handler close."""
        self._flush()
        super().close()


class ElasticsearchHandler(logging.Handler):
    """
    Logging handler that sends logs to Elasticsearch/OpenSearch.
    
    Configure via environment variables:
    - ELASTICSEARCH_URL: Elasticsearch URL (e.g., http://elasticsearch:9200)
    - ELASTICSEARCH_INDEX: Index name prefix (default: verso-logs)
    - ELASTICSEARCH_USERNAME: Optional username
    - ELASTICSEARCH_PASSWORD: Optional password
    """
    
    def __init__(self, url=None, index_prefix='verso-logs'):
        super().__init__()
        self.url = url or os.environ.get('ELASTICSEARCH_URL')
        self.index_prefix = os.environ.get('ELASTICSEARCH_INDEX', index_prefix)
        self.username = os.environ.get('ELASTICSEARCH_USERNAME')
        self.password = os.environ.get('ELASTICSEARCH_PASSWORD')
        
        self._batch = []
        self._batch_size = 100
        self._last_flush = time.time()
        self._flush_interval = 5
    
    def emit(self, record):
        if not self.url:
            return
        
        try:
            # Format log document
            doc = {
                '@timestamp': datetime.now(timezone.utc).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'hostname': socket.gethostname(),
                'app': 'verso-backend',
            }
            
            # Add request context
            if has_request_context():
                doc['request'] = {
                    'id': getattr(g, 'request_id', None),
                    'method': request.method,
                    'path': request.path,
                    'ip': request.remote_addr,
                }
            
            # Add exception if present
            if record.exc_info:
                doc['exception'] = self.formatException(record.exc_info)
            
            self._batch.append(doc)
            
            if len(self._batch) >= self._batch_size or \
               time.time() - self._last_flush > self._flush_interval:
                self._flush()
                
        except Exception:
            self.handleError(record)
    
    def _flush(self):
        """Send batched logs to Elasticsearch."""
        if not self._batch:
            return
        
        try:
            import requests
            
            # Build bulk request body
            index_name = f"{self.index_prefix}-{datetime.utcnow().strftime('%Y.%m.%d')}"
            
            bulk_body = ''
            for doc in self._batch:
                bulk_body += json.dumps({'index': {'_index': index_name}}) + '\n'
                bulk_body += json.dumps(doc) + '\n'
            
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            
            requests.post(
                f'{self.url}/_bulk',
                data=bulk_body,
                headers={'Content-Type': 'application/x-ndjson'},
                auth=auth,
                timeout=10
            )
        except Exception:
            pass
        finally:
            self._batch = []
            self._last_flush = time.time()
    
    def close(self):
        self._flush()
        super().close()


class CloudWatchHandler(logging.Handler):
    """
    Logging handler that sends logs to AWS CloudWatch Logs.
    
    Configure via environment variables:
    - AWS_REGION: AWS region
    - CLOUDWATCH_LOG_GROUP: Log group name
    - CLOUDWATCH_LOG_STREAM: Log stream name (default: hostname)
    
    Requires boto3 and AWS credentials configured.
    """
    
    def __init__(self, log_group=None, log_stream=None, region=None):
        super().__init__()
        self.log_group = log_group or os.environ.get('CLOUDWATCH_LOG_GROUP', 'verso-backend')
        self.log_stream = log_stream or os.environ.get('CLOUDWATCH_LOG_STREAM', socket.gethostname())
        self.region = region or os.environ.get('AWS_REGION', 'us-east-1')
        
        self._client = None
        self._sequence_token = None
        self._batch = []
        self._batch_size = 100
        self._last_flush = time.time()
        self._flush_interval = 5
    
    def _get_client(self):
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client('logs', region_name=self.region)
                
                # Ensure log group and stream exist
                try:
                    self._client.create_log_group(logGroupName=self.log_group)
                except:
                    pass
                
                try:
                    self._client.create_log_stream(
                        logGroupName=self.log_group,
                        logStreamName=self.log_stream
                    )
                except:
                    pass
            except ImportError:
                return None
        return self._client
    
    def emit(self, record):
        try:
            log_event = {
                'timestamp': int(time.time() * 1000),
                'message': json.dumps({
                    'level': record.levelname,
                    'logger': record.name,
                    'message': self.format(record),
                    'module': record.module,
                    'request_id': getattr(g, 'request_id', None) if has_request_context() else None,
                })
            }
            
            self._batch.append(log_event)
            
            if len(self._batch) >= self._batch_size or \
               time.time() - self._last_flush > self._flush_interval:
                self._flush()
                
        except Exception:
            self.handleError(record)
    
    def _flush(self):
        """Send batched logs to CloudWatch."""
        if not self._batch:
            return
        
        client = self._get_client()
        if not client:
            self._batch = []
            return
        
        try:
            kwargs = {
                'logGroupName': self.log_group,
                'logStreamName': self.log_stream,
                'logEvents': sorted(self._batch, key=lambda x: x['timestamp'])
            }
            
            if self._sequence_token:
                kwargs['sequenceToken'] = self._sequence_token
            
            response = client.put_log_events(**kwargs)
            self._sequence_token = response.get('nextSequenceToken')
        except Exception:
            pass
        finally:
            self._batch = []
            self._last_flush = time.time()
    
    def close(self):
        self._flush()
        super().close()


def setup_log_aggregation(app):
    """
    Set up log aggregation based on environment configuration.
    
    Supports:
    - Loki (LOKI_URL)
    - Elasticsearch (ELASTICSEARCH_URL)
    - CloudWatch (CLOUDWATCH_LOG_GROUP with AWS credentials)
    """
    from app.modules.logging_config import StructuredJsonFormatter
    
    handlers_added = []
    
    # Loki
    if os.environ.get('LOKI_URL'):
        handler = LokiHandler()
        handler.setFormatter(StructuredJsonFormatter(include_request=False))
        logging.getLogger().addHandler(handler)
        handlers_added.append('Loki')
    
    # Elasticsearch
    if os.environ.get('ELASTICSEARCH_URL'):
        handler = ElasticsearchHandler()
        handler.setFormatter(StructuredJsonFormatter(include_request=False))
        logging.getLogger().addHandler(handler)
        handlers_added.append('Elasticsearch')
    
    # CloudWatch
    if os.environ.get('CLOUDWATCH_LOG_GROUP'):
        handler = CloudWatchHandler()
        handler.setFormatter(StructuredJsonFormatter(include_request=False))
        logging.getLogger().addHandler(handler)
        handlers_added.append('CloudWatch')
    
    if handlers_added:
        app.logger.info(f'Log aggregation enabled: {", ".join(handlers_added)}')


# ============================================================================
# OpenTelemetry Distributed Tracing
# ============================================================================

_tracer = None


def init_opentelemetry(app):
    """
    Initialize OpenTelemetry distributed tracing.
    
    Configure via environment variables:
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (e.g., http://jaeger:4317)
    - OTEL_SERVICE_NAME: Service name (default: verso-backend)
    - OTEL_ENABLED: Set to 'true' to enable (default: false)
    """
    global _tracer
    
    if os.environ.get('OTEL_ENABLED', '').lower() != 'true':
        return
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        
        # Configure resource
        resource = Resource.create({
            'service.name': os.environ.get('OTEL_SERVICE_NAME', 'verso-backend'),
            'service.version': app.config.get('VERSION', 'unknown'),
            'deployment.environment': 'production' if not app.debug else 'development',
        })
        
        # Set up tracer provider
        provider = TracerProvider(resource=resource)
        
        # Configure exporter
        endpoint = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT')
        if endpoint:
            exporter = OTLPSpanExporter(endpoint=endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(__name__)
        
        # Auto-instrument Flask
        FlaskInstrumentor().instrument_app(app)
        
        # Auto-instrument SQLAlchemy
        try:
            from app.database import db
            SQLAlchemyInstrumentor().instrument(engine=db.engine)
        except:
            pass
        
        # Auto-instrument outgoing HTTP requests
        RequestsInstrumentor().instrument()
        
        app.logger.info('OpenTelemetry tracing enabled')
        
    except ImportError as e:
        app.logger.warning(f'OpenTelemetry dependencies not installed: {e}')


def get_tracer():
    """Get the configured OpenTelemetry tracer, or None if not configured."""
    return _tracer


def traced(name=None):
    """
    Decorator to create a span for a function.
    
    Usage:
        @traced('my-operation')
        def my_function():
            ...
    """
    def decorator(func):
        span_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            if tracer is None:
                return func(*args, **kwargs)
            
            with tracer.start_as_current_span(span_name) as span:
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


# ============================================================================
# Real User Monitoring (RUM)
# ============================================================================

class RUMConfig:
    """Configuration for Real User Monitoring."""
    
    def __init__(self):
        self.enabled = os.environ.get('RUM_ENABLED', '').lower() == 'true'
        self.provider = os.environ.get('RUM_PROVIDER', 'custom')  # custom, datadog, newrelic
        
        # Provider-specific config
        self.datadog_application_id = os.environ.get('DD_RUM_APPLICATION_ID')
        self.datadog_client_token = os.environ.get('DD_RUM_CLIENT_TOKEN')
        self.newrelic_license_key = os.environ.get('NEW_RELIC_LICENSE_KEY')
        self.newrelic_application_id = os.environ.get('NEW_RELIC_APP_ID')


def get_rum_script():
    """
    Generate the RUM JavaScript snippet to inject in pages.
    
    Returns HTML script tag(s) for Real User Monitoring.
    """
    config = RUMConfig()
    
    if not config.enabled:
        return ''
    
    if config.provider == 'datadog' and config.datadog_application_id:
        return f'''
<script src="https://www.datadoghq-browser-agent.com/datadog-rum-v4.js"></script>
<script>
  window.DD_RUM && window.DD_RUM.init({{
    clientToken: '{config.datadog_client_token}',
    applicationId: '{config.datadog_application_id}',
    site: 'datadoghq.com',
    service: 'verso-backend',
    env: 'production',
    sessionSampleRate: 100,
    sessionReplaySampleRate: 20,
    trackUserInteractions: true,
    trackResources: true,
    trackLongTasks: true,
    defaultPrivacyLevel: 'mask-user-input'
  }});
  window.DD_RUM && window.DD_RUM.startSessionReplayRecording();
</script>
'''
    
    elif config.provider == 'newrelic' and config.newrelic_license_key:
        return f'''
<script type="text/javascript">
  window.NREUM||(NREUM={{}});NREUM.init={{
    distributed_tracing:{{enabled:true}},
    privacy:{{cookies_enabled:true}},
    ajax:{{deny_list:["bam.nr-data.net"]}}
  }};
  NREUM.loader_config={{
    accountID:"{config.newrelic_application_id}",
    trustKey:"{config.newrelic_application_id}",
    agentID:"{config.newrelic_application_id}",
    licenseKey:"{config.newrelic_license_key}",
    applicationID:"{config.newrelic_application_id}"
  }};
</script>
<script src="https://js-agent.newrelic.com/nr-loader-spa-current.min.js"></script>
'''
    
    else:
        # Custom RUM implementation
        return '''
<script>
(function() {
  // Verso RUM - Performance Monitoring
  var rum = {
    init: function() {
      this.startTime = Date.now();
      this.collectPerformance();
      this.trackErrors();
    },
    
    collectPerformance: function() {
      window.addEventListener('load', function() {
        setTimeout(function() {
          var timing = performance.timing;
          var data = {
            dns: timing.domainLookupEnd - timing.domainLookupStart,
            tcp: timing.connectEnd - timing.connectStart,
            ttfb: timing.responseStart - timing.requestStart,
            download: timing.responseEnd - timing.responseStart,
            domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
            load: timing.loadEventEnd - timing.navigationStart,
            path: window.location.pathname
          };
          
          // Send to server
          if (navigator.sendBeacon) {
            navigator.sendBeacon('/rum/collect', JSON.stringify(data));
          }
        }, 0);
      });
    },
    
    trackErrors: function() {
      window.onerror = function(msg, url, line, col, error) {
        var data = {
          message: msg,
          url: url,
          line: line,
          column: col,
          stack: error ? error.stack : null,
          path: window.location.pathname,
          userAgent: navigator.userAgent
        };
        
        if (navigator.sendBeacon) {
          navigator.sendBeacon('/rum/error', JSON.stringify(data));
        }
        return false;
      };
      
      window.addEventListener('unhandledrejection', function(event) {
        var data = {
          message: event.reason ? event.reason.message : 'Promise rejection',
          stack: event.reason ? event.reason.stack : null,
          path: window.location.pathname
        };
        
        if (navigator.sendBeacon) {
          navigator.sendBeacon('/rum/error', JSON.stringify(data));
        }
      });
    }
  };
  
  rum.init();
})();
</script>
'''


def init_rum_routes(app):
    """
    Initialize RUM data collection endpoints.
    
    Creates endpoints:
    - POST /rum/collect - Collect performance metrics
    - POST /rum/error - Collect client-side errors
    """
    from flask import Blueprint, request, jsonify
    from app import csrf
    
    rum_bp = Blueprint('rum', __name__, url_prefix='/rum')
    
    @rum_bp.route('/collect', methods=['POST'])
    def collect_performance():
        """Collect RUM performance data."""
        try:
            data = request.get_json(silent=True) or {}
            
            # Log performance metrics
            logger.info('RUM performance', extra={
                'rum_type': 'performance',
                'path': data.get('path'),
                'dns_ms': data.get('dns'),
                'tcp_ms': data.get('tcp'),
                'ttfb_ms': data.get('ttfb'),
                'dom_ready_ms': data.get('domReady'),
                'load_ms': data.get('load'),
            })
            
            return '', 204
        except Exception:
            return '', 204
    
    @rum_bp.route('/error', methods=['POST'])
    def collect_error():
        """Collect RUM error data."""
        try:
            data = request.get_json(silent=True) or {}
            
            # Log client error
            logger.warning('RUM client error', extra={
                'rum_type': 'error',
                'message': data.get('message'),
                'url': data.get('url'),
                'line': data.get('line'),
                'column': data.get('column'),
                'path': data.get('path'),
                'user_agent': data.get('userAgent'),
            })
            
            return '', 204
        except Exception:
            return '', 204
    
    # Exempt RUM routes from CSRF (beacon API doesn't send tokens)
    csrf.exempt(rum_bp)
    app.register_blueprint(rum_bp)
    
    app.logger.info('RUM collection endpoints enabled')


# ============================================================================
# Sentry Error Tracking
# ============================================================================

def init_sentry(app):
    """
    Initialize Sentry error tracking.
    
    Configure via environment variables:
    - SENTRY_DSN: Sentry DSN
    - SENTRY_ENVIRONMENT: Environment name (default: production/development)
    - SENTRY_TRACES_SAMPLE_RATE: Performance monitoring sample rate (0.0-1.0)
    - SENTRY_PROFILES_SAMPLE_RATE: Profiling sample rate (0.0-1.0)
    """
    sentry_dsn = os.environ.get('SENTRY_DSN')
    
    if not sentry_dsn:
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        # Configure logging integration
        logging_integration = LoggingIntegration(
            level=logging.INFO,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors and above as events
        )
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.environ.get('SENTRY_ENVIRONMENT', 
                                       'development' if app.debug else 'production'),
            release=app.config.get('VERSION', 'unknown'),
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
                logging_integration,
            ],
            traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
            send_default_pii=False,  # Don't send PII by default
            before_send=_sentry_before_send,
        )
        
        app.logger.info('Sentry error tracking enabled')
        
    except ImportError as e:
        app.logger.warning(f'Sentry SDK not installed: {e}')


def _sentry_before_send(event, hint):
    """
    Filter/modify events before sending to Sentry.
    
    - Removes sensitive data
    - Filters out expected exceptions
    """
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        for key in ['Authorization', 'Cookie', 'X-Api-Key']:
            if key in headers:
                headers[key] = '[REDACTED]'
    
    # Remove sensitive form data
    if 'request' in event and 'data' in event['request']:
        data = event['request'].get('data')
        if isinstance(data, dict):
            for key in ['password', 'token', 'secret', 'api_key', 'credit_card']:
                if key in data:
                    data[key] = '[REDACTED]'
    
    # Filter out specific exceptions
    if 'exception' in hint:
        exc_type = type(hint['exception']).__name__
        # Don't report 404s as errors
        if exc_type == 'NotFound':
            return None
    
    return event


def capture_exception(exception, **extra_context):
    """
    Capture an exception to Sentry with additional context.
    
    Args:
        exception: The exception to capture
        **extra_context: Additional context to attach
    """
    try:
        import sentry_sdk
        
        with sentry_sdk.push_scope() as scope:
            for key, value in extra_context.items():
                scope.set_extra(key, value)
            
            # Add request context if available
            if has_request_context():
                scope.set_extra('request_id', getattr(g, 'request_id', None))
            
            sentry_sdk.capture_exception(exception)
    except ImportError:
        # Sentry not installed, just log
        logger.exception('Exception captured (Sentry not available)', exc_info=exception)


def capture_message(message, level='info', **extra_context):
    """
    Send a message to Sentry.
    
    Args:
        message: Message to send
        level: Severity level (debug, info, warning, error, fatal)
        **extra_context: Additional context to attach
    """
    try:
        import sentry_sdk
        
        with sentry_sdk.push_scope() as scope:
            for key, value in extra_context.items():
                scope.set_extra(key, value)
            
            sentry_sdk.capture_message(message, level=level)
    except ImportError:
        getattr(logger, level, logger.info)(message)


# ============================================================================
# Grafana Dashboard Export
# ============================================================================

def generate_grafana_dashboard():
    """
    Generate a Grafana dashboard JSON for Verso Backend.
    
    Returns a complete dashboard definition that can be imported into Grafana.
    """
    return {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": [
            # Request Rate Panel
            {
                "type": "timeseries",
                "title": "Request Rate",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "targets": [{
                    "expr": 'rate(http_requests_total{job="verso-backend"}[5m])',
                    "legendFormat": "{{method}} {{path}}",
                    "refId": "A"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "reqps"
                    }
                }
            },
            # Error Rate Panel
            {
                "type": "timeseries",
                "title": "Error Rate",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                "targets": [{
                    "expr": 'rate(http_requests_total{job="verso-backend",status=~"5.."}[5m]) / rate(http_requests_total{job="verso-backend"}[5m]) * 100',
                    "legendFormat": "Error %",
                    "refId": "A"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 1},
                                {"color": "red", "value": 5}
                            ]
                        }
                    }
                }
            },
            # Response Time Panel
            {
                "type": "timeseries",
                "title": "Response Time (p95)",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "targets": [{
                    "expr": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="verso-backend"}[5m]))',
                    "legendFormat": "p95",
                    "refId": "A"
                }, {
                    "expr": 'histogram_quantile(0.50, rate(http_request_duration_seconds_bucket{job="verso-backend"}[5m]))',
                    "legendFormat": "p50",
                    "refId": "B"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "s"
                    }
                }
            },
            # Database Queries Panel
            {
                "type": "stat",
                "title": "Database Queries",
                "gridPos": {"h": 4, "w": 6, "x": 12, "y": 8},
                "targets": [{
                    "expr": 'rate(db_queries_total{job="verso-backend"}[5m])',
                    "legendFormat": "Queries/sec",
                    "refId": "A"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "short"
                    }
                }
            },
            # Slow Queries Panel
            {
                "type": "stat",
                "title": "Slow Queries",
                "gridPos": {"h": 4, "w": 6, "x": 18, "y": 8},
                "targets": [{
                    "expr": 'db_slow_queries_total{job="verso-backend"}',
                    "legendFormat": "Slow Queries",
                    "refId": "A"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "short",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 10},
                                {"color": "red", "value": 50}
                            ]
                        }
                    }
                }
            },
            # Business Metrics Row
            {
                "type": "stat",
                "title": "Total Users",
                "gridPos": {"h": 4, "w": 4, "x": 0, "y": 16},
                "targets": [{
                    "expr": 'business_users_total{job="verso-backend"}',
                    "refId": "A"
                }]
            },
            {
                "type": "stat",
                "title": "Total Orders",
                "gridPos": {"h": 4, "w": 4, "x": 4, "y": 16},
                "targets": [{
                    "expr": 'business_orders_total{job="verso-backend"}',
                    "refId": "A"
                }]
            },
            {
                "type": "stat",
                "title": "Total Leads",
                "gridPos": {"h": 4, "w": 4, "x": 8, "y": 16},
                "targets": [{
                    "expr": 'business_leads_total{job="verso-backend"}',
                    "refId": "A"
                }]
            },
            {
                "type": "stat",
                "title": "Orders (24h)",
                "gridPos": {"h": 4, "w": 4, "x": 12, "y": 16},
                "targets": [{
                    "expr": 'business_orders_24h{job="verso-backend"}',
                    "refId": "A"
                }]
            },
            {
                "type": "stat",
                "title": "New Users (24h)",
                "gridPos": {"h": 4, "w": 4, "x": 16, "y": 16},
                "targets": [{
                    "expr": 'business_users_24h{job="verso-backend"}',
                    "refId": "A"
                }]
            },
            {
                "type": "stat",
                "title": "Uptime",
                "gridPos": {"h": 4, "w": 4, "x": 20, "y": 16},
                "targets": [{
                    "expr": 'verso_uptime_seconds{job="verso-backend"}',
                    "refId": "A"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "s"
                    }
                }
            },
            # Worker Tasks Panel
            {
                "type": "timeseries",
                "title": "Worker Tasks",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 20},
                "targets": [{
                    "expr": 'rate(worker_tasks_total{job="verso-backend"}[5m])',
                    "legendFormat": "{{task}} - {{status}}",
                    "refId": "A"
                }]
            },
            # Cache Hit Rate Panel
            {
                "type": "gauge",
                "title": "Cache Hit Rate",
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 20},
                "targets": [{
                    "expr": 'cache_hits_total{job="verso-backend"} / (cache_hits_total{job="verso-backend"} + cache_misses_total{job="verso-backend"}) * 100',
                    "refId": "A"
                }],
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "min": 0,
                        "max": 100,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "red", "value": None},
                                {"color": "yellow", "value": 50},
                                {"color": "green", "value": 80}
                            ]
                        }
                    }
                }
            }
        ],
        "refresh": "30s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["verso", "backend", "flask"],
        "templating": {"list": []},
        "time": {"from": "now-6h", "to": "now"},
        "timepicker": {},
        "timezone": "",
        "title": "Verso Backend Dashboard",
        "uid": "verso-backend",
        "version": 1,
        "weekStart": ""
    }


# ============================================================================
# Alerting Rules for Prometheus/Alertmanager
# ============================================================================

def generate_alerting_rules():
    """
    Generate Prometheus alerting rules for Verso Backend.
    
    Returns YAML-compatible dict for Prometheus rules.
    """
    return {
        "groups": [{
            "name": "verso-backend",
            "rules": [
                {
                    "alert": "HighErrorRate",
                    "expr": 'rate(http_requests_total{job="verso-backend",status=~"5.."}[5m]) / rate(http_requests_total{job="verso-backend"}[5m]) > 0.05',
                    "for": "5m",
                    "labels": {"severity": "critical"},
                    "annotations": {
                        "summary": "High error rate detected",
                        "description": "Error rate is above 5% for the last 5 minutes"
                    }
                },
                {
                    "alert": "SlowResponseTime",
                    "expr": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="verso-backend"}[5m])) > 2',
                    "for": "5m",
                    "labels": {"severity": "warning"},
                    "annotations": {
                        "summary": "Slow response times",
                        "description": "95th percentile response time is above 2 seconds"
                    }
                },
                {
                    "alert": "HighSlowQueryCount",
                    "expr": 'increase(db_slow_queries_total{job="verso-backend"}[1h]) > 100',
                    "for": "15m",
                    "labels": {"severity": "warning"},
                    "annotations": {
                        "summary": "High number of slow database queries",
                        "description": "More than 100 slow queries in the last hour"
                    }
                },
                {
                    "alert": "ServiceDown",
                    "expr": 'up{job="verso-backend"} == 0',
                    "for": "1m",
                    "labels": {"severity": "critical"},
                    "annotations": {
                        "summary": "Verso Backend is down",
                        "description": "The service has been unreachable for more than 1 minute"
                    }
                },
                {
                    "alert": "NoActiveWorkers",
                    "expr": 'sum(worker_heartbeat_active{job="verso-backend"}) == 0',
                    "for": "5m",
                    "labels": {"severity": "warning"},
                    "annotations": {
                        "summary": "No active background workers",
                        "description": "No workers have sent a heartbeat in the last 5 minutes"
                    }
                }
            ]
        }]
    }


# ============================================================================
# Master Initialization
# ============================================================================

def init_advanced_observability(app):
    """
    Initialize all advanced observability features.
    
    Call this in app factory after basic observability is set up.
    """
    # Log aggregation
    setup_log_aggregation(app)
    
    # OpenTelemetry distributed tracing
    init_opentelemetry(app)
    
    # RUM collection endpoints
    if os.environ.get('RUM_ENABLED', '').lower() == 'true':
        init_rum_routes(app)
    
    # Sentry error tracking
    init_sentry(app)
    
    app.logger.info('Advanced observability features initialized')
