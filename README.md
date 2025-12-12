<p align="center">
  <img src="app/static/images/logo.png" alt="Verso Logo" width="180" />
</p>

<h1 align="center">Verso-Backend</h1>
<h3 align="center">The Sovereign Enterprise Platform</h3>

<p align="center">
  <strong>End the SaaS Tax. Own your stack. Sleep at night.</strong>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-what-verso-replaces">What It Replaces</a> •
  <a href="#-features">Features</a> •
  <a href="#-documentation">Docs</a> •
  <a href="#-deployment">Deploy</a> •
  <a href="#-contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/flask-3.0+-green.svg" alt="Flask 3.0+" />
  <img src="https://img.shields.io/badge/react-18-61dafb.svg" alt="React 18" />
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License" />
  <img src="https://img.shields.io/github/stars/versoindustries/verso-backend?style=social" alt="GitHub Stars" />
</p>

---

## 🎯 The Problem We Solve

Most small-to-medium businesses are bleeding **$12,000–$25,000/year** on fragmented SaaS tools that don't talk to each other:

| What You're Paying For | Typical Monthly Cost |
|------------------------|---------------------|
| CRM (HubSpot, Salesforce) | $200–$500/mo |
| Scheduling (Calendly, Acuity) | $100–$200/mo |
| Email Marketing (Mailchimp, Klaviyo) | $100–$300/mo |
| Team Chat (Slack, Teams) | $150–$250/mo |
| HR Portal (BambooHR) | $100–$200/mo |
| Forms/Surveys (Typeform) | $50–$100/mo |
| CMS/Blog (WordPress hosting) | $50–$150/mo |
| **Total Integration Tax** | **$750–$1,700/mo** |

**Verso replaces all of this with one self-hosted system you actually own.**

---

## 💡 The Verso Philosophy

> **"Server-side truth. Single latency domain. No rent-seeking dependencies."**

Verso is not a starter kit. It's a **production-grade modular monolith** built on boring, battle-tested technology that will still run in 2035:

- **Python + Flask** — The world's most readable backend language
- **SQLAlchemy + PostgreSQL/SQLite** — ACID-compliant data you control
- **Jinja2 SSR + React Islands** — Zero hydration errors, progressive enhancement
- **Your Server** — VPS, bare metal, Raspberry Pi, air-gapped facility

**We optimize for:** Unit economics, operational sovereignty, long-term maintainability

**We reject:** Framework churn, per-seat pricing, vendor lock-in, "serverless" roulette

---

## 💰 Economic Comparison

### Year 1 Cost: Typical SaaS Stack vs. Verso

| Scenario | SaaS Stack (15 employees) | Verso (Self-Hosted) |
|----------|---------------------------|---------------------|
| **Monthly Software** | $1,500/mo | $0 |
| **Hosting** | $150/mo (variable) | $20–$40/mo (fixed) |
| **Setup/Migration** | $0 | $2,500–$5,000 (one-time) |
| **Year 1 Total** | **$19,800** | **$3,240–$5,480** |
| **Year 2+ Total** | **$19,800/yr** | **$240–$480/yr** |

> **ROI:** Verso pays for itself in **60–90 days**. Every year after, you keep the $15,000+.

---

## ✅ What Verso Replaces

### The "Annoying Stack" We Eliminate

| Category | Tools You're Paying For | Verso Equivalent |
|----------|------------------------|------------------|
| **CRM & Leads** | HubSpot, Salesforce, Pipedrive | Built-in CRM with pipeline stages |
| **Scheduling** | Calendly, Acuity, Jobber | Full booking system with staff availability |
| **Email Marketing** | Mailchimp, Klaviyo, Constant Contact | Campaigns, templates, drip sequences |
| **Team Messaging** | Slack, Microsoft Teams | Channels, threads, @mentions, emoji reactions |
| **Forms & Surveys** | Typeform, JotForm, Google Forms | Dynamic form builder + NPS/CSAT |
| **Website/Blog** | WordPress, Contentful, Squarespace | Full CMS with SEO, JSON-LD, sitemaps |
| **HR Portal** | BambooHR (basic), Gusto (HR only) | Leave requests, time tracking, employee directory |
| **Analytics** | Mixpanel, GA | Built-in visitor tracking & conversion funnels |

### What We **Don't** Replace

| System | Why | Our Approach |
|--------|-----|--------------|
| **Accounting** (QuickBooks, Xero) | Critical financial infrastructure | Keep it. We don't touch your books. |
| **Payroll** (Gusto, ADP) | Heavily regulated, compliance risk | Keep it. Use our HR portal alongside. |
| **Deep Inventory/ERP** | Complex enterprise systems | Keep it. We handle orders and CRM. |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend build)
- SQLite (dev) or PostgreSQL (production)

