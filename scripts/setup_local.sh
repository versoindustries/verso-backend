#!/bin/bash
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Verso Local Setup...${NC}"

# OS Detection
OS="$(uname -s)"
case "${OS}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${OS}"
esac
echo -e "Detected OS: ${GREEN}${machine}${NC}"

# Verify Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
     echo -e "${RED}Python 3.10+ is required. Found ${PYTHON_VERSION}.${NC}"
     exit 1
fi
echo -e "Python version: ${GREEN}${PYTHON_VERSION}${NC}"

# Create/Activate venv
if [ ! -d ".venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}No .env file found. Creating one from example...${NC}"
    cat > .env << 'EOF'
FLASK_APP=app
FLASK_DEBUG=1
SECRET_KEY=dev-key-change-me
DATABASE_URL=sqlite:///verso.sqlite
# Mail configuration (update as needed)
# MAIL_SERVER=smtp.example.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=you@example.com
# MAIL_PASSWORD=your_password
# MAIL_DEFAULT_SENDER=you@example.com
EOF
    echo -e "${GREEN}.env file created. Please update with your settings.${NC}"
fi

# Database setup
if [ ! -f "verso.sqlite" ]; then
    echo -e "${GREEN}🗄️ Initializing database...${NC}"
    flask db upgrade 2>/dev/null || flask db init && flask db upgrade
    echo -e "${GREEN}🌱 Seeding default data...${NC}"
    flask seed-business-config || true
    flask create-roles || true
else
    echo -e "${GREEN}✅ Database found. Running migrations...${NC}"
    flask db upgrade
fi

echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "To run the development server:"
echo -e "  ${YELLOW}source .venv/bin/activate${NC}"
echo -e "  ${YELLOW}python3 run.py${NC}"
echo ""
echo -e "Or use Flask's development server:"
echo -e "  ${YELLOW}source .venv/bin/activate${NC}"
echo -e "  ${YELLOW}flask run --host=0.0.0.0 --debug${NC}"
