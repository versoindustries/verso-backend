#!/bin/bash
set -e

echo "🚀 Starting Verso Local Setup..."

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting local setup for Verso-Backend...${NC}"

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
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${GREEN}No .env file found. Creating one from example...${NC}"
    echo "FLASK_APP=app" > .env
    echo "FLASK_DEBUG=1" >> .env
    echo "SECRET_KEY=dev-key-change-me" >> .env
    echo "DATABASE_URL=sqlite:///verso.sqlite" >> .env
fi

if [ ! -f "verso.sqlite" ]; then
    echo "🗄️ Initializing database..."
    flask db upgrade
    echo "🌱 Seeding default data..."
    flask seed-business-config
    flask create-roles
else
    echo "✅ Database found. Running migrations to be safe..."
    flask db upgrade
fi

echo "🎉 Setup complete! Launching Verso..."
python run.py
