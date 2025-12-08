import os

class Config:
    WTF_CSRF_ENABLED = True
    
    # Use Heroku's DATABASE_URL if available (production), fallback to SQLite for local development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', "sqlite:///mydatabase.sqlite").replace('postgres://', 'postgresql://')

    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Stripe
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Languages
    LANGUAGES = {
        'en': 'English',
        'es': 'Spanish'
    }
    
    # === Phase 23: Performance Optimization ===
    
    # Flask-Caching Configuration
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'SimpleCache')  # Use 'redis' for production
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))  # 5 minutes
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/0')
    
    # Flask-DebugToolbar Configuration (development only)
    DEBUG_TB_ENABLED = os.environ.get('DEBUG_TB_ENABLED', 'false').lower() == 'true'
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_PROFILER_ENABLED = True
    
    # Flask-Compress Configuration
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml', 'text/javascript',
        'application/json', 'application/javascript', 'application/xml'
    ]
    COMPRESS_LEVEL = 6  # Compression level 1-9
    COMPRESS_MIN_SIZE = 500  # Minimum size to compress (bytes)
    
    # Performance Settings
    SLOW_QUERY_THRESHOLD = float(os.environ.get('SLOW_QUERY_THRESHOLD', 0.5))  # seconds