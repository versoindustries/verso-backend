# Technical Roadmap: Verso-Backend Integration & Testing

> [!NOTE]
> This document was generated from deep codebase analysis on 2025-12-08.

## Executive Summary

Deep analysis of the Verso-Backend codebase revealed several integration gaps, particularly around the theme editor's incomplete connections to public-facing content, inconsistent configuration usage, and areas needing end-to-end testing.

---

## Current State Analysis

### Theme Editor Status

| Feature | Status | Notes |
|---------|--------|-------|
| Primary/Secondary/Accent Colors | ✅ Working | Saved to `BusinessConfig`, applied via CSS vars |
| Font Family | ✅ Working | Applied via `--font-family` |
| Border Radius | ✅ Working | Used in theme preview |
| GA4 Tracking ID | ✅ Working | Dynamically inserted in `<head>` |
| Logo Upload | ⚠️ Partial | Saved to `Media`, **NOT** shown in public pages |
| Site Name | ❌ Missing | Hardcoded as `"Verso Backend"` in `base.html:87` |
| Page Text/Content | ❌ Missing | Homepage text is template-hardcoded |

### Critical Integration Gaps

1. **Site Name Not Editable** - `base.html:87` hardcodes the site name
2. **Uploaded Logo Ignored** - `base.html:158` uses static file only
3. **Homepage Text Not CMS-Controlled** - Marketing copy in templates
4. **Inconsistent Config Keys** - `business_name` vs `site_name`
5. **Test Suite Errors** - 318 tests exist but fixtures have issues

---

## Implementation Phases

### Phase 1: Theme Editor Critical Fixes (2-3 hours)
- Make `site_name` dynamically configurable
- Use uploaded logo in public pages
- Consistent config key usage

### Phase 2: Content Management (4-5 hours)
- Add editable site content fields to BusinessConfig
- Update templates to use CMS content

### Phase 3: Test Infrastructure Repair (3-4 hours)
- Fix `conftest.py` fixtures
- Ensure all 318 tests pass

### Phase 4: E2E Admin Testing (4-6 hours)
- Test all admin routes manually and via automation
- Fix any discovered issues

---

## Workflow

Use `/integration-fixes` workflow to execute these phases step by step.

---

## Files to Modify

| File | Changes |
|------|---------|
| `app/templates/base.html` | Dynamic site_name, logo from Media |
| `app/__init__.py` | Add site_name to seed config |
| `app/routes/theme.py` | Add site_name field |
| `app/tests/conftest.py` | Fix fixtures |
| Various templates | Consistent config usage |