### Installation

```bash
# Clone the repository
git clone https://github.com/versoindustries/verso-backend.git
cd verso-backend

# Create virtual environment
python3 -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
npm install

# Configure environment
cp .env.example .env
# Edit .env with your settings (see Configuration section)

# Initialize database
python dbl.py
flask db upgrade
flask create-roles
flask seed-business-config

# Build frontend assets
npm run build

# Run the server
flask run --host=0.0.0.0 --debug
```

Visit **http://localhost:5000** — you're sovereign now.

### Configuration

Create a `.env` file with these essential variables:

```env
# Core
FLASK_APP=app
SECRET_KEY=your-secure-random-key-here
DATABASE_URL=sqlite:///verso.sqlite

# Email (for notifications, password reset)
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=you@example.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Optional: Stripe (for payments)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional: Storage
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=your-bucket
```

---

## 📦 Features

### Core Platform

| Module | Description | Key Files |
|--------|-------------|-----------|
| **Authentication & RBAC** | Flask-Login with role-based access control | `app/modules/auth_manager.py` |
| **Multi-tenant Support** | Business isolation with configurable branding | `app/models.py:Business` |
| **React Islands Architecture** | Progressive enhancement with Vite + TypeScript | `app/static/src/` |

### Customer-Facing

| Module | Description | Routes |
|--------|-------------|--------|
| **Public Website** | SEO-optimized pages with CMS | `/`, `/about`, `/services` |
| **Blog/Content** | Full CMS with CKEditor, categories, tags | `/blog/*` |
| **Online Booking** | Calendar with staff availability, services | `/book/*`, `/api/calendar/*` |
| **E-commerce** | Products, variants, cart, Stripe checkout | `/shop/*`, `/cart/*` |
| **Customer Portal** | Orders, appointments, account settings | `/my-account/*` |

### Business Operations

| Module | Description | Routes |
|--------|-------------|--------|
| **CRM & Pipeline** | Contacts, leads, deal stages, activities | `/admin/crm/*` |
| **Email Marketing** | Campaigns, templates, subscriber segments | `/admin/campaigns/*` |
| **Team Messaging** | Channels, threads, mentions, file sharing | `/messaging/*` |
| **HR & Time Tracking** | Leave requests, timecards, employee profiles | `/admin/hr/*` |
| **Automation** | Workflow builder with triggers and actions | `/admin/automation/*` |
| **Analytics** | Visitor tracking, conversion funnels, reports | `/admin/analytics/*` |

### Admin & Settings

| Module | Description | Routes |
|--------|-------------|--------|
| **Admin Dashboard** | Unified command center for all operations | `/admin/` |
| **Theme Editor** | Visual customization with live preview | `/admin/theme-editor/*` |
| **Location Manager** | Multi-location support with HQ designation | `/admin/locations/*` |
| **User Management** | Roles, permissions, team administration | `/admin/users/*` |

---

## 📁 Repository Structure

```
verso-backend/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py             # Configuration classes
│   ├── models.py             # SQLAlchemy models (136 classes)
│   ├── routes/               # Flask blueprints (47 route files)
│   │   ├── admin.py          # Admin dashboard routes
│   │   ├── auth.py           # Authentication routes
│   │   ├── blog.py           # Blog/CMS routes
│   │   ├── booking.py        # Appointment scheduling
│   │   ├── shop.py           # E-commerce routes
│   │   └── ...
│   ├── modules/              # Business logic (35 modules)
│   │   ├── auth_manager.py   # RBAC decorators
│   │   ├── email_service.py  # Email sending utilities
│   │   ├── file_manager.py   # Upload handling
│   │   └── ...
│   ├── templates/            # Jinja2 templates
│   └── static/
│       └── src/              # React TypeScript source
│           ├── components/   # React components
│           ├── registry.ts   # Island registration
│           └── types.ts      # TypeScript definitions
├── migrations/               # Flask-Migrate scripts
├── docs/                     # Documentation
├── tests/                    # Pytest test suite
├── scripts/                  # Utility scripts
├── vite.config.js            # Frontend build config
├── requirements.txt          # Python dependencies
└── package.json              # Node.js dependencies
```

---

## 🚢 Deployment

### Option 1: Sovereign VPS (Recommended)

Deploy on any Linux VPS (DigitalOcean, Linode, Hetzner, etc.):

