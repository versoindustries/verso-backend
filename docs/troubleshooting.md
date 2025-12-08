# Troubleshooting Guide

This guide helps diagnose and resolve common issues with Verso-Backend.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Database Issues](#database-issues)
- [Authentication Issues](#authentication-issues)
- [Email Issues](#email-issues)
- [Payment Issues](#payment-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)

---

## Installation Issues

### Virtual Environment Not Activating

**Symptom:** `source env/bin/activate` fails or Python commands use system Python.

**Solution:**
```bash
# Check if venv exists
ls -la env/

# Recreate if corrupted
rm -rf env/
python3 -m venv env
source env/bin/activate

# Verify correct Python
which python
# Should show: /path/to/project/env/bin/python
```

### Dependency Installation Fails

**Symptom:** `pip install -r requirements.txt` fails with compilation errors.

**Solution:**
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install python3-dev libpq-dev build-essential

# Install system dependencies (macOS)
brew install postgresql

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Try again
pip install -r requirements.txt
```

### psycopg2 Build Fails

**Symptom:** Error building psycopg2 wheel.

**Solution:**
```bash
# Option 1: Install binary version
pip install psycopg2-binary

# Option 2: Install PostgreSQL dev libraries
# Ubuntu/Debian
sudo apt-get install libpq-dev

# macOS
brew install postgresql
```

---

## Database Issues

### Migration Errors

**Symptom:** `flask db upgrade` fails with constraint or dependency errors.

**Solutions:**

```bash
# Check migration status
flask db current
flask db history

# If migrations are out of sync, reset (DEVELOPMENT ONLY)
flask db downgrade base
flask db upgrade

# If foreign key constraint error
# Edit migration file to add constraint names
# See: fix_migration.py script
```

### "Table already exists" Error

**Symptom:** Migration fails because table already exists.

**Solution:**
```bash
# Mark migrations as applied without running
flask db stamp head

# Or reset migrations (DEVELOPMENT ONLY)
rm -rf migrations/
flask db init
flask db migrate -m "Initial"
flask db upgrade
```

### Database Connection Refused

**Symptom:** `OperationalError: could not connect to server`

**Solutions:**

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Check connection string
echo $DATABASE_URL
# Should be: postgresql://user:pass@localhost:5432/dbname

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### SQLite Lock Errors

**Symptom:** `database is locked` errors during writes.

**Solution:**
```python
# In config.py, increase timeout
SQLALCHEMY_ENGINE_OPTIONS = {
    'connect_args': {'timeout': 30}
}
```

Or switch to PostgreSQL for production.

---

## Authentication Issues

### Login Fails with Correct Credentials

**Symptom:** User can't log in despite correct email/password.

**Debugging:**
```python
# In Flask shell
flask shell

>>> from app.models import User
>>> user = User.query.filter_by(email='user@example.com').first()
>>> print(f"User found: {user}")
>>> print(f"Is active: {user.is_active}")
>>> print(f"Password check: {user.check_password('password')}")
```

**Common Causes:**
1. User account is deactivated (`is_active = False`)
2. Password was hashed incorrectly
3. Email case sensitivity issues

**Fix:**
```python
# Reset password
>>> user.set_password('newpassword')
>>> db.session.commit()
```

### Session Expires Too Quickly

**Symptom:** Users are logged out frequently.

**Solution:**
```python
# In config.py
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
REMEMBER_COOKIE_DURATION = timedelta(days=30)
```

### MFA Not Working

**Symptom:** TOTP codes are rejected.

**Debugging:**
```python
# Check server time
import datetime
print(datetime.datetime.utcnow())

# Server time must be accurate (within 30 seconds)
# Sync with NTP
sudo ntpdate pool.ntp.org
```

### Password Reset Emails Not Arriving

See [Email Issues](#email-issues) below.

---

## Email Issues

### Emails Not Sending

**Symptom:** No emails are received, no errors in logs.

**Debugging:**
```python
# Test email configuration
flask shell

>>> from flask_mail import Message
>>> from app.extensions import mail
>>> msg = Message(
...     subject='Test',
...     recipients=['your@email.com'],
...     body='Test message'
... )
>>> mail.send(msg)
```

**Check Configuration:**
```bash
# Verify environment variables
echo $MAIL_SERVER
echo $MAIL_PORT
echo $MAIL_USERNAME
echo $MAIL_PASSWORD
echo $MAIL_USE_TLS
```

### SMTP Authentication Error

**Symptom:** `SMTPAuthenticationError: (535, 'Authentication failed')`

**Solutions:**

For Gmail:
1. Enable "Less secure app access" OR
2. Use App Passwords (recommended):
   - Go to Google Account → Security → App Passwords
   - Generate a new app password
   - Use that password in `MAIL_PASSWORD`

For other providers:
- Verify username/password
- Check if 2FA requires app password
- Verify SMTP port (587 for TLS, 465 for SSL)

### Emails Going to Spam

**Solutions:**
1. Configure SPF, DKIM, and DMARC records
2. Use a dedicated email service (SendGrid, Mailgun)
3. Warm up your sending domain
4. Avoid spam trigger words in subject

---

## Payment Issues

### Stripe Webhook Errors

**Symptom:** Orders not updating after payment.

**Debugging:**
```bash
# Check webhook logs in Stripe Dashboard
# Dashboard → Developers → Webhooks → Select endpoint → Recent events

# Test locally with Stripe CLI
stripe listen --forward-to localhost:5000/webhooks/stripe
```

**Common Causes:**
1. Webhook secret mismatch
2. Signature verification failing
3. Endpoint not accessible

**Solution:**
```python
# Verify webhook secret
echo $STRIPE_WEBHOOK_SECRET
# Should match the secret in Stripe Dashboard
```

### Checkout Session Fails

**Symptom:** "Error creating checkout session"

**Debugging:**
```python
# Check Stripe API key
import stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
print(f"Key starts with: {stripe.api_key[:7]}...")
# Should be 'sk_live_' or 'sk_test_'

# Test API connectivity
try:
    stripe.Account.retrieve()
    print("Stripe connected!")
except stripe.error.AuthenticationError:
    print("Invalid API key")
```

---

## Performance Issues

### Slow Page Loads

**Debugging:**
```python
# Enable query logging
app.config['SQLALCHEMY_ECHO'] = True

# Check for N+1 queries
# Look for repeated similar queries in logs
```

**Solutions:**
```python
# Use eager loading
products = Product.query.options(
    joinedload(Product.category),
    joinedload(Product.images)
).all()

# Add indexes
# In models.py
__table_args__ = (
    Index('idx_product_category', 'category_id'),
)
```

### High Memory Usage

**Debugging:**
```bash
# Check memory usage
ps aux | grep gunicorn

# Profile memory
pip install memory_profiler
python -m memory_profiler run.py
```

**Solutions:**
1. Reduce Gunicorn workers
2. Use pagination for large queries
3. Stream large file downloads
4. Implement caching

### Database Connection Pool Exhausted

**Symptom:** `TimeoutError: QueuePool limit reached`

**Solution:**
```python
# In config.py
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
SQLALCHEMY_POOL_TIMEOUT = 30
SQLALCHEMY_POOL_RECYCLE = 1800
```

---

## Deployment Issues

### Application Won't Start

**Symptom:** Gunicorn fails to start or crashes immediately.

**Debugging:**
```bash
# Check logs
journalctl -u verso-web -n 100

# Test app directly
python -c "from app import create_app; app = create_app(); print('OK')"

# Check for missing environment variables
python -c "import os; print(os.environ.get('SECRET_KEY'))"
```

### Static Files Not Loading

**Symptom:** CSS/JS files return 404.

**Solutions:**

With Nginx:
```nginx
location /static {
    alias /path/to/verso-backend/app/static;
    expires 30d;
}
```

With Flask (development only):
```python
# Ensure static folder is correct
app = Flask(__name__, static_folder='static')
```

### SSL/HTTPS Issues

**Symptom:** Mixed content warnings or redirect loops.

**Solution:**
```python
# In config.py
PREFERRED_URL_SCHEME = 'https'
SESSION_COOKIE_SECURE = True

# With proxy
class ReverseProxied:
    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)
```

### Background Worker Not Running

**Symptom:** Emails not sending, tasks not processing.

**Debugging:**
```bash
# Check worker status
supervisorctl status verso-worker
# or
systemctl status verso-worker

# Check worker logs
tail -f /var/log/verso-worker.err.log

# Test worker directly
flask run-worker
```

---

## Debug Mode

### Enabling Debug Output

**Development only:**
```bash
export FLASK_DEBUG=1
export FLASK_ENV=development
flask run --debug
```

### Flask Shell

Access application context for debugging:
```bash
flask shell

>>> from app.models import User, Order
>>> User.query.count()
>>> Order.query.filter_by(status='pending').all()
```

### SQL Query Logging

```python
# In config.py (development only)
SQLALCHEMY_ECHO = True
```

### Request Debugging

```python
@app.before_request
def log_request():
    app.logger.debug(f"Request: {request.method} {request.path}")
    app.logger.debug(f"Headers: {dict(request.headers)}")
```

---

## Getting Help

If you can't resolve an issue:

1. **Check Logs**: Most issues leave traces in logs
2. **Search Issues**: Check GitHub Issues for similar problems
3. **Minimal Reproduction**: Create a minimal test case
4. **Open Issue**: Include:
   - Python version
   - OS and version
   - Error message and full traceback
   - Steps to reproduce
   - Configuration (redact secrets)

---

*Last Updated: December 2024*
