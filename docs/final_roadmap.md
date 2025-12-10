# Verso Backend - Complete Feature & Enterprise Roadmap

**Version**: 2.0  
**Date**: December 9, 2025  
**Status**: Active Development

---

## Executive Summary

This roadmap consolidates all incomplete features, establishes template standards, redesigns the admin center, and ensures enterprise-level UX/compliance. No code is deleted - all existing assets are integrated.

### Metrics
| Metric | Count |
|--------|-------|
| Model Classes | 136 |
| Route Files | 47 |
| Admin Templates | 47 in 21 subdirectories |
| Public Templates | ~60 |
| Development Phases | 29 |
| Unintegrated Features | 12 areas |

---

## Phase Structure Overview

| Phase | Focus | Effort |
|-------|-------|--------|
| **A** | Template Migration (React Islands + Jinja2) | 40 hrs |
| **B** | Admin Center Redesign | 30 hrs |
| **C** | Theme Editor Validation | 8 hrs |
| **D** | In-Page Content/SEO Editing | 12 hrs |
| **E** | Feature Completion (from v1 roadmap) | 50 hrs |
| **F** | Codebase Organization | 16 hrs |
| **G** | Performance & OWASP/SOC2 Audit | 12 hrs |
| **H** | Testing & Automation Workflow | 8 hrs |
| **I** | Enterprise Messaging Platform | 24 hrs |
| **J** | **Comprehensive Feature Enhancement Audit** | **88 hrs** |

---

## Execution Metadata

> **Note**: This roadmap is designed for automated execution via `/full-qa` workflow. Each task has a unique ID, validation criteria, and state tracking in `docs/execution_state.md`.

### Task ID Convention
- Format: `{Phase}.{Section}.{Item}` (e.g., `A.2.3` = Phase A, Section 2, Item 3)
- Dependencies reference other task IDs
- Status tracked in `docs/execution_state.md`

### Validation Types
| Type | Description |
|------|-------------|
| `pytest` | Backend test file must pass |
| `tsc` | TypeScript compilation with no errors |
| `browser` | Visual check in browser, capture screenshot |
| `seo` | Has `<title>`, `<meta description>`, single `<h1>` |
| `theme` | Uses CSS variables, no hardcoded colors |
| `security` | Has `@login_required` or `@role_required` |
| `schema` | Has JSON-LD schema markup |

### Compliance Gates
Before advancing to next phase, ALL must pass:
- All pytest tests for modified modules
- Zero TypeScript errors in affected components
- Browser validation with no console errors
- OWASP/SOC2 compliance for security changes

---

# Phase A: Template Migration

## A.1 Template Standards

All templates must follow these standards from `docs/Grok_Prompts/`:

### Decision Framework
| Content Type | Render Method |
|--------------|---------------|
| SEO-critical text (H1, descriptions) | Jinja2 |
| Interactive tables/forms | React Island |
| Navigation/Dropdowns | React Island |
| Static feature lists | Jinja2 |
| Image galleries/carousels | React Island |
| Data visualizations | React Island |

### React Islands Pattern
```html
<div data-react-component="ComponentName"
     data-react-props='{"key": {{ value_json|safe }}}'>
    <noscript><!-- SEO fallback --></noscript>
</div>
```

### Template Checklist
- [ ] Extends `base.html`
- [ ] Uses `{% block title %}` with SEO-optimized title
- [ ] Uses `{% block description %}` for meta description
- [ ] Single `<h1>` tag on page
- [ ] All CSS classes from `base.css` variables
- [ ] Interactive elements use React Islands
- [ ] `<noscript>` fallback for critical React content

---

## A.2 Template Audit List

