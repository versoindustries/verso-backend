# AGENTS: Verso-Backend

## Mission
Give agents a fast way to spin up, extend, and harden the Verso Flask monolith + React Islands without breaking sovereignty, omitting compliance checks, or shipping untested changes.

## Stack & Layout
- **Backend**: Python 3.10.11, Flask App Factory (`app/__init__.py`).
- **Frontend**: React 18, TypeScript, Vite. React "Islands" mounted in Jinja2 templates via `app/templates` and `app/static/src`.
- **Data**: SQLAlchemy + Flask-Migrate. SQLite (`verso.sqlite`) / Postgres.
- **Structure**:
  - Blueprints: `app/routes/` (auth, admin, blog, main, user)
  - Models: `app/models.py`
  - Helpers: `app/modules/`
  - React Entry: `app/static/src/` (configured in `vite.config.js` and `package.json`)
- **Config**: `app/config.py` and `.env`.

## Local Setup
1. **Backend**:
   ```bash
   python3 -m venv env && source env/bin/activate && pip install -r requirements.txt
   # Setup .env (see README)
   python dbl.py
   flask db upgrade
   flask create-roles
   flask seed-business-config
   ```
2. **Frontend**:
   ```bash
   npm install
   npm run build  # or npm run dev for HMR
   ```
3. **Run**:
   ```bash
   flask run --host=0.0.0.0 --debug
   ```

## Compliance Directives (SOC2 & OWASP)
**CRITICAL**: All changes must adhere to the following security and compliance standards.

### OWASP Top 10 (Security)
- **Injection**: Use SQLAlchemy ORM for all queries. Sanitize all other inputs.
- **Broken Access Control**: Ensure every route has `@login_required` or `@role_required(...)` unless explicitly public. verify ownership of resources before access.
- **XSS**: Jinja2 auto-escapes by default. For React, avoid `dangerouslySetInnerHTML`; use `bleach` for allowed HTML if necessary.
- **Cryptographic Failures**: Never store secrets in code. Use env vars.
- **Logging**: Log security events (login/fail, sensitive access) but **NEVER** log credentials or PII.

### SOC2 (Process & Privacy)
- **Change Management**: All schema changes must be migrated (`flask db migrate`). No ad-hoc SQL.
- **Access Control**: Respect Role-Based Access Control (RBAC). Use defined roles (Admin, Manager, User).
- **Data Privacy**: Treat user data as sensitive. Do not expose PII in logs or error messages.

## Testing & QA
- **Automated**: Run `pytest` for backend coverage. React components should be type-checked (`tsc`).
- **Manual**: Verify auth flows, role boundaries, and "Happy Path" for new features.

## Useful Commands
```bash
flask db migrate -m "message"
flask db upgrade
npm run build
pytest
```
