#!/bin/bash
set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

APP_NAME=$1

if [ -z "$APP_NAME" ]; then
    echo -e "${RED}Usage: ./deploy_heroku.sh <app-name>${NC}"
    exit 1
fi

echo -e "${GREEN}Deploying to Heroku app: ${APP_NAME}...${NC}"

# Check if logged in
if ! heroku whoami &> /dev/null; then
    echo -e "${RED}Not logged in to Heroku. Please run 'heroku login'.${NC}"
    exit 1
fi

# Set git remote if missing
if ! git remote | grep -q "heroku"; then
    echo -e "${GREEN}Adding heroku remote...${NC}"
    heroku git:remote -a "$APP_NAME"
fi

# Push to Heroku
echo -e "${GREEN}Pushing code...${NC}"
git push heroku main

# Run migrations
# Seed business config (idempotent)
echo "🌱 Seeding Business Config..."
flask seed-business-config

# Create roles (idempotent)
echo "👥 Ensuring Roles Exist..."
flask create-roles

echo "✅ Deployment tasks completed."
