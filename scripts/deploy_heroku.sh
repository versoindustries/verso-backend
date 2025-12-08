#!/bin/bash
set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get app name from argument or prompt
APP_NAME="${1:-}"

if [ -z "$APP_NAME" ]; then
    echo -e "${RED}Usage: ./deploy_heroku.sh <app-name>${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Deploying to Heroku app: ${APP_NAME}...${NC}"

# Check if logged in
if ! heroku whoami &> /dev/null; then
    echo -e "${RED}Not logged in to Heroku. Please run 'heroku login'.${NC}"
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️ Warning: You have uncommitted changes.${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborted.${NC}"
        exit 1
    fi
fi

# Set git remote if missing
if ! git remote | grep -q "heroku"; then
    echo -e "${GREEN}Adding heroku remote...${NC}"
    heroku git:remote -a "$APP_NAME"
fi

# Push to Heroku
echo -e "${GREEN}Pushing code to Heroku...${NC}"
git push heroku main

# Run database migrations on Heroku
echo -e "${GREEN}🗄️ Running database migrations...${NC}"
heroku run flask db upgrade -a "$APP_NAME"

# Seed business config (idempotent)
echo -e "${GREEN}🌱 Seeding Business Config...${NC}"
heroku run flask seed-business-config -a "$APP_NAME" || true

# Create roles (idempotent)
echo -e "${GREEN}👥 Ensuring Roles Exist...${NC}"
heroku run flask create-roles -a "$APP_NAME" || true

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "View your app at: ${YELLOW}https://${APP_NAME}.herokuapp.com${NC}"
echo -e "View logs with: ${YELLOW}heroku logs --tail -a ${APP_NAME}${NC}"
