# Verso-Backend Operations Manual

**Protocol:** Sovereign Monolith • **Mission:** End the Complexity Tax • **Stack:** Flask + SQLAlchemy + Jinja2

This document is written for high-agency operators who want a fixed-cost, causally consistent web platform. It reframes the codebase as a set of **modules of sovereignty**, not a pile of features.

## Who This Selects
- Founders/CTOs done paying rent to Auth0/Contentful/Clerk/Vercel.
- Teams that prefer Python/SQL truth over hydration roulette.
- Builders who need linear operating costs on commodity VPS hardware.

## Modules of Sovereignty
- **Identity & Access Core (IAC)** — Flask-Login, RBAC decorators in `app/modules/auth_manager.py`; owns users/roles in SQL.
- **Sovereign Narrative Engine** — Blog/CMS via `app/routes/blog.py` + CKEditor + `Post` model. No headless CMS bills.
- **Temporal Logistics Module** — Appointment booking with FullCalendar, UTC normalization in `Appointment` model.
- **Bounded Contexts** — Blueprints (`auth.py`, `admin.py`, `blog.py`, `main_routes.py`, `user.py`) give service clarity without the microservice tax.
- **Asset & File Pipeline** — `app/modules/file_manager.py` for uploads/compression; swap to S3 later if you choose.
- **Indexing & SEO** — `app/modules/indexing.py` builds sitemaps/JSON-LD.

## Directory Signal
- `app/` — core application
  - `routes/` — blueprints listed above
  - `templates/` — server-rendered pages (index, about, dashboards, blog)
  - `static/` — JS (`calendar.js`, `slider.js`), CSS, images
  - `models.py` — `User`, `Role`, `Appointment`, `Service`, `Estimator`, `Post`, `ContactFormSubmission`
  - `forms.py` — WTForms for auth, estimate requests, posts
  - `modules/` — auth decorators, indexing, file pipeline, role bootstrap, locations
  - `config.py`, `database.py`, `extensions.py`, `__init__.py`
- `dbl.py` — SQLite bootstrap helper
- `Procfile` — Heroku/Dokku entrypoint
- `run.py` — dev server entry

## Environment Contract (`.env` minimum)
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

## Boot Sequence (Local Independence)
1. Clone & enter
   ```bash
   git clone https://github.com/versoindustries/verso-backend.git
   cd verso-backend
   ```
2. Virtualenv + deps
   ```bash
   python3 -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   ```
3. Initialize database + roles
   ```bash
   python dbl.py               # optional SQLite scaffold
   flask db init
   flask db migrate
   flask db upgrade
   flask create-roles          # admin, user, commercial, blogger
   flask seed-business-config  # timezone/hours defaults
   ```
4. Run
   ```bash
   flask run --host=0.0.0.0 --debug
   ```
   Visit `http://localhost:5000`.

## Deployment Runbooks
- **Sovereign Path (VPS)**: Ubuntu/Debian + `gunicorn` + `systemd` + Nginx. Fixed monthly fee, air-gap capable. Run the same migrations/seeders as local.
- **Hybrid Path (Heroku/Dokku)**: Use `Procfile`; set env vars; after deploy run `flask db upgrade`, `flask create-roles`, `flask seed-business-config`.
- **Edge Path (On-Prem / Device)**: Raspberry Pi / Jetson. Same commands, zero third-party auth/CMS calls.

## Operational Notes
- **Timezone Safety**: Appointments stored in UTC; `calendar.js` applies business hours from seeded config.
- **RBAC**: Decorators in `auth_manager.py` enforce `admin_required`, etc.; roles created via `flask create-roles`.
- **Templates**: All views extend `base.html`; meta tags already wired for SEO. Keep SSR; avoid client-side hydration.
- **Assets**: Uploads handled locally via `file_manager.py`. Swap storage by adapting that module.
- **Testing**: Use pytest/Flask testing; ensure migrations run cleanly before merge.

## Support & Donations
If this repo reduced your cloud burn or cognitive load, you can keep it sustainable via [GitHub Sponsors](https://github.com/sponsors/versoindustries).

## Call to Action
Ship the monolith. Pay fixed costs. Sleep through DDoS headlines.