### Public Templates (Priority 1)
| ID | Template | Status | React Components | Validation |
|----|----------|--------|------------------|------------|
| A.2.1 | `index.html` | ✅ DONE | HomePage, Header, Footer | `browser`, `seo`, `schema` |
| A.2.2 | `booking/book.html` | ✅ DONE | BookingWizard | `browser`, `seo` |
| A.2.3 | `shop/product.html` | ✅ DONE | ProductView, ImageGallery | `browser`, `seo`, `schema` |
| A.2.4 | `shop/cart.html` | ✅ DONE | CartPage | `browser` |
| A.2.5 | `contact.html` | ⚠️ AUDIT | None (form) | `browser`, `seo` |
| A.2.6 | `services.html` | ⚠️ AUDIT | None | `browser`, `seo` |
| A.2.7 | `blog/post.html` | ⚠️ AUDIT | BlogPostUtils | `browser`, `seo`, `schema` |
| A.2.8 | `aboutus.html` | ❌ TODO | Review needed | `browser`, `seo` |

### Admin Templates (Priority 2)
| ID | Template Area | Count | React Components | Validation |
|----|---------------|-------|------------------|------------|
| A.3.1 | Dashboard | 4 | AdminDashboard, KPICard, Chart | `browser`, `security` |
| A.3.2 | CRM | 6 | KanbanBoard, AdminDataTable | `browser`, `security` |
| A.3.3 | Shop | 7 | AdminDataTable | `browser`, `security` |
| A.3.4 | Email | 12 | EmailTemplateCards, AdminDataTable | `browser`, `security` |
| A.3.5 | Analytics | 10 | AnalyticsDashboard, Chart | `browser`, `security` |
| A.3.6 | Forms | 5 | FormBuilder (new) | `browser`, `security` |
| A.3.7 | Scheduling | 6 | AdminCalendar, AdminDataTable | `browser`, `security` |
| A.3.8 | Reports | 8 | Chart, AdminDataTable | `browser`, `security` |

---

# Phase B: Admin Center Redesign

## B.1 Current Issues
- Fragmented navigation (21 subdirectories)
- Inconsistent layouts across admin pages
- No unified dashboard with quick actions
- Complex multi-step workflows

## B.2 Redesign Goals
1. **Single Dashboard Hub** - All key metrics at a glance
2. **Collapsible Sidebar** - Categorized navigation
3. **Quick Actions** - Most common tasks one click away
4. **Consistent Table Pattern** - All lists use `AdminDataTable`
5. **Inline Editing** - Edit without full page navigation

## B.3 New Admin Structure

```
/admin/dashboard          → Main hub with KPIs
├── Quick Actions Panel
│   ├── New Lead
│   ├── New Order
│   ├── New Blog Post
│   └── View Messages
├── KPI Cards Row
│   ├── Revenue Today
│   ├── New Leads
│   ├── Pending Orders
│   └── Site Traffic
├── Recent Activity Feed
└── Alerts/Notifications

/admin/crm               → CRM dashboard
/admin/shop              → E-commerce dashboard  
/admin/content           → Blog/Pages dashboard
/admin/communications    → Email/SMS/Push dashboard
/admin/scheduling        → Appointments dashboard
/admin/analytics         → Full analytics
/admin/settings          → System configuration
```

## B.4 Admin Component Map

| Section | React Components |
|---------|------------------|
| Dashboard | `AdminDashboard`, `KPICard`, `Chart`, `NotificationBell` |
| CRM | `KanbanBoard`, `AdminDataTable` |
| Shop | `AdminDataTable`, `Chart` |
| Content | `AdminDataTable`, Editor (TinyMCE) |
| Communications | `EmailTemplateCards`, `AdminDataTable` |
| Scheduling | `AdminCalendar`, `AdminDataTable` |
| Analytics | `AnalyticsDashboard`, `Chart` |

---

# Phase C: Theme Editor Validation

## C.1 Current Theme System

**Primary Theme File**: `app/static/css/theme-variables.css`

```css
:root {
    --primary-color: #4169e1;      /* Main brand color */
    --secondary-color: #6c757d;    
    --accent-color: #28a745;
    /* 20+ derived variables */
}
```

## C.2 Theme Editor Requirements

