#!/bin/bash
#
# Release Packaging Script
#
# Creates a production-ready deployment package for Verso-Backend.
#
# Usage:
#     ./scripts/package_release.sh [version]
#
# Example:
#     ./scripts/package_release.sh 2.0.0
#
# Output:
#     dist/verso-backend-{version}.tar.gz
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Get version from argument or VERSION file
if [ -n "$1" ]; then
    VERSION="$1"
else
    VERSION=$(cat "$PROJECT_ROOT/VERSION" 2>/dev/null || echo "dev")
fi

PACKAGE_NAME="verso-backend-${VERSION}"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$DIST_DIR/$PACKAGE_NAME"

echo "============================================================"
echo -e "${BLUE}VERSO-BACKEND RELEASE PACKAGER${NC}"
echo "============================================================"
echo ""
echo "Version: $VERSION"
echo "Output:  $DIST_DIR/$PACKAGE_NAME.tar.gz"
echo ""

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf "$BUILD_DIR"
rm -f "$DIST_DIR/$PACKAGE_NAME.tar.gz"
mkdir -p "$BUILD_DIR"

# Build frontend assets
echo ""
echo -e "${BLUE}Building frontend assets...${NC}"
cd "$PROJECT_ROOT"

if [ -f "package.json" ]; then
    npm install --silent
    npm run build
    echo -e "${GREEN}✓ Frontend build complete${NC}"
else
    echo -e "${YELLOW}○ No package.json found, skipping frontend build${NC}"
fi

# Copy application files
echo ""
echo -e "${BLUE}Copying application files...${NC}"

# Core application
cp -r "$PROJECT_ROOT/app" "$BUILD_DIR/"
echo "  ✓ app/"

# Configuration files
cp "$PROJECT_ROOT/requirements.txt" "$BUILD_DIR/"
cp "$PROJECT_ROOT/run.py" "$BUILD_DIR/"
cp "$PROJECT_ROOT/dbl.py" "$BUILD_DIR/"
cp "$PROJECT_ROOT/VERSION" "$BUILD_DIR/"
cp "$PROJECT_ROOT/Makefile" "$BUILD_DIR/" 2>/dev/null || true
echo "  ✓ Configuration files"

# Documentation
mkdir -p "$BUILD_DIR/docs"
cp -r "$PROJECT_ROOT/docs"/* "$BUILD_DIR/docs/" 2>/dev/null || true
cp "$PROJECT_ROOT/README.md" "$BUILD_DIR/"
cp "$PROJECT_ROOT/CHANGELOG.md" "$BUILD_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/RELEASE_NOTES.md" "$BUILD_DIR/" 2>/dev/null || true
cp "$PROJECT_ROOT/LICENSE" "$BUILD_DIR/" 2>/dev/null || true
echo "  ✓ Documentation"

# Migrations
if [ -d "$PROJECT_ROOT/migrations" ]; then
    cp -r "$PROJECT_ROOT/migrations" "$BUILD_DIR/"
    echo "  ✓ migrations/"
fi

# Scripts
mkdir -p "$BUILD_DIR/scripts"
cp -r "$PROJECT_ROOT/scripts"/* "$BUILD_DIR/scripts/" 2>/dev/null || true
echo "  ✓ scripts/"

# Remove development/test files
echo ""
echo -e "${BLUE}Cleaning development files...${NC}"

# Remove __pycache__ directories
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Remove .pyc files
find "$BUILD_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

# Remove test files
rm -rf "$BUILD_DIR/app/tests" 2>/dev/null || true

# Remove .git artifacts
find "$BUILD_DIR" -name ".git*" -exec rm -rf {} + 2>/dev/null || true

# Remove node_modules (frontend is already built)
rm -rf "$BUILD_DIR/node_modules" 2>/dev/null || true

# Remove source TypeScript (keep built JS)
find "$BUILD_DIR" -name "*.tsx" -delete 2>/dev/null || true
find "$BUILD_DIR" -name "*.ts" -not -name "*.d.ts" -delete 2>/dev/null || true

# Remove development configs
rm -f "$BUILD_DIR/.env" 2>/dev/null || true
rm -f "$BUILD_DIR/.env.local" 2>/dev/null || true

echo -e "${GREEN}✓ Development files cleaned${NC}"

# Create .env.example if it doesn't exist
if [ ! -f "$BUILD_DIR/.env.example" ]; then
    cat > "$BUILD_DIR/.env.example" << 'EOF'
# Verso-Backend Environment Configuration
# Copy this file to .env and fill in your values

# Flask Configuration
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-minimum-32-chars

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/verso

# Email (SMTP)
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=noreply@example.com

# Stripe Payments
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Redis (Optional - for caching)
# REDIS_URL=redis://localhost:6379/0

# Security
# SESSION_COOKIE_SECURE=True
# PREFERRED_URL_SCHEME=https

# MFA (Optional)
# MFA_ISSUER_NAME=Your Company Name
EOF
    echo "  ✓ Created .env.example"
fi

# Create installation script
cat > "$BUILD_DIR/install.sh" << 'EOF'
#!/bin/bash
#
# Verso-Backend Installation Script
#
set -e

echo "Installing Verso-Backend..."

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - please edit with your settings"
fi

# Initialize database
echo "Initializing database..."
flask db upgrade
flask create-roles
flask seed-business-config

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your configuration"
echo "  2. Run: source .venv/bin/activate"
echo "  3. Run: flask run --host=0.0.0.0"
echo ""
EOF
chmod +x "$BUILD_DIR/install.sh"
echo "  ✓ Created install.sh"

# Create systemd service file
mkdir -p "$BUILD_DIR/deploy"
cat > "$BUILD_DIR/deploy/verso.service" << 'EOF'
[Unit]
Description=Verso-Backend Web Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/verso-backend
Environment="PATH=/var/www/verso-backend/.venv/bin"
ExecStart=/var/www/verso-backend/.venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8000 "app:create_app()"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
echo "  ✓ Created deploy/verso.service"

# Create nginx config
cat > "$BUILD_DIR/deploy/nginx.conf" << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Static files
    location /static {
        alias /var/www/verso-backend/app/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
echo "  ✓ Created deploy/nginx.conf"

# Generate checksums
echo ""
echo -e "${BLUE}Generating checksums...${NC}"
cd "$BUILD_DIR"
find . -type f -exec sha256sum {} \; > SHA256SUMS
echo -e "${GREEN}✓ SHA256SUMS generated${NC}"

# Create archive
echo ""
echo -e "${BLUE}Creating archive...${NC}"
cd "$DIST_DIR"
tar -czf "$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"

# Calculate archive checksum
ARCHIVE_SHA=$(sha256sum "$PACKAGE_NAME.tar.gz" | cut -d' ' -f1)

# Clean up build directory
rm -rf "$BUILD_DIR"

echo ""
echo "============================================================"
echo -e "${GREEN}PACKAGE CREATED SUCCESSFULLY${NC}"
echo "============================================================"
echo ""
echo "Package:  $DIST_DIR/$PACKAGE_NAME.tar.gz"
echo "Size:     $(du -h "$DIST_DIR/$PACKAGE_NAME.tar.gz" | cut -f1)"
echo "SHA256:   $ARCHIVE_SHA"
echo ""
echo "To deploy:"
echo "  1. Copy package to server"
echo "  2. Extract: tar -xzf $PACKAGE_NAME.tar.gz"
echo "  3. Run: cd $PACKAGE_NAME && ./install.sh"
echo ""
