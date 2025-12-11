#!/bin/bash
#
# Verso-Backend Local Development Setup Script
# ============================================
# Complete first-time setup with Stripe CLI integration.
# Usage: ./scripts/setup_local.sh [--run]
#
# Options:
#   --run    Start Flask server and Stripe CLI after setup
#   --help   Show this help message
#

set -euo pipefail

# ==============================================================================
# COLORS AND HELPERS
# ==============================================================================
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# ==============================================================================
# SCRIPT ARGUMENT PARSING
# ==============================================================================
RUN_AFTER_SETUP=false

for arg in "$@"; do
    case $arg in
        --run)
            RUN_AFTER_SETUP=true
            shift
            ;;
        --help|-h)
            echo "Verso-Backend Local Development Setup"
            echo ""
            echo "Usage: ./scripts/setup_local.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --run    Start Flask server and Stripe CLI after setup"
            echo "  --help   Show this help message"
            echo ""
            echo "For complete documentation, see: docs/first_time_setup.md"
            exit 0
            ;;
    esac
done

# ==============================================================================
# MAIN SETUP
# ==============================================================================
print_header "🚀 Verso-Backend Local Development Setup"

# Detect script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

print_info "Project root: $PROJECT_ROOT"

# ==============================================================================
# OS DETECTION
# ==============================================================================
print_header "📦 System Detection"

OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE="Linux";;
    Darwin*)    MACHINE="Mac";;
    CYGWIN*)    MACHINE="Cygwin";;
    MINGW*)     MACHINE="MinGw";;
    MSYS*)      MACHINE="MSYS";;
    *)          MACHINE="UNKNOWN:${OS}"
esac
print_step "Operating System: ${MACHINE}"

# ==============================================================================
# PREREQUISITE CHECKS
# ==============================================================================
print_header "🔍 Checking Prerequisites"

# Check Python 3.10+
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.10 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_PYTHON="3.10"

if [ "$(printf '%s\n' "$REQUIRED_PYTHON" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_PYTHON" ]; then
    print_error "Python 3.10+ is required. Found: ${PYTHON_VERSION}"
    exit 1
fi
print_step "Python: ${PYTHON_VERSION}"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_warn "Node.js is not installed. Frontend assets will not be built."
    print_info "Install Node.js 18+ from https://nodejs.org/"
    HAS_NODE=false
else
    NODE_VERSION=$(node --version | sed 's/v//')
    print_step "Node.js: ${NODE_VERSION}"
    HAS_NODE=true
fi

# Check npm
if ! command -v npm &> /dev/null; then
    print_warn "npm is not installed."
    HAS_NPM=false
else
    NPM_VERSION=$(npm --version)
    print_step "npm: ${NPM_VERSION}"
    HAS_NPM=true
fi

# Check Stripe CLI
if ! command -v stripe &> /dev/null; then
    print_warn "Stripe CLI is not installed."
    echo ""
    echo -e "  ${YELLOW}Install Stripe CLI:${NC}"
    if [[ "$MACHINE" == "Mac" ]]; then
        echo "    brew install stripe/stripe-cli/stripe"
    elif [[ "$MACHINE" == "Linux" ]]; then
        echo "    # For Debian/Ubuntu:"
        echo "    curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg"
        echo "    echo \"deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.dev/stripe-cli-debian-local stable main\" | sudo tee -a /etc/apt/sources.list.d/stripe.list"
        echo "    sudo apt update && sudo apt install stripe"
    else
        echo "    See: https://stripe.com/docs/stripe-cli#install"
    fi
    echo ""
    HAS_STRIPE=false
else
    STRIPE_VERSION=$(stripe --version | head -n1)
    print_step "Stripe CLI: ${STRIPE_VERSION}"
    HAS_STRIPE=true
fi

# ==============================================================================
# VIRTUAL ENVIRONMENT
# ==============================================================================
print_header "🐍 Python Virtual Environment"

