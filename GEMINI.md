# AGENTS: Verso-Backend

## Mission
Give agents a fast way to spin up, extend, and harden the Verso Flask monolith without breaking sovereignty or shipping untested changes.

## Stack & Layout
- Python 3.10.11, Flask app factory in `app/__init__.py` (creates the app used by `run.py` and `flask --app app run`).
- Data layer: SQLAlchemy + Flask-Migrate; default SQLite via `dbl.py`, Postgres via `DATABASE_URL` (psycopg2-binary is installed).
- Blueprints live in `app/routes/` (auth, admin, blog, main, user); models in `app/models.py`; helpers in `app/modules/`; templates/static under `app/templates/` and `app/static/`.
- Config comes from env vars in `app/config.py` and `.env`; mail via Flask-Mail; auth via Flask-Login + RBAC decorators.
- Docs worth skimming: `README.md` for setup, `docs/System Instructions for Verso-Backend Contributors.markdown` for coding standards, `docs/enhancement-roadmap.md` for future work.

## Local Setup
1. `python3 -m venv env && source env/bin/activate && pip install -r requirements.txt`
2. Create `.env` (example):
   ```
   FLASK_APP=app
   SECRET_KEY=replace_me
   DATABASE_URL=sqlite:///verso.sqlite
   MAIL_SERVER=smtp.example.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=you@example.com
   MAIL_PASSWORD=your_password
   MAIL_DEFAULT_SENDER=you@example.com
   ```
3. Bootstrap DB (SQLite path is `verso.sqlite`): `python dbl.py`; first-time migrations `flask db init`; ongoing `flask db migrate -m "msg"` + `flask db upgrade`.
4. Seed basics when needed: `flask create-roles` then `flask seed-business-config`.
5. Run dev server: `flask run --host=0.0.0.0 --debug` (or `python run.py`; honors `PORT`).

## Testing & QA
- No automated suite yet (`app/tests/` holds a placeholder). Add pytest-based tests for routes, models, and forms before merging meaningful changes.
- For manual QA: exercise auth flows, blog CRUD, appointment scheduling/calendar UTC handling, and file uploads (see `modules/file_manager.py`).

## Coding Standards
- Follow PEP 8, include docstrings, and keep templates extending `base.html`. Sanitize user content (CKEditor + `bleach`) and keep CSRF enabled.
- Use migrations for schema changes; do not edit the SQLite file directly. Keep seeds aligned with new roles/config.
- Never commit secrets; prefer env vars. Keep mail and DB credentials out of code and logs.
- Prefer `rg` for searching; keep new dependencies lean and Lindy-friendly.

## Useful Commands
```
flask db migrate -m "message"
flask db upgrade
flask create-roles
flask seed-business-config
```
