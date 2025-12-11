# First-Time Setup Guide

> Complete guide to setting up Verso-Backend for local development.

## Quick Start

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/versoindustries/verso-backend.git
cd verso-backend

# Run the setup script
chmod +x scripts/setup_local.sh
./scripts/setup_local.sh

# Edit your environment configuration
nano .env  # or your preferred editor

# Start development servers
./scripts/setup_local.sh --run
```

---

## Prerequisites

### Required

| Software | Version | Installation |
|----------|---------|--------------|
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **pip** | Latest | Included with Python |

### Recommended

| Software | Version | Purpose |
|----------|---------|---------|
| **Node.js** | 18+ | Frontend build (React Islands) |
| **npm** | 9+ | Package management |
| **Stripe CLI** | Latest | Payment webhook testing |

### Installing Stripe CLI

**macOS:**
```bash
brew install stripe/stripe-cli/stripe
```

**Linux (Debian/Ubuntu):**
```bash
# Add Stripe GPG key
curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public | \
  gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg

# Add repository
echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.dev/stripe-cli-debian-local stable main" | \
  sudo tee -a /etc/apt/sources.list.d/stripe.list

# Install
sudo apt update && sudo apt install stripe
```

**Windows:**
```bash
scoop install stripe
```

After installation, authenticate:
```bash
stripe login
```

---

## Manual Setup

If you prefer more control, follow these steps:

### 1. Python Environment

```bash
# Create virtual environment
python3 -m venv env

# Activate (Linux/macOS)
source env/bin/activate

# Activate (Windows)
env\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Frontend Build

```bash
npm install
npm run build  # Production build
# or
npm run dev    # Development with hot reload
```

### 3. Environment Configuration

Create `.env` in the project root:

```bash
cp .env.example .env  # If example exists
# or the setup script creates one automatically
```

### 4. Database Setup

```bash
# Initialize database
python dbl.py           # Creates tables
flask db upgrade        # Apply migrations

# Seed default data
flask create-roles          # Admin, User, Commercial, Blogger
flask seed-business-config  # Business hours, timezone, theme
```

### 5. Create Admin User

```bash
# After registering a user, grant admin access:
flask set-admin your_email@example.com
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_APP` | Flask application | `app` |
| `SECRET_KEY` | Session encryption key | `your-secure-random-key` |
| `DATABASE_URL` | Database connection | `sqlite:///verso.sqlite` |

### Stripe Configuration

| Variable | Description | Where to Find |
|----------|-------------|---------------|
| `STRIPE_PUBLISHABLE_KEY` | Public API key | [Stripe Dashboard → API Keys](https://dashboard.stripe.com/test/apikeys) |
| `STRIPE_SECRET_KEY` | Secret API key | Same as above |
| `STRIPE_WEBHOOK_SECRET` | Webhook signing secret | Run `stripe listen --print-secret` |

### Email Configuration (SMTP)

| Variable | Description | Example |
|----------|-------------|---------|
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USE_TLS` | Enable TLS | `True` |
| `MAIL_USERNAME` | Email username | `your_email@gmail.com` |
| `MAIL_PASSWORD` | Email password/app key | `your_app_password` |
| `MAIL_DEFAULT_SENDER` | From address | `noreply@example.com` |

### OAuth (Optional)

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret |
| `RECAPTCHA_SITE_KEY` | reCAPTCHA site key |
| `RECAPTCHA_SECRET_KEY` | reCAPTCHA secret key |

### Caching (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `CACHE_TYPE` | Cache backend | `SimpleCache` |
| `CACHE_REDIS_URL` | Redis URL | `redis://localhost:6379/0` |

---

## Running the Application

### Development Server (Single Terminal)

```bash
source .venv/bin/activate
flask run --host=0.0.0.0 --debug
```

Application: http://localhost:5000

### With Stripe Webhooks (Two Terminals)

**Terminal 1 - Flask:**
```bash
source .venv/bin/activate
flask run --host=0.0.0.0 --debug
```

**Terminal 2 - Stripe:**
```bash
stripe listen --forward-to localhost:5000/webhooks/stripe
```

### Combined Launch

Use the setup script with `--run`:
```bash
./scripts/setup_local.sh --run
```

This starts both servers and handles cleanup on Ctrl+C.

---

## Stripe Webhook Setup

The webhook endpoint is: `/webhooks/stripe`

### Getting the Webhook Secret

```bash
stripe listen --print-secret
```

Copy the `whsec_...` value to your `.env` file as `STRIPE_WEBHOOK_SECRET`.

### Handled Events

- `checkout.session.completed` - Order/booking payment success
- `invoice.paid` - Subscription payment success
- `invoice.payment_failed` - Subscription payment failure
- `customer.subscription.updated` - Subscription changes
- `customer.subscription.deleted` - Subscription cancellation

### Testing Webhooks

Trigger test events:
```bash
stripe trigger checkout.session.completed
stripe trigger invoice.paid
```

---

## Flask CLI Commands

| Command | Description |
|---------|-------------|
| `flask create-roles` | Create default user roles |
| `flask seed-business-config` | Seed business settings |
| `flask set-admin <email>` | Grant admin role to user |
| `flask db upgrade` | Apply database migrations |
| `flask run-worker` | Start background worker |

---

## Troubleshooting

### "No module named 'app'"

Ensure your virtual environment is activated:
```bash
source .venv/bin/activate
```

### Database Errors

Reset the database:
```bash
rm verso.sqlite  # Backup first if needed!
python dbl.py
flask db upgrade
flask create-roles
flask seed-business-config
```

### Stripe "Invalid signature"

Your webhook secret is incorrect. Get the current secret:
```bash
stripe listen --print-secret
```

Update `STRIPE_WEBHOOK_SECRET` in `.env`.

### Frontend Assets Not Loading

Rebuild Vite assets:
```bash
npm run build
```

For development with hot reload:
```bash
npm run dev
```

### Port Already in Use

Find and kill the process:
```bash
lsof -i :5000
kill -9 <PID>
```

---

## Useful URLs

| URL | Description |
|-----|-------------|
| http://localhost:5000 | Main application |
| http://localhost:5000/admin | Admin dashboard |
| http://localhost:5000/admin/calendar | Appointment calendar |
| http://localhost:5000/api/docs | API documentation |
| http://localhost:5000/login | User login |
| http://localhost:5000/register | User registration |

---

## Next Steps

1. **Edit `.env`** with your API keys and configuration
2. **Register a user** at `/register`
3. **Grant admin access**: `flask set-admin your@email.com`
4. **Access admin panel** at `/admin`
5. **Customize theme** at `/admin/theme`
6. **Configure business hours** at `/admin/settings`

For deployment, see [docs/deployment.md](deployment.md).
