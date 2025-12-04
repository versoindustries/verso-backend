# Verso-Backend: The Sovereign Monolith Protocol

**Status:** Production-grade / Industrial use • **Philosophy:** High-agency • No-rent • Pythonic Truth

This is not a starter kit. Verso-Backend is a **Complexity Containment Field** for founders who refuse hydration errors, API overages, and venture-subsidized "serverless" roulette. It is a Python + SQL monolith that lives on commodity hardware, speaks in causal facts (SSR), and keeps every record under your roof.

## Who We Are Selecting
- Operators who optimize for **unit economics and sovereignty**, not badge-driven framework churn.
- Teams exhausted by the **Complexity Tax** of Vercel/Auth0/Contentful/Clerk/Supabase sprawl.
- Builders who want an asset that will still run in 2035, not a quarterly rewrite of App Router lore.

## Sovereign Modules (No-Rent Stack)
- **Identity & Access Core (IAC)** — Flask-Login + RBAC decorators (`auth_manager.py`) keep auth and roles in your SQL tables.
- **Sovereign Narrative Engine** — First-party blog/CMS (`routes/blog.py`, CKEditor, SQLAlchemy `Post`). No headless CMS tax.
- **Temporal Logistics Module** — FullCalendar + UTC-safe scheduling (`Appointment` model) for bookings without Calendly rent.
- **Bounded Contexts** — Blueprinted routes (`auth.py`, `admin.py`, `blog.py`, `main_routes.py`, `user.py`) give microservice clarity inside one process.
- **Asset & File Pipeline** — Local uploads and compression via `file_manager.py`; S3 later only if you choose.
- **Indexing & SEO** — Sitemaps/JSON-LD (`modules/indexing.py`) keep the corpus discoverable without SaaS middleware.

## Economic Scorecard (100k MAU, 1TB transfer)
| Layer | SaaS Stack Burn | Verso Stack |
| --- | --- | --- |
| Auth (Auth0/Clerk) | ~$1,800/mo variable | $0 (owned) |
| CMS (Contentful/Sanity) | ~$489/mo | $0 (in-repo) |
| Scheduling (Calendly Enterprise) | ~$1,250/mo | $0 (in-repo) |
| Hosting (Vercel + bandwidth) | ~$150+ uncapped | ~$5–$20 fixed VPS |
| **Total** | **~$2,400+/mo (variable risk)** | **~$20–$40/mo (fixed)** |

## Operating Principles
- **Server-Side Truth**: Jinja2 renders finished HTML; zero hydration mismatches.
- **Single Latency Domain**: All joins happen near the CPU, not across SaaS APIs.
- **Feature Freeze on Fads**: No rent-seeking dependencies; Lindy-first tech (Python, SQL, HTML).
- **Modular Monolith**: Separation by blueprints, not by Kubernetes clusters.

## Repository Layout
- `app/routes/` — auth, admin, blog, main, user blueprints.
- `app/templates/` — server-rendered pages (index, about, dashboards, blog).
- `app/models.py` — Users, Roles, Posts, Appointments, Services, Estimators, Contacts.
- `app/modules/` — auth decorators, file pipeline, indexing, role bootstrap, locations.
- `app/static/` — JS (FullCalendar, sliders), CSS, images.
- `dbl.py` — database bootstrap script.

## Local Independence (Setup)
1. Clone and enter:
   ```bash
   git clone https://github.com/versoindustries/verso-backend.git
   cd verso-backend
   ```
2. Create env + install:
   ```bash
   python3 -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   ```
3. Configure minimal `.env`:
   ```
   FLASK_APP=app
   SECRET_KEY=generate_a_secure_key
   DATABASE_URL=sqlite:///verso.sqlite
   MAIL_SERVER=smtp.example.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=you@example.com
   MAIL_PASSWORD=your_password
   MAIL_DEFAULT_SENDER=you@example.com
   ```
4. Initialize the causal core:
   ```bash
   python dbl.py
   flask db init
   flask db migrate
   flask db upgrade
   flask create-roles
   flask seed-business-config
   ```
5. Run it:
   ```bash
   flask run --host=0.0.0.0 --debug
   ```
   Visit `http://localhost:5000`.

## Deployment Playbooks
- **Sovereign Path — Raw VPS**: Ubuntu/Debian + `gunicorn`/`systemd` + Nginx. Fixed fee; air-gappable.
- **Hybrid Path — Heroku/Dokku**: Use `Procfile`; set env vars; run `flask db upgrade`, `flask create-roles`, `flask seed-business-config` post-deploy.
- **Edge Path — On-Prem/Device**: Raspberry Pi / Jetson for regulated or offline installs; identical codebase, zero third-party auth/CMS calls.

## Defaults & Roles
- Default roles: `admin`, `user`, `commercial`, `blogger`.
- Seeders: `flask create-roles` (roles), `flask seed-business-config` (timezone/hours), `dbl.py` (initial DB file if using SQLite).
- Appointment calendar uses UTC internally; see `models.py` + `calendar.js`.

## Support & Donations
If this stack saves you from the Complexity Tax, keep the lights on: [GitHub Sponsors](https://github.com/sponsors/versoindustries).

Claim your sovereignty. Ship the monolith. Sleep at night.
