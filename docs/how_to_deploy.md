# Deployment Guide

This document outlines the steps to deploy Verso Backend to local development environments and Heroku.

## Local Development

### Prerequisites
- Python 3.10+
- `pip`
- `make` (optional, for using Makefile)
- SQLite (default) or PostgreSQL

### Setup
1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd verso-backend
   ```

2. **Run Setup Script**:
   This script sets up the virtual environment, installs dependencies, and initializes the database.
   ```bash
   ./scripts/setup_local.sh
   ```
   *Alternatively, use `make dev` if configured.*

3. **Environment Variables**:
   Create a `.env` file in the root directory.
   ```ini
   FLASK_APP=app
   FLASK_DEBUG=1
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///verso.sqlite
   ```

4. **Run the Server**:
   ```bash
   python run.py
   # OR
   flask run --host=0.0.0.0 --debug
   ```

## Heroku Deployment

### Prerequisites
- Heroku CLI installed and logged in.
- Git repository initialized.

### Steps
1. **Create Heroku App**:
   ```bash
   heroku create <app-name>
   ```

2. **Configure Environment**:
   Set the necessary config vars.
   ```bash
   heroku config:set FLASK_APP=app SECRET_KEY=$(openssl rand -hex 32)
   heroku config:set FLASK_DEBUG=0
   ```

3. **Add PostgreSQL**:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. **Deploy Code**:
   ```bash
   git push heroku main
   ```

5. **Initialize Database**:
   Run migrations on the Heroku dyno.
   ```bash
   heroku run flask db upgrade
   heroku run flask seed-business-config
   heroku run flask create-roles
   heroku run flask create-initial-admin
   ```

### Troubleshooting
- **Logs**: Run `heroku logs --tail` to view application logs.
- **500 Errors**: Check if `SECRET_KEY` is set and if the database is properly migrated.

## Production Considerations
- **HTTPS**: Always use HTTPS in production. Heroku provides this by default.
- **Backups**: Enable automatic database backups.
  ```bash
  heroku pg:backups:schedule DATABASE_URL --at '02:00 America/Los_Angeles'
  ```
- **Secret Key**: Ensure `SECRET_KEY` is strong and random.
- **Mail**: Configure `MAIL_SERVER` and credentials for email functionality.
