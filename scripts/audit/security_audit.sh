#!/bin/bash
#
# Security Audit Script
#
# Runs security scans on the Verso-Backend codebase using:
# - Bandit (Python static analysis)
# - pip-audit (Dependency vulnerabilities)
# - Secret detection
#
# Usage:
#     ./scripts/audit/security_audit.sh [--full]
#
# Options:
#     --full    Run comprehensive scans (slower)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo "============================================================"
echo -e "${BLUE}VERSO-BACKEND SECURITY AUDIT${NC}"
echo "============================================================"
echo ""
echo "Project: $PROJECT_ROOT"
echo "Date: $(date)"
echo ""

# Check for required tools
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${YELLOW}Warning: $1 not found. Installing...${NC}"
        pip install $1 2>/dev/null || echo -e "${RED}Failed to install $1${NC}"
    fi
}

check_tool bandit
check_tool pip-audit

echo "------------------------------------------------------------"
echo -e "${BLUE}1. BANDIT - Python Security Scanner${NC}"
echo "------------------------------------------------------------"
echo ""

# Run Bandit
cd "$PROJECT_ROOT"

echo "Running Bandit security scan..."
echo ""

# Low and higher severity, exclude tests
bandit -r app/ -ll -ii -x app/tests --format txt 2>/dev/null || true

echo ""
echo "------------------------------------------------------------"
echo -e "${BLUE}2. DEPENDENCY VULNERABILITY CHECK${NC}"
echo "------------------------------------------------------------"
echo ""

echo "Checking for vulnerable dependencies..."
echo ""

pip-audit 2>/dev/null || echo -e "${YELLOW}pip-audit check completed (or not installed)${NC}"

echo ""
echo "------------------------------------------------------------"
echo -e "${BLUE}3. SECRET DETECTION${NC}"
echo "------------------------------------------------------------"
echo ""

echo "Scanning for potential secrets in code..."
echo ""

# Patterns to search for
declare -a patterns=(
    "password\s*=\s*['\"][^'\"]*['\"]"
    "api[_-]?key\s*=\s*['\"][^'\"]*['\"]"
    "secret[_-]?key\s*=\s*['\"][^'\"]*['\"]"
    "aws[_-]?(access|secret)"
    "stripe[_-]?(secret|publishable)"
    "BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY"
    "[a-zA-Z0-9+/]{40,}="
)

found_secrets=0

for pattern in "${patterns[@]}"; do
    results=$(grep -rniE "$pattern" app/ --include="*.py" 2>/dev/null | grep -v "__pycache__" | grep -v ".pyc" | grep -v "env.get\|environ.get\|config\." || true)
    if [ ! -z "$results" ]; then
        echo -e "${YELLOW}Potential secret pattern found:${NC}"
        echo "$results" | head -5
        echo ""
        ((found_secrets++)) || true
    fi
done

if [ $found_secrets -eq 0 ]; then
    echo -e "${GREEN}No hardcoded secrets detected.${NC}"
else
    echo -e "${RED}Found $found_secrets potential secret patterns. Please review.${NC}"
fi

echo ""
echo "------------------------------------------------------------"
echo -e "${BLUE}4. SECURITY HEADER CHECK${NC}"
echo "------------------------------------------------------------"
echo ""

echo "Checking for security header implementation..."
echo ""

# Check for security headers middleware
if grep -r "X-Content-Type-Options" app/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ X-Content-Type-Options header found${NC}"
else
    echo -e "${YELLOW}✗ X-Content-Type-Options header not found${NC}"
fi

if grep -r "X-Frame-Options" app/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ X-Frame-Options header found${NC}"
else
    echo -e "${YELLOW}✗ X-Frame-Options header not found${NC}"
fi

if grep -r "Strict-Transport-Security" app/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ HSTS header found${NC}"
else
    echo -e "${YELLOW}✗ HSTS header not found${NC}"
fi

if grep -r "Content-Security-Policy" app/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ CSP header found${NC}"
else
    echo -e "${YELLOW}✗ CSP header not found${NC}"
fi

echo ""
echo "------------------------------------------------------------"
echo -e "${BLUE}5. INPUT VALIDATION CHECK${NC}"
echo "------------------------------------------------------------"
echo ""

echo "Checking for input validation patterns..."
echo ""

# Check for WTForms usage
if grep -r "from wtforms" app/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ WTForms validation in use${NC}"
else
    echo -e "${YELLOW}✗ WTForms not detected${NC}"
fi

# Check for CSRF protection
if grep -r "CSRFProtect\|csrf_token" app/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ CSRF protection found${NC}"
else
    echo -e "${YELLOW}✗ CSRF protection not detected${NC}"
fi

# Check for Bleach (HTML sanitization)
if grep -r "import bleach\|from bleach" app/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Bleach HTML sanitization in use${NC}"
else
    echo -e "${YELLOW}✗ Bleach not detected (for HTML sanitization)${NC}"
fi

echo ""
echo "------------------------------------------------------------"
echo -e "${BLUE}6. AUTHENTICATION CHECK${NC}"
echo "------------------------------------------------------------"
echo ""

# Check for Flask-Login
if grep -r "from flask_login" app/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Flask-Login authentication in use${NC}"
else
    echo -e "${YELLOW}✗ Flask-Login not detected${NC}"
fi

# Check for password hashing
if grep -r "bcrypt\|pbkdf2\|argon2" app/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Password hashing detected${NC}"
else
    echo -e "${YELLOW}✗ Password hashing not detected${NC}"
fi

# Check for rate limiting
if grep -r "rate_limit\|RateLimiter" app/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Rate limiting detected${NC}"
else
    echo -e "${YELLOW}○ Rate limiting not detected (consider adding)${NC}"
fi

echo ""
echo "============================================================"
echo -e "${BLUE}SECURITY AUDIT COMPLETE${NC}"
echo "============================================================"
echo ""
echo "For a full security assessment, consider:"
echo "  - OWASP ZAP dynamic scanning"
echo "  - Manual penetration testing"
echo "  - Third-party security audit"
echo ""