if [ ! -d "env" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv env
    print_step "Virtual environment created: env/"
else
    print_step "Virtual environment exists: env/"
fi

# Activate virtual environment
source env/bin/activate
print_step "Virtual environment activated"

# Upgrade pip and install dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
print_step "Python dependencies installed"

# ==============================================================================
# NODE.JS DEPENDENCIES
# ==============================================================================
if [[ "$HAS_NODE" == true ]] && [[ "$HAS_NPM" == true ]]; then
    print_header "📦 Node.js Dependencies"
    
    if [ ! -d "node_modules" ]; then
        print_info "Installing npm packages..."
        npm install --silent
        print_step "npm packages installed"
    else
        print_step "node_modules/ exists (run 'npm install' to update)"
    fi
    
    # Build frontend assets
    print_info "Building frontend assets..."
    npm run build --silent 2>/dev/null || npm run build
    print_step "Frontend assets built"
fi

# ==============================================================================
# ENVIRONMENT CONFIGURATION
# ==============================================================================
print_header "⚙️  Environment Configuration"

if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cat > .env << 'ENVFILE'
# ==============================================================================
# Verso-Backend Environment Configuration
# ==============================================================================
# Generated by setup_local.sh - Update with your actual values!
# Documentation: docs/first_time_setup.md

# ------------------------------------------------------------------------------
# FLASK SETTINGS
# ------------------------------------------------------------------------------
FLASK_APP=app
FLASK_DEBUG=1
SECRET_KEY=CHANGE-ME-generate-a-secure-random-key

# ------------------------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------------------------
# SQLite (local development)
DATABASE_URL=sqlite:///verso.sqlite

# PostgreSQL (production - uncomment and configure)
# DATABASE_URL=postgresql://user:password@localhost:5432/verso

# ------------------------------------------------------------------------------
# STRIPE (Payment Processing)
# ------------------------------------------------------------------------------
# Get your keys from: https://dashboard.stripe.com/test/apikeys
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here

# Webhook secret - run: stripe listen --print-secret
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# ------------------------------------------------------------------------------
# EMAIL (SMTP Configuration)
# ------------------------------------------------------------------------------
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_DEFAULT_SENDER=noreply@example.com

# ------------------------------------------------------------------------------
# GOOGLE OAUTH (Optional)
# ------------------------------------------------------------------------------
# Get credentials from: https://console.cloud.google.com/apis/credentials
# GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
# GOOGLE_CLIENT_SECRET=your_google_client_secret

# ------------------------------------------------------------------------------
# RECAPTCHA (Optional)
# ------------------------------------------------------------------------------
# Get keys from: https://www.google.com/recaptcha/admin
# RECAPTCHA_SITE_KEY=your_recaptcha_site_key
# RECAPTCHA_SECRET_KEY=your_recaptcha_secret_key

# ------------------------------------------------------------------------------
# CACHING (Optional - defaults to in-memory)
# ------------------------------------------------------------------------------
CACHE_TYPE=SimpleCache
# CACHE_TYPE=redis
# CACHE_REDIS_URL=redis://localhost:6379/0

# ------------------------------------------------------------------------------
# DEBUGGING (Development only)
# ------------------------------------------------------------------------------
DEBUG_TB_ENABLED=false
SLOW_QUERY_THRESHOLD=0.5
ENVFILE

    print_step ".env file created"
    print_warn "⚡ IMPORTANT: Edit .env with your actual API keys and settings!"
else
    print_step ".env file exists"
fi

# ==============================================================================
# DATABASE SETUP
# ==============================================================================
print_header "🗄️  Database Setup"

# Source environment for Flask commands
set -a
source .env 2>/dev/null || true
set +a

if [ ! -f "verso.sqlite" ] && [[ "${DATABASE_URL:-}" == *"sqlite"* ]]; then
    print_info "Initializing SQLite database..."
    
    # Run migrations
    if [ -d "migrations" ]; then
        flask db upgrade 2>/dev/null && print_step "Database migrations applied" || {
            print_info "Initializing migrations..."
            flask db init 2>/dev/null || true
            flask db migrate -m "Initial migration" 2>/dev/null || true
            flask db upgrade 2>/dev/null || true
            print_step "Database initialized"
        }
    else
        # No migrations folder - use dbl.py to create tables
        print_info "Creating database tables..."
        python dbl.py
        print_step "Database tables created"
    fi
    
    # Seed default data
    print_info "Seeding default data..."
    flask create-roles 2>/dev/null && print_step "Default roles created" || print_warn "Roles may already exist"
    flask seed-business-config 2>/dev/null && print_step "Business config seeded" || print_warn "Config may already exist"
else
    print_step "Database exists or using external database"
    
    # Still run migrations if needed
    if [ -d "migrations" ]; then
        flask db upgrade 2>/dev/null && print_step "Migrations up to date" || true
    fi
fi

# ==============================================================================
# STRIPE CLI SETUP
# ==============================================================================
if [[ "$HAS_STRIPE" == true ]]; then
    print_header "💳 Stripe CLI Setup"
    
    # Check if logged in
    if stripe config --list 2>/dev/null | grep -q "test_mode_api_key"; then
        print_step "Stripe CLI is configured"
    else
        print_warn "Stripe CLI not logged in"
        print_info "Run: stripe login"
    fi
    
    # Update webhook secret hint
    print_info "To get webhook secret, run:"
    echo -e "    ${YELLOW}stripe listen --print-secret${NC}"
    echo ""
    print_info "Webhook endpoint: /webhooks/stripe"
fi

# ==============================================================================
# COMPLETION
# ==============================================================================
print_header "🎉 Setup Complete!"

echo ""
echo -e "${GREEN}Your Verso-Backend environment is ready!${NC}"
echo ""
echo -e "${BOLD}Quick Start Commands:${NC}"
echo ""
echo -e "  ${CYAN}1. Activate virtual environment:${NC}"
echo -e "     ${YELLOW}source .venv/bin/activate${NC}"
echo ""
echo -e "  ${CYAN}2. Start the development server:${NC}"
echo -e "     ${YELLOW}flask run --host=0.0.0.0${NC}"
echo ""
echo -e "  ${CYAN}3. Start Stripe webhook listener (in another terminal):${NC}"
echo -e "     ${YELLOW}stripe listen --forward-to localhost:5000/webhooks/stripe${NC}"
echo ""
echo -e "  ${CYAN}4. Create an admin user:${NC}"
echo -e "     ${YELLOW}flask set-admin your_email@example.com${NC}"
echo ""
echo -e "${BOLD}Useful URLs:${NC}"
echo -e "  • Application:    ${BLUE}http://localhost:5000${NC}"
echo -e "  • Admin Panel:    ${BLUE}http://localhost:5000/admin${NC}"
echo -e "  • API Docs:       ${BLUE}http://localhost:5000/api/docs${NC}"
echo ""
echo -e "For detailed documentation, see: ${YELLOW}docs/first_time_setup.md${NC}"
echo ""

# ==============================================================================
# OPTIONAL: RUN SERVERS
# ==============================================================================
if [[ "$RUN_AFTER_SETUP" == true ]]; then
    print_header "🚀 Starting Development Servers"
    
    # Function to cleanup background processes on exit
    cleanup() {
        print_info "Shutting down servers..."
        kill $(jobs -p) 2>/dev/null
        exit 0
    }
    trap cleanup SIGINT SIGTERM
    
    # Start Stripe listener if available
    if [[ "$HAS_STRIPE" == true ]]; then
        print_info "Starting Stripe webhook listener..."
        stripe listen --forward-to localhost:5000/webhooks/stripe &
        STRIPE_PID=$!
        sleep 2
    fi
    
    # Start Flask
    print_info "Starting Flask development server..."
    python run.py &
    FLASK_PID=$!
    
    echo ""
    print_step "Servers started! Press Ctrl+C to stop."
    echo ""
    echo -e "  ${CYAN}Flask:${NC}   http://localhost:5000"
    echo -e "  ${CYAN}Stripe:${NC}  Webhook listener forwarding to /webhooks/stripe"
    echo ""
    
    # Wait for processes
    wait
fi