```bash
# On your server
git clone https://github.com/versoindustries/verso-backend.git
cd verso-backend

# Setup environment
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt gunicorn
npm install && npm run build

# Configure
cp .env.example .env
nano .env  # Set production values

# Database
flask db upgrade
flask create-roles
flask seed-business-config

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

Configure Nginx as reverse proxy, add SSL with Let's Encrypt, set up systemd for auto-restart.

**Full deployment guide:** [docs/deployment.md](docs/deployment.md)

### Option 2: Docker

```bash
docker build -t verso-backend .
docker run -p 5000:5000 --env-file .env verso-backend
```

### Option 3: Platform-as-a-Service

Works with Heroku, Railway, Render, or any platform supporting Python:

```bash
# Procfile included
web: gunicorn "app:create_app()"
```

### Option 4: Air-Gapped / Edge

Runs on Raspberry Pi 4+, Intel NUC, or any device with Python 3.10. No external API calls required for core functionality.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/architecture.md) | System design, data flow, module relationships |
| [API Reference](docs/api_reference.md) | REST endpoints, authentication, examples |
| [Database Schema](docs/database_schema.md) | All 136 models explained |
| [Deployment Guide](docs/deployment.md) | Production setup, Nginx, SSL, monitoring |
| [First Time Setup](docs/first_time_setup.md) | Detailed onboarding walkthrough |
| [How to Extend](docs/how_to_extend.md) | Adding features, custom modules |
| [Testing Guide](docs/testing.md) | Running pytest, coverage, CI/CD |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |
| [OpenAPI Spec](docs/openapi.yaml) | Machine-readable API specification |

### For Developers

| Document | Description |
|----------|-------------|
| [Contributing Guide](docs/CONTRIBUTING.md) | Code standards, PR process |
| [React Islands Pattern](docs/developer/react_islands.md) | Frontend architecture |
| [Module Conventions](docs/developer/conventions.md) | Naming, structure, patterns |

---

## 🔒 Security & Compliance

Verso is built with enterprise security requirements in mind:

### OWASP Top 10 Compliance

- ✅ **Injection Prevention** — SQLAlchemy ORM for all database operations
- ✅ **Broken Authentication** — Flask-Login with secure session handling
- ✅ **XSS Protection** — Jinja2 auto-escaping, React DOM sanitization
- ✅ **CSRF Protection** — Flask-WTF tokens on all forms
- ✅ **Security Headers** — Configurable CSP, HSTS, X-Frame-Options

### SOC2 Readiness

- ✅ **Change Management** — All schema changes via Flask-Migrate
- ✅ **Access Control** — RBAC with audit logging
- ✅ **Data Privacy** — No PII in logs, configurable data retention
- ✅ **Encryption** — HTTPS enforced, bcrypt password hashing

**Security documentation:** [docs/compliance/](docs/compliance/)

---

## 🧪 Testing

```bash
# Run full test suite
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_auth.py -v

# Type checking
npm run type-check

# Dead code detection
vulture app/ --min-confidence 80
```

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](docs/CONTRIBUTING.md) first.

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt
npm install

# Run in development mode (with hot reload)
flask run --debug &
npm run dev
```

### Quick Contribution Ideas

- 🐛 Bug fixes and security patches
- 📝 Documentation improvements
- 🌐 Translations and localization
- 🧪 Additional test coverage
- 🎨 UI/UX enhancements

---

## 📄 License

Verso-Backend is released under the **MIT License**. 

You are free to:
- Use commercially
- Modify and distribute
- Use privately
- Sublicense

See [LICENSE](LICENSE) for full terms.

---

## 💖 Support the Project

If Verso saves you from the Integration Tax, consider supporting development:

- ⭐ **Star this repo** — Helps others discover Verso
- 🐛 **Report issues** — Help us improve
- 💬 **Share your story** — Tell us how Verso helped your business
- ☕ **Sponsor** — [GitHub Sponsors](https://github.com/sponsors/versoindustries)

---

## 🗺️ Roadmap

### Current Focus (v2.x)
- [x] React Islands architecture
- [x] Unified Admin Dashboard
- [x] Enterprise Messaging Platform
- [x] Theme Editor with live preview
- [ ] Advanced automation workflows
- [ ] Mobile-responsive admin UI
- [ ] Plugin/extension system

### Future (v3.x)
- [ ] GraphQL API layer
- [ ] Real-time collaboration
- [ ] AI-powered analytics
- [ ] White-label SaaS mode

See our [full roadmap](docs/roadmap.md) for details.

---

<p align="center">
  <strong>Claim your sovereignty. Ship the monolith. Sleep at night.</strong>
</p>

<p align="center">
  Made with ❤️ by <a href="https://versoindustries.com">Verso Industries</a>
</p>
