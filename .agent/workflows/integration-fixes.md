---
description: Fix theme editor integration gaps and run E2E tests on admin interface
---
# Integration Fixes Workflow

This workflow addresses discovered integration issues and validates fixes through E2E testing.

## Prerequisites
// turbo
1. Ensure venv is activated: `source env/bin/activate`
2. Ensure Flask server is running: `flask run --debug`

## Phase 1: Check for url_for Bugs
// turbo
1. Search for leading space issues:
   ```bash
   grep -r "url_for(' " app/templates/
   ```
2. If found, fix with sed:
   ```bash
   find app/templates -name "*.html" -exec sed -i "s/url_for(' /url_for('/g" {} \;
   ```

## Phase 2: Validate Base Template
1. Check `base.html` for Jinja2 corruption:
   - CSS `:root` block should have single-line `{{ business_config.get(...) }}`
   - JS `window.versoContext` should have no spaces in `{{ }}`
2. Verify `window.versoContext` is defined in browser console

## Phase 3: Theme Editor Validation
1. Navigate to `/admin/theme`
2. Verify these fields are present and functional:
   - Site Name input
   - Color pickers (primary, secondary, accent)
   - Font family dropdown
   - Logo upload area
   - Save button
3. Change primary color, save, verify it appears on homepage

## Phase 4: E2E Admin Testing
1. Create test admin if needed:
   ```python
   from app import create_app, db
   from app.models import User, Role
   app = create_app()
   with app.app_context():
       user = User(username='testadmin', email='admin@example.com', password='admin123')
       admin_role = Role.query.filter_by(name='admin').first()
       user.roles.append(admin_role)
       user.confirmed = True
       db.session.add(user)
       db.session.commit()
   ```
2. Login with admin@example.com / admin123
3. Test these routes:
   - [ ] `/admin/dashboard` - Dashboard with KPIs
   - [ ] `/admin/theme` - Theme editor
   - [ ] `/admin/users` - User management
   - [ ] `/admin/appointments` - Appointments calendar
   - [ ] `/admin/crm/leads` - CRM leads

## Phase 5: Run Test Suite
// turbo
1. Execute full test suite:
   ```bash
   python -m pytest app/tests/ -v --tb=short
   ```

## Common Issues

### BuildError: Could not build url for endpoint ' xxx'
- Cause: Leading space in url_for endpoint name
- Fix: `sed -i "s/url_for(' /url_for('/g" <file>`

### React Islands Not Rendering
- Check browser console for `versoContext undefined`
- Inspect `base.html` for corrupted Jinja2 syntax in `{{ }}` blocks

### 429 Too Many Requests
- Check rate limiter settings in `app/modules/security.py`
- Adjust `MAX_FAILED_LOGIN_ATTEMPTS` or similar

### Login Shows "Invalid email address"
- Verify user exists: `User.query.filter_by(email='...').first()`
- Ensure `confirmed=True`
- Clear failed login attempts: `LoginAttempt.query.filter_by(email='...').delete()`
