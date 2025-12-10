# AGENTS: Verso-Backend

## Mission
Give agents a fast way to spin up, extend, and harden the Verso Flask monolith + React Islands. Complete all unfinished features following the priority roadmap, maintain SOC2/OWASP compliance, and organize the codebase for maintainability.

## Stack & Layout
- **Backend**: Python 3.10.11, Flask App Factory (`app/__init__.py`).
- **Frontend**: React 18, TypeScript, Vite. React "Islands" mounted in Jinja2 templates via `app/templates` and `app/static/src`.
- **Data**: SQLAlchemy + Flask-Migrate. SQLite (`verso.sqlite`) / Postgres.
- **Structure**:
  - Blueprints: `app/routes/` (47 route files)
  - Models: `app/models.py` (136 classes, 4,496 lines - see reorganization plan)
  - Helpers: `app/modules/` (35 modules)
  - React Entry: `app/static/src/` (configured in `vite.config.js`)
- **Config**: `app/config.py` and `.env`.

## Feature Completion Roadmap
**Reference**: See `final_roadmap.md` for complete implementation details (v2.0).

### Phase Overview
| Phase | Focus |
|-------|-------|
| A | Template Migration (React Islands + Jinja2) |
| B | Admin Center Redesign |
| C | Theme Editor Validation |
| D | In-Page Content/SEO Editing |
| E | Feature Completion |
| F | Codebase Organization |
| G | Performance & OWASP/SOC2 Audit |
| H | Testing & Automation Workflow |
| I | Enterprise Messaging Platform |
| J | Comprehensive Feature Enhancement Audit |

### Launch QA Workflow
```bash
# Use the slash command to run full QA:
/full-qa
```

This runs:
- pytest test suite
- TypeScript type checking
- Dead code detection (vulture)
- Browser testing with screenshots

### Priority Features to Complete
- `ProductVariant` integration (E-commerce)
- `DiscountRule` engine (checkout)
- `file_manager.py` integration (media)
- `SMSTemplate`/`SMSConsent` routes (communications)
- `WorkflowStep` execution handlers (automation)

## Models Reference
The following models exist but need route integration:
- `ProductVariant` (line 1591) - E-commerce variants
- `ProductImage` (line 2156) - Product gallery
- `DiscountRule` (line 2254) - Discount conditions
- `ReportExport` (line 2793) - Saved reports
- `SMSTemplate` (line 3174) - SMS marketing
- `SMSConsent` (line 3227) - TCPA compliance
- `WorkflowStep` (line 1924) - Automation actions


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
- **Broken Access Control**: Ensure every route has `@login_required` or `@role_required(...)` unless explicitly public. Verify ownership of resources before access.
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
- **Dead Code**: Run `vulture app/ --min-confidence 80` to check for unused code.

## Useful Commands
```bash
flask db migrate -m "message"
flask db upgrade
npm run build
pytest
vulture app/ --min-confidence 80  # Dead code detection
```

## Codebase Organization (Future)
When feature completion reaches 90%, reorganize:
1. Split `models.py` into domain modules (`models/ecommerce.py`, `models/crm.py`, etc.)
2. Group routes into `routes/public/`, `routes/admin/`, `routes/api/`
3. Consolidate modules into `modules/services/`, `modules/integrations/`

See `final_roadmap.md` for detailed organization plan.