1. **Color Variables** - All templates must use CSS variables, not hardcoded colors
2. **Live Preview** - Changes visible instantly
3. **Persistence** - Save to `BusinessConfig` model
4. **Template Audit** - Verify all templates reference variables

## C.3 Validation Tasks

- [ ] Audit all CSS files for hardcoded colors
- [ ] Replace with `var(--primary-color)` or derived variants
- [ ] Test theme editor changes propagate to all pages
- [ ] Verify React components read theme variables
- [ ] Document theme variable usage

### Files Using Theme Variables (Current)
- `theme-variables.css` (source)
- `components/theme-editor.css`
- `components/components.css`
- Need to audit: `admin-dashboard.css`, others

---

# Phase D: In-Page Content/SEO Editing

## D.1 Requirements

1. **Edit Mode Toggle** - Admin and Marketing users see "Edit" button on pages, and employee role has access to writing blog posts.
2. **Inline Text Editing** - Click to edit H1, paragraphs
3. **SEO Sidebar** - Edit title, meta description, og tags
4. **Save to Database** - Persist via AJAX to `Page` or `Post` model

## D.2 Implementation

### Frontend (React)
```tsx
// InlineEditor component
<div data-react-component="InlineEditor"
     data-react-props='{"pageId": {{ page.id }}, "canEdit": {{ current_user.is_admin|tojson }}}'>
</div>
```

### Backend (Flask)
```python
@bp.route('/api/page/<int:id>/content', methods=['PATCH'])
@role_required('Admin')
def update_page_content(id):
    # Update Page model fields
    # Update SEO fields
```

## D.3 Pages Requiring In-Page Editing
- All `Page` model pages
- Blog posts (`Post` model)
- Product descriptions
- Landing pages

---

# Phase E: Feature Completion (from v1)

## Priority 1: E-Commerce
- [ ] `ProductVariant` integration with shop routes
- [ ] `DiscountRule` engine in checkout
- [ ] `ProductImage` gallery

## Priority 2: Media Management
- [ ] Wire `file_manager.py` into routes
- [ ] `compress_image()` integration

## Priority 3: Analytics
- [ ] `ReportExport` model integration
- [ ] Scheduled report generation

## Priority 4: Communication
- [ ] SMS admin routes (`SMSTemplate`, `SMSConsent`)
- [ ] Push notification delivery

## Priority 5: Automation
- [ ] `WorkflowStep` execution handlers
- [ ] Event triggers

---

# Phase F: Codebase Organization

## F.1 Split models.py (4,496 lines → 10 files)

```
app/models/
├── __init__.py
├── user.py           # User, Role
├── scheduling.py     # Appointment, Availability
├── ecommerce.py      # Product, Order, Cart
├── crm.py            # Lead, Pipeline
├── blog.py           # Post, Comment
├── messaging.py      # Channel, Message
├── analytics.py      # PageView, Session
├── forms.py          # FormDefinition
└── infrastructure.py # Task, Worker
```

## F.2 Route Organization

```
app/routes/
├── public/           # Customer-facing
├── api/              # REST endpoints
├── admin/            # Admin dashboard
└── employee/         # Employee portal
```

---

# Phase G: Performance & Compliance Audit

## G.1 OWASP Top 10 Checklist
- [ ] SQL Injection: SQLAlchemy ORM only
- [ ] XSS: Jinja2 autoescape + bleach for HTML
- [ ] CSRF: Flask-WTF on all forms
- [ ] Access Control: `@role_required` on all admin routes
- [ ] Cryptography: Secrets in env vars only
- [ ] Logging: No PII in logs

## G.2 SOC2 Checklist
- [ ] Change management: All schema via migrations
- [ ] Access control: RBAC enforced
- [ ] Data privacy: PII handling documented
- [ ] Audit logs: All admin actions logged

## G.3 Performance Tasks
- [ ] Enable query logging for slow queries
- [ ] Add Redis caching for frequent queries
- [ ] Lazy load React Islands
- [ ] Minify CSS/JS in production

---

