#!/bin/bash
# Flask Server Startup Script
# Handles common app reference issues by ensuring proper environment setup

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Navigate to project root (one level up from scripts/)
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT" || { echo "Failed to navigate to project root"; exit 1; }

echo "=== Flask Development Server Startup ==="
echo "Project Root: $PROJECT_ROOT"

# Check for virtual environment and activate if exists
if [ -d "env" ]; then
    echo "Activating virtual environment..."
    source env/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Set Flask environment variables
export FLASK_APP=run.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Load .env file if it exists
if [ -f ".env" ]; then
    echo "Loading .env file..."
    set -a
    source .env
    set +a
fi

# Display active configuration
echo "FLASK_APP: $FLASK_APP"
echo "FLASK_ENV: $FLASK_ENV"
echo "FLASK_DEBUG: $FLASK_DEBUG"
echo ""

# Run the Flask server
echo "Starting Flask server in debug mode..."
python run.py
