# Production Deployment Guide

Complete guide to deploying Verso-Backend in production environments.

## Table of Contents

- [Deployment Options](#deployment-options)
- [VPS Deployment](#vps-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Platforms](#cloud-platforms)
- [Background Worker](#background-worker)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Security Hardening](#security-hardening)
- [Monitoring](#monitoring)
- [Database Migrations](#database-migrations)

---

## Deployment Options

| Option | Best For | Cost | Complexity |
|--------|----------|------|------------|
| **VPS (Recommended)** | Full control, enterprise | $5-50/mo | Medium |
| **Docker** | Consistency, DevOps workflows | Variable | Medium |
| **Heroku** | Quick deployment, small teams | $7-50/mo | Low |
| **Railway/Render** | Modern PaaS, auto-deploy | $5-25/mo | Low |
| **Kubernetes** | Large scale, enterprise | Variable | High |

---

## VPS Deployment

Recommended for production. Full control over infrastructure.

### Prerequisites

- Ubuntu 22.04 LTS or Debian 12
- SSH access with sudo
- Domain name pointing to server IP

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.10 python3.10-venv python3-pip \
    postgresql nginx certbot python3-certbot-nginx \
    supervisor git

# Create application user
sudo useradd -m -s /bin/bash verso
sudo usermod -aG sudo verso
```

### Step 2: PostgreSQL Setup

```bash
# Start PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql <<EOF
CREATE USER verso WITH PASSWORD 'secure_password_here';
CREATE DATABASE verso_production OWNER verso;
GRANT ALL PRIVILEGES ON DATABASE verso_production TO verso;
EOF
```

### Step 3: Application Deploy

```bash
# Switch to app user
sudo su - verso

# Clone repository
git clone https://github.com/versoindustries/verso-backend.git
cd verso-backend

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Configure environment
cat > .env <<EOF
FLASK_APP=app
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=postgresql://verso:secure_password_here@localhost/verso_production
MAIL_SERVER=smtp.your-provider.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
EOF

# Initialize database
flask db upgrade
flask create-roles
flask seed-business-config
```

### Step 4: Gunicorn Service

Create `/etc/systemd/system/verso-web.service`:

```ini
[Unit]
Description=Verso Backend Web Server
After=network.target

[Service]
User=verso
Group=verso
WorkingDirectory=/home/verso/verso-backend
Environment="PATH=/home/verso/verso-backend/venv/bin"
EnvironmentFile=/home/verso/verso-backend/.env
ExecStart=/home/verso/verso-backend/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/verso/access.log \
    --error-logfile /var/log/verso/error.log \
    "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/verso
sudo chown verso:verso /var/log/verso

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable verso-web
sudo systemctl start verso-web
```

### Step 5: Nginx Configuration

Create `/etc/nginx/sites-available/verso`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (for messaging)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /home/verso/verso-backend/app/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    client_max_body_size 16M;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/verso /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Docker Deployment

### Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY . .

# Build frontend
RUN apt-get update && apt-get install -y nodejs npm \
    && npm install && npm run build \
    && apt-get remove -y nodejs npm && apt-get autoremove -y

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:create_app()"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_APP=app
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://verso:${DB_PASSWORD}@db:5432/verso_production
    depends_on:
      - db
      - redis
    restart: unless-stopped

  worker:
    build: .
    command: flask run-worker
    environment:
      - FLASK_APP=app
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://verso:${DB_PASSWORD}@db:5432/verso_production
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=verso
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=verso_production
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Running with Docker

```bash
# Set environment variables
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
export DB_PASSWORD=secure_database_password

# Build and start
docker-compose up -d

# Run migrations
docker-compose exec web flask db upgrade
docker-compose exec web flask create-roles
docker-compose exec web flask seed-business-config

# View logs
docker-compose logs -f
```

---

## Cloud Platforms

### Heroku

```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:essential-0

# Set environment variables
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set FLASK_APP=app
heroku config:set MAIL_SERVER=smtp.your-provider.com
# ... other variables

# Deploy
git push heroku main

# Run migrations
heroku run flask db upgrade
heroku run flask create-roles
heroku run flask seed-business-config

# Scale worker
heroku ps:scale worker=1
```

### Railway

1. Connect GitHub repository at [railway.app](https://railway.app)
2. Add PostgreSQL service
3. Set environment variables in dashboard
4. Deploy triggers automatically on push
5. Run migrations via Railway shell

### DigitalOcean App Platform

1. Create new App from GitHub
2. Set environment variables
3. Add managed PostgreSQL database
4. Configure health checks (`/health`)
5. Deploy

---

## Background Worker

The worker process handles background tasks (email, reports, cleanup).

### Supervisor (Recommended for VPS)

Create `/etc/supervisor/conf.d/verso-worker.conf`:

```ini
[program:verso-worker]
command=/home/verso/verso-backend/venv/bin/flask run-worker
directory=/home/verso/verso-backend
user=verso
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/verso/worker.err.log
stdout_logfile=/var/log/verso/worker.out.log
environment=FLASK_APP="app"
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

### Systemd

Create `/etc/systemd/system/verso-worker.service`:

```ini
[Unit]
Description=Verso Background Worker
After=network.target

[Service]
User=verso
Group=verso
WorkingDirectory=/home/verso/verso-backend
Environment="PATH=/home/verso/verso-backend/venv/bin"
EnvironmentFile=/home/verso/verso-backend/.env
ExecStart=/home/verso/verso-backend/venv/bin/flask run-worker
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## SSL/TLS Configuration

### Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run
```

### Manual SSL Configuration

After obtaining certificate, update Nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # ... rest of configuration
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Security Hardening

### Pre-Deployment Checklist

- [ ] Strong `SECRET_KEY` (minimum 32 bytes)
- [ ] `DEBUG=False` in production
- [ ] HTTPS enforced
- [ ] Database password is strong
- [ ] Firewall configured (UFW)
- [ ] SSH key-only authentication
- [ ] Regular security updates enabled

### Firewall Setup

```bash
# Enable UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Security Headers

Verify headers are set in `app/modules/security_headers.py`:

```python
# These should be included:
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; ...
```

### Rate Limiting

Configure rate limiting in Nginx:

```nginx
# In http block
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

# In server block
location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://127.0.0.1:8000;
}
```

---

## Monitoring

### Health Check Endpoint

The `/health` endpoint returns application status:

```bash
curl https://yourdomain.com/health
# {"status": "healthy", "database": "connected"}
```

### Log Rotation

Create `/etc/logrotate.d/verso`:

```
/var/log/verso/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 verso verso
    sharedscripts
    postrotate
        systemctl reload verso-web
    endscript
}
```

### External Monitoring

Recommended services:
- **Uptime**: UptimeRobot, Pingdom
- **Errors**: Sentry (`SENTRY_DSN` in .env)
- **Metrics**: Prometheus + Grafana

---

## Database Migrations

### Before Deploying Changes

```bash
# On development, create migration
flask db migrate -m "Description of changes"

# Test migration
flask db upgrade
flask db downgrade
flask db upgrade

# Commit migration file to git
git add migrations/
git commit -m "Add migration: Description of changes"
```

### During Deployment

```bash
# SSH to production server
flask db upgrade

# If migration fails, rollback
flask db downgrade
```

### Zero-Downtime Migrations

For critical changes:

1. Deploy new code that works with old AND new schema
2. Run migration
3. Deploy code that only uses new schema
4. Clean up old code

---

*Last Updated: December 2024*