# Phase H: Automated Testing Workflow

## H.1 Workflow File

Create `.agent/workflows/full-qa.md`:

```markdown
---
description: Complete QA workflow with browser testing
---

# Full QA Workflow

## Prerequisites
// turbo-all

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   npm install
   ```

2. Build frontend assets
   ```bash
   npm run build
   ```

3. Run database migrations
   ```bash
   flask db upgrade
   ```

## Automated Tests

4. Run pytest suite
   ```bash
   pytest app/tests/ -v --tb=short
   ```

5. Run TypeScript type check
   ```bash
   npx tsc --noEmit
   ```

6. Run dead code detection
   ```bash
   vulture app/ --min-confidence 80
   ```

## Browser Testing

7. Start Flask server in background
   ```bash
   flask run --host=0.0.0.0 &
   ```

8. Wait for server to start
   ```bash
   sleep 3
   ```

9. Open browser and test pages
   - Navigate to http://localhost:5000
   - Verify homepage loads
   - Navigate to /admin/dashboard
   - Verify admin loads with login
   - Navigate to /booking
   - Verify booking wizard loads
   - Check console for JavaScript errors

10. Stop server
    ```bash
    pkill -f "flask run"
    ```

## Completion
Report any failures to the user with screenshots.
```

## H.2 Launch Instructions

To launch the workflow:

```bash
# In your agent session, use the slash command:
/full-qa
```

Or manually:
1. Open the workflow file
2. Agent follows each step sequentially
3. Browser tests validate visual rendering
4. Any failures reported with evidence

---

# Phase I: Enterprise Messaging Platform

## I.1 Current State

**Existing Models** (from `app/models.py`):
- `Channel` (line 735) - public/private/direct types
- `Message` (line 770) - with threading support
- `ChannelMember` (line 804) - read receipts
- `MessageReaction` (line 829) - emoji reactions

**Existing Routes** (`app/routes/messaging.py`):
- Channel CRUD, DMs, @mentions
- Message sending, polling
- Reactions, member management
- Archive/unarchive

## I.2 Enhancement Goals

Transform internal messaging into enterprise-grade communication platform:

### Channel Types (Expanded)
| Type | Visibility | Use Case |
|------|------------|----------|
| `internal` | Employees only | Team communication |
| `support` | Staff + assigned customer | Customer support tickets |
| `public` | All registered users | Community/announcements |
| `customer_private` | Business + specific customer | Account-specific discussions |
| `group` | Invited members only | Project teams |

### Key Features to Add
1. **Customer-facing channels** (optional per business)
2. **Database data referencing** in messages
3. **Rich message formatting** (markdown, code blocks)
4. **File attachments** with preview
5. **Typing indicators** (WebSocket)
6. **Real-time updates** (WebSocket/SSE)
7. **Message search** with filters
8. **Channel categories** for organization

## I.3 Data Reference System

### Slash Commands for Data Lookup
Employees/admins can reference database records inline:

```
/order #12345        → Embeds Order card with status, items, total
/contact #789        → Embeds Contact form submission details
/appointment #456    → Embeds Appointment card with date/time/service
/product SKU-001     → Embeds Product card with price/inventory
/user @username      → Links to user profile
/lead #123           → Embeds Lead card with pipeline stage
```

---

# Phase J: Comprehensive Feature Enhancement Audit

> **This phase systematically reviews EVERY feature in the codebase** and applies enterprise-level enhancements: intuitive UX, world-class design, streamlined workflows, and data integration. We are looking to streamline workflows and offer a system no one else has internally. Think out of the box for useful on features.

## J.1 Audit Methodology

For EACH feature area, perform:

1. **Current State Analysis** - What exists, what's incomplete
2. **Enterprise Gap Analysis** - What's missing for enterprise-level
3. **UX/UI Enhancement** - Apply world-class design theory
4. **Data Integration** - Connect to relevant models/embeds
5. **Workflow Streamlining** - Reduce clicks, consolidate views
6. **Template Compliance** - Jinja2 + React Islands pattern
7. **Theme Compliance** - All CSS uses `--primary-color` variables

## J.2 Feature Audit Checklist

### Authentication & User Management
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Login/Register | `auth.py`, `login.html` | ✅ Social login, MFA, enterprise SSO option |
| Password Reset | `auth.py` | Security hardening, rate limiting |
| User Profiles | `user.py` | Avatar upload, preferences panel |
| Role Management | `admin.py` | Granular permissions UI |
| Onboarding | `onboarding.py` | Progressive disclosure, guided tours |

### Scheduling & Booking
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Booking Wizard | `booking/*.py` | Multi-service, group booking |
| Calendar View | `calendar.py` | Drag-drop rescheduling, conflict detection |
| Availability | `availability_service.py` | Buffer times, break management |
| Estimators | `estimator_form.html` | Link to User accounts, skills matrix |
| Recurring Appointments | `scheduling.py` | Pattern editor, exception handling |
| Resources | `scheduling.py` | Room/equipment booking integration |

### E-Commerce
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Product Catalog | `shop.py` | Variants, attributes, image gallery |
| Cart | `cart.py` | Real-time inventory, save for later |
| Checkout | `ecommerce.py` | Address autocomplete, tax calculation |
| Orders | `orders_admin.py` | Fulfillment workflow, status pipeline |
| Discounts | `ecommerce_admin.py` | Rule builder, automatic application |
| Gift Cards | `ecommerce_admin.py` | Balance display, redemption history |
| Shipping | `ecommerce_admin.py` | Rate calculator, carrier integration |

### CRM & Leads
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Lead Pipeline | `crm.py` | Kanban with automation triggers |
| Contact Management | `crm.py` | Merge duplicates, timeline view |
| Lead Scoring | Models exist | Implement scoring rules engine |
| Activity Tracking | `UserActivity` | Unified timeline across all actions |
| Notes & Attachments | `crm.py` | Rich text, file attachments |

### Blog & Content
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Post Editor | `blog.py` | WYSIWYG with media library |
| Categories/Tags | `blog.py` | Bulk management, SEO suggestions |
| Comments | `blog.py` | Moderation queue, spam detection |
| Pages | `pages.py` | In-page editing, version history |
| Media Library | `media.py` | Gallery view, bulk upload, compression |

### Communications
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Email Templates | `email_admin.py` | Visual builder, variable preview |
| Email Campaigns | `email_admin.py` | A/B testing, scheduling |
| SMS Templates | ❌ Create routes | TCPA compliance, segment preview |
| Push Notifications | `push.py` | Targeting rules, analytics |
| Messaging Hub | `messaging.py` | **See Phase I details** |

### Forms & Data Collection
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Form Builder | `forms_admin.py` | Drag-drop fields, conditional logic |
| Submissions | `forms_admin.py` | Export, filtering, charts |
| Surveys | `surveys/` | Response analytics, NPS tracking |
| Contact Forms | `contact.py` | Auto-lead creation, notifications |

### Analytics & Reporting
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Dashboard | `analytics.py` | Real-time metrics, drill-down |
| Reports | `reports.py` | Scheduled generation, export formats |
| Page Views | `PageView` model | Funnel analysis, path tracking |
| Conversion Tracking | `analytics.py` | Attribution models |
| Custom Reports | `SavedReport` | Builder UI, sharing |

### Automation & Workflows
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Workflow Builder | `automation.py` | Visual flow editor |
| Triggers | `automation.py` | Event-based, scheduled, conditional |
| Actions | `WorkflowStep` | Email, SMS, task creation, webhook |
| Execution Log | `automation.py` | Debug view, retry failed |

### Employee Portal
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Leave Requests | `employee.py` | Calendar integration, approval workflow |
| Time Tracking | `TimeEntry` | Timer widget, project allocation |
| Documents | `EncryptedDocument` | Secure viewer, download tracking |
| Directory | `employee.py` | Org chart, skills search |

### Admin Center
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Dashboard | `dashboard.html` | KPI cards, quick actions, activity feed |
| Navigation | All admin | Collapsible sidebar, search |
| Settings | `business_config.html` | Categorized tabs, validation |
| Theme Editor | `theme_editor.html` | Live preview, preset themes |
| API Keys | `list_api_keys.html` | Usage stats, rate limit display |
| Audit Logs | `audit_logs.html` | Filter by user/action, export |

### Support & Ticketing
| Feature | File(s) | Enhancement Tasks |
|---------|---------|-------------------|
| Ticket System | `support.py` | Priority, SLA, assignment |
| Knowledge Base | ❌ Create | Article editor, search |
| Live Chat | ❌ Consider | WebSocket, agent routing |

## J.3 Per-Feature Enhancement Template

For each feature, apply this analysis:

```markdown
### [Feature Name]

**Current State:**
- Routes: [list files]
- Models: [list models]
- Templates: [list templates]

**Enterprise Gaps:**
- [ ] Missing functionality
- [ ] UX friction points
- [ ] Design inconsistencies
- [ ] Data not connected

**UX Enhancements:**
- [ ] Reduce clicks for common actions
- [ ] Add keyboard shortcuts
- [ ] Implement inline editing
- [ ] Add bulk operations

**Design Enhancements:**
- [ ] Apply glassmorphism cards
- [ ] Use theme variables
- [ ] Add micro-animations
- [ ] Ensure mobile responsive

**Data Integration:**
- [ ] Reference related records
- [ ] Add activity timeline
- [ ] Show contextual data

**Template Compliance:**
- [ ] Extends base.html
- [ ] Uses React Islands for interactivity
- [ ] Has SEO meta tags
- [ ] Follows Grok_Prompts patterns
```

## J.4 Implementation Order

| Week | Features to Audit |
|------|-------------------|
| 1 | Authentication, User Management |
| 2 | Scheduling, Booking |
| 3 | E-Commerce (Products, Cart, Checkout) |
| 4 | E-Commerce (Orders, Discounts, Shipping) |
| 5 | CRM, Leads |
| 6 | Blog, Content, Media |
| 7 | Communications (Email, SMS, Push) |
| 8 | Forms, Surveys, Analytics |
| 9 | Automation, Workflows |
| 10 | Employee Portal, Admin Center |
| 11 | Support, Final Integration |

## J.5 Success Metrics

| Metric | Target |
|--------|--------|
| Features audited | 100% |
| Enterprise gaps closed | 90%+ |
| Templates on React Islands | 100% |
| Theme variable compliance | 100% |
| UX improvements per feature | 3+ |
| Reduced clicks for common workflows | 30%+ |

## Notes

- Go all out on this build, no holding back. Make sure everything is integrated. The goal is for eccommerce to be an enabled feature, think that's done but it needs documented fully. Most people won't need that feature, everything else is fully viable. Make sure that the booking form editor for admins has the ability to integrate payment based bookings that integrate with stripe. Stripe is also what we will use for payment processing upfront for the ecommerce end as well. We don't want redis or any 3rd party integrations for the backend if we can help it. Make sure you update all documentation for the new features and make sure to update the documenation for usage and development in the docs folder. 

---

# Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | A | Template migration (public) |
| 3 | A | Template migration (admin) |
| 4 | B | Admin dashboard redesign |
| 5 | B | Admin navigation/workflows |
| 6 | C, D | Theme validation, in-page editing |
| 7-8 | E | Feature completion |
| 9 | F | Codebase reorganization |
| 10 | G, H | Audit, testing workflow |
| 11-12 | I | Enterprise messaging platform |

---

# Success Criteria

| Metric | Target |
|--------|--------|
| Templates with React Islands | 100% |
| Theme variable compliance | 100% |
| Admin pages using AdminDataTable | 100% |
| Pytest passing | 100% |
| TypeScript errors | 0 |
| OWASP checklist | 100% |
| SOC2 checklist | 100% |
