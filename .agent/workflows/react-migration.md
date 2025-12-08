---
description: Continue React template migration (Phase 18.3+)
---

# React Template Migration Workflow

## Quick Start
1. Check current progress in the **Template Migration Status** section below
2. Pick the next uncompleted template from the appropriate priority tier
3. Follow the relevant **Migration Pattern** for that template type
4. Update the checkbox in this file after successful migration
5. Run `npm run build` to verify

> **⚠️ IMPORTANT: No Tailwind CSS**  
> This project uses 100% custom CSS. All styling is done section-by-section with BEM-style class names.  
> Layout CSS files: `layout-header.css`, `layout-footer.css`, `layout-navigation.css`, `homepage-layout.css`  
> Component CSS files are in `app/static/css/components/`

---

## Migration Patterns

### Pattern A: AdminDataTable (List/Table Views)
Use for: Simple data tables with search, sort, pagination, bulk actions

```bash
# Steps:
# 1. Update Flask route to serialize data as JSON
# 2. Update template with React mount point
# 3. Build and verify
```

**Flask Route Pattern:**
```python
from flask import render_template
import json

@bp.route('/admin/example')
def example_list():
    items = Model.query.all()
    items_json = json.dumps([{
        'id': item.id,
        'name': item.name,
        'actions': f'<a href="/admin/example/{item.id}">Edit</a>'
    } for item in items])
    return render_template('admin/example.html', items_json=items_json)
```

**Template Pattern:**
```html
<div data-react-component="AdminDataTable"
     data-react-props='{
       "columns": {{ columns_json|safe }},
       "data": {{ items_json|safe }},
       "bulkActions": [{"value": "delete", "label": "Delete"}]
     }'>
</div>
```

// turbo
**Verify:** `npm run build`

---

### Pattern B: Custom Interactive Component
Use for: Specialized functionality (calendars, wizards, kanban, charts)

1. Create component in `app/static/src/components/features/<category>/`
2. Create CSS in `app/static/css/components/<component>.css`
3. Register in `app/static/src/registry.ts`
4. Import CSS in `app/static/css/components/index.css`
5. Update Flask route to pass JSON props
6. Update template with React mount point
// turbo
7. Run `npm run build`

---

### Pattern C: Keep Jinja2
Skip migration for: Forms, static pages, email templates, one-off pages

---

## Key Files Reference

| Purpose | Path |
|---------|------|
| Component Registry | `app/static/src/registry.ts` |
| Feature Components | `app/static/src/components/features/` |
| UI Components | `app/static/src/components/ui/` |
| Component CSS | `app/static/css/components/` |
| CSS Index | `app/static/css/components/index.css` |
| API Utilities | `app/static/src/api.ts` |
| Toast API Hook | `app/static/src/hooks/useToastApi.ts` |

---

## Template Migration Status

### Legend
- ✅ = Migrated to React
- ⏳ = Pending migration
- ➖ = Skip (keep Jinja2)

---

### TIER 1: Core & Public (Priority: HIGH)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `base.html` | Toast, ShoppingCartWidget, NotificationBell | Global layout |
| ✅ | `index.html` | ImageGallery | Homepage |
| ✅ | `booking/book.html` | BookingPage | Booking wizard |
| ➖ | `login.html` | - | Auth form |
| ➖ | `register.html` | - | Auth form |
| ➖ | `aboutus.html` | - | Static content |
| ➖ | `accessibility.html` | - | Static content |
| ➖ | `contact.html` | - | Contact form |
| ➖ | `services.html` | - | Static content |
| ➖ | `page.html` | - | CMS pages |
| ⏳ | `booking/index.html` | TBD | Booking landing |

---

### TIER 2: Shop & E-commerce (Priority: HIGH)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `shop/cart.html` | CartPage | Cart view |
| ✅ | `shop/product.html` | ProductView | Product detail |
| ⏳ | `shop/index.html` | TBD | Shop listing |
| ⏳ | `shop/wishlist.html` | TBD | Wishlist |
| ⏳ | `shop/reviews.html` | TBD | Reviews list |
| ⏳ | `shop/collections/index.html` | TBD | Collections |
| ⏳ | `shop/collections/detail.html` | TBD | Collection detail |
| ➖ | `shop/checkout_success.html` | - | Success page |
| ➖ | `shop/review_form.html` | - | Review form |
| ➖ | `shop/my_downloads.html` | - | Downloads list |

---

### TIER 3: Blog (Priority: MEDIUM)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `blog/post.html` | BlogPostUtils | Post view |
| ✅ | `blog/manage_posts.html` | AdminDataTable | Post management |
| ⏳ | `blog/blog.html` | TBD | Blog listing |
| ⏳ | `blog/admin/editorial_calendar.html` | TBD | Calendar view |
| ➖ | `blog/admin/comment_moderation.html` | - | Has bulk action form |
| ➖ | `blog/edit.html` | - | Edit form |
| ➖ | `blog/new_post.html` | - | Create form |
| ➖ | `blog/blog_category.html` | - | Category page |
| ➖ | `blog/blog_tag.html` | - | Tag page |
| ➖ | `blog/blog_search.html` | - | Search results |
| ➖ | `blog/blog_series.html` | - | Series page |

---

### TIER 4: Admin - Core (Priority: HIGH)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `admin/dashboard.html` | AdminDashboard | Main dashboard |
| ✅ | `admin/calendar.html` | AdminCalendar | Calendar view |
| ✅ | `admin/theme_editor.html` | ThemeEditor | Theme config |
| ✅ | `admin/audit_logs.html` | AdminDataTable | Audit logs |
| ✅ | `admin/list_api_keys.html` | AdminDataTable | API keys |
| ✅ | `admin/list_users.html` | AdminDataTable | User list |
| ✅ | `admin/list_locations.html` | AdminDataTable | Locations |
| ✅ | `admin/list_pages.html` | AdminDataTable | Pages |
| ✅ | `admin/list_roles.html` | AdminDataTable | Roles |
| ✅ | `admin/reschedule_requests.html` | AdminDataTable | Reschedules |
| ⏳ | `admin/search.html` | TBD | Global search |
| ➖ | `admin/edit_user.html` | - | Edit form |
| ➖ | `admin/edit_page.html` | - | Edit form |
| ➖ | `admin/edit_role.html` | - | Edit form |
| ➖ | `admin/new_*.html` | - | Create forms |
| ➖ | `admin/business_config.html` | - | Config form |

---

### TIER 5: Admin - Analytics (Priority: MEDIUM)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `admin/analytics/dashboard.html` | AnalyticsDashboard | Main analytics |
| ✅ | `admin/analytics/goals/index.html` | AdminDataTable | Goals list |
| ➖ | `admin/analytics/funnels/index.html` | - | Cards, not table |
| ⏳ | `admin/analytics/funnels/detail.html` | TBD | Funnel viz |
| ⏳ | `admin/analytics/sessions.html` | TBD | Sessions |
| ⏳ | `admin/analytics/traffic.html` | TBD | Traffic |
| ⏳ | `admin/analytics/visitors.html` | TBD | Visitors |
| ➖ | `admin/analytics/goals/create.html` | - | Create form |
| ➖ | `admin/analytics/goals/edit.html` | - | Edit form |
| ➖ | `admin/analytics/funnels/create.html` | - | Create form |

---

### TIER 6: Admin - CRM (Priority: HIGH)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `admin/crm/kanban.html` | KanbanBoard | Lead kanban |
| ⏳ | `admin/crm/analytics.html` | TBD | CRM charts |
| ✅ | `admin/crm/duplicates.html` | AdminDataTable | Duplicate leads |
| ✅ | `admin/crm/templates.html` | AdminDataTable | CRM templates |
| ➖ | `admin/crm/lead_detail.html` | - | Lead detail |
| ➖ | `admin/crm/pipeline_settings.html` | - | Settings form |

---

### TIER 7: Admin - E-commerce (Priority: HIGH)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `admin/ecommerce/discounts/index.html` | AdminDataTable | Discounts |
| ✅ | `admin/ecommerce/collections/index.html` | AdminDataTable | Collections |
| ✅ | `admin/ecommerce/gift-cards/index.html` | AdminDataTable | Gift cards |
| ✅ | `admin/shop/orders.html` | AdminDataTable | Orders |
| ✅ | `admin/shop/products.html` | AdminDataTable | Products |
| ✅ | `admin/shop/categories.html` | AdminDataTable | Categories |
| ➖ | `admin/shop/order_detail.html` | - | Order detail |
| ➖ | `admin/shop/create_product.html` | - | Create form |
| ➖ | `admin/shop/edit_product.html` | - | Edit form |
| ➖ | `admin/ecommerce/*/form.html` | - | Forms |

---

### TIER 8: Admin - Email & Newsletter (Priority: MEDIUM)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `admin/email/templates/index.html` | EmailTemplateCards | Templates |
| ✅ | `admin/email/sequences/index.html` | AdminDataTable | Sequences |
| ✅ | `admin/newsletter/index.html` | AdminDataTable | Newsletters |
| ✅ | `admin/email/campaigns/index.html` | AdminDataTable | Campaigns |
| ➖ | `admin/email/segments/index.html` | - | Cards, not table |
| ✅ | `admin/email/suppression/index.html` | AdminDataTable | Suppression |
| ⏳ | `admin/email/campaigns/stats.html` | TBD | Campaign stats |
| ➖ | `admin/email/*/form.html` | - | Forms |
| ➖ | `admin/email/templates/preview.html` | - | Preview |
| ➖ | `admin/newsletter/create.html` | - | Create form |

---

### TIER 9: Admin - Forms & Surveys (Priority: MEDIUM)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `admin/forms/index.html` | AdminDataTable | Forms list |
| ✅ | `admin/surveys/index.html` | AdminDataTable | Surveys list |
| ✅ | `admin/forms/submissions.html` | AdminDataTable | Submissions |
| ✅ | `admin/reviews/index.html` | AdminDataTable | Review moderation |
| ➖ | `admin/forms/create.html` | - | Create form |
| ➖ | `admin/forms/edit.html` | - | Edit form |
| ➖ | `admin/forms/submission_detail.html` | - | Detail view |
| ➖ | `admin/surveys/create.html` | - | Create form |

---

### TIER 10: Admin - Scheduling (Priority: MEDIUM)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `admin/scheduling/types/index.html` | AdminDataTable | Appt types |
| ✅ | `admin/scheduling/resources/index.html` | AdminDataTable | Resources |
| ✅ | `admin/scheduling/waitlist/index.html` | AdminDataTable | Waitlist |
| ➖ | `admin/availability/list_estimators.html` | - | Cards, not table |
| ✅ | `admin/availability/list_exceptions.html` | AdminDataTable | Exceptions |
| ⏳ | `admin/scheduling/capacity.html` | TBD | Capacity view |
| ➖ | `admin/scheduling/*/form.html` | - | Forms |
| ➖ | `admin/availability/edit_availability.html` | - | Edit form |

---

### TIER 11: Admin - Tasks & Automation (Priority: LOW)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `admin/tasks/cron.html` | AdminDataTable | Cron jobs |
| ✅ | `admin/automation/index.html` | AdminDataTable | Automations |
| ✅ | `admin/tasks/queue.html` | AdminDataTable | Task queue |
| ✅ | `admin/tasks/dead_letter.html` | AdminDataTable | Dead letters |
| ⏳ | `admin/tasks/worker_status.html` | TBD | Worker status |
| ➖ | `admin/tasks/dashboard.html` | - | Dashboard |
| ➖ | `admin/tasks/detail.html` | - | Task detail |
| ➖ | `admin/automation/edit.html` | - | Edit form |
| ➖ | `admin/automation/new.html` | - | Create form |

---

### TIER 12: Admin - API & Webhooks (Priority: LOW)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `admin/api/webhooks.html` | AdminDataTable | Webhooks |
| ➖ | `admin/api/webhook_form.html` | - | Webhook form |

---

### TIER 13: Admin - Reports (Priority: LOW)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ➖ | `admin/reports/saved/index.html` | - | Cards, not table |
| ⏳ | `admin/reports/builder/index.html` | TBD | Report builder |
| ⏳ | `admin/reports/revenue.html` | TBD | Revenue charts |
| ⏳ | `admin/reports/customers.html` | TBD | Customer charts |
| ⏳ | `admin/reports/products.html` | TBD | Product charts |
| ⏳ | `admin/reports/tax.html` | TBD | Tax reports |
| ➖ | `admin/reports/saved/create.html` | - | Create form |
| ➖ | `admin/reports/saved/view.html` | - | View report |

---

### TIER 14: Admin - HR (Priority: LOW)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ➖ | `admin/hr/leave_requests.html` | - | Has modals, complex |
| ➖ | `admin/hr/leave_balances.html` | - | Form + table hybrid |
| ➖ | `admin/hr/timesheets.html` | - | Multi-table grouped by user |
| ⏳ | `admin/hr/org_chart.html` | TBD | Org chart |

---

### TIER 15: Admin - Other (Priority: LOW)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ⏳ | `admin/ai/dashboard.html` | TBD | AI dashboard |
| ⏳ | `admin/compliance/dashboard.html` | TBD | Compliance |
| ✅ | `admin/backups/index.html` | AdminDataTable | Backups |
| ⏳ | `admin/observability/metrics.html` | TBD | Metrics |
| ⏳ | `admin/dashboards/operations.html` | TBD | Ops dashboard |
| ⏳ | `admin/dashboards/owner.html` | TBD | Owner dashboard |
| ⏳ | `admin/dashboards/sales.html` | TBD | Sales dashboard |

---

### TIER 16: Messaging (Priority: MEDIUM)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `messaging/channel.html` | MessagingChannel | Channel view |
| ⏳ | `messaging/index.html` | TBD | Inbox |
| ⏳ | `messaging/members.html` | TBD | Members |

---

### TIER 17: Employee Portal (Priority: LOW)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ✅ | `employee/calendar.html` | EmployeeCalendar | Calendar |
| ⏳ | `employee/dashboard.html` | TBD | Dashboard |
| ➖ | `employee/directory.html` | - | Cards, not table |
| ⏳ | `employee/timesheet.html` | TBD | Timesheet |
| ⏳ | `employee/org_chart.html` | TBD | Org chart |
| ⏳ | `employee/shared_docs.html` | TBD | Documents |

---

### TIER 18: User Dashboard (Priority: LOW)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ⏳ | `UserDashboard/user_dashboard.html` | TBD | Main dashboard |
| ⏳ | `UserDashboard/activity_feed.html` | TBD | Activity feed |
| ⏳ | `UserDashboard/customer_portal.html` | TBD | Portal |
| ⏳ | `UserDashboard/order_detail.html` | TBD | Order detail |
| ⏳ | `UserDashboard/saved_items.html` | TBD | Saved items |
| ➖ | `UserDashboard/preferences.html` | - | Settings form |
| ➖ | `UserDashboard/commercial_dashboard.html` | - | B2B specific |

---

### TIER 19: Notifications (Priority: LOW)

| Status | Template | Component | Notes |
|--------|----------|-----------|-------|
| ⏳ | `notifications/index.html` | TBD | Notification list |
| ➖ | `notifications/preferences.html` | - | Settings form |

---

### TIER 20: Skip / Keep Jinja2

| Template | Reason |
|----------|--------|
| `form_macros.html` | Helper macros |
| `offline.html` | PWA offline page |
| `accept_terms.html` | Legal form |
| `confirmation.html` | Success page |
| `contact_confirmation.html` | Success page |
| `estimate_submitted.html` | Success page |
| `privacy/consent.html` | Legal form |
| `resend_verification.html` | Auth form |
| `unsubscribe_success.html` | Email success |
| `email/*.html` | Email templates |
| `onboarding/*.html` | Onboarding forms |
| `forms/*.html` | Dynamic forms |
| `surveys/*.html` | Survey forms |
| `setup/wizard.html` | Setup wizard |
| `account/subscriptions.html` | Account form |

---

## Progress Summary

| Category | Total | ✅ Done | ⏳ Pending | ➖ Skip |
|----------|-------|---------|-----------|--------|
| Core & Public | 11 | 3 | 1 | 7 |
| Shop | 10 | 2 | 5 | 3 |
| Blog | 11 | 2 | 3 | 6 |
| Admin Core | 16 | 9 | 2 | 5 |
| Admin Analytics | 10 | 2 | 5 | 3 |
| Admin CRM | 6 | 1 | 3 | 2 |
| Admin E-commerce | 10 | 5 | 1 | 4 |
| Admin Email | 10 | 3 | 4 | 3 |
| Admin Forms | 10 | 2 | 2 | 6 |
| Admin Scheduling | 8 | 3 | 3 | 2 |
| Admin Tasks | 9 | 2 | 3 | 4 |
| Admin API | 2 | 1 | 0 | 1 |
| Admin Reports | 8 | 0 | 6 | 2 |
| Admin HR | 4 | 0 | 4 | 0 |
| Admin Other | 7 | 0 | 7 | 0 |
| Messaging | 3 | 1 | 2 | 0 |
| Employee | 6 | 1 | 5 | 0 |
| User Dashboard | 7 | 0 | 5 | 2 |
| Notifications | 2 | 0 | 1 | 1 |
| Skip (Various) | 15 | 0 | 0 | 15 |
| **TOTAL** | **165** | **38** | **62** | **65** |

---

## Next Actions

When running `/react-migration`, start with:
1. Pick next ⏳ template from highest priority tier with work remaining
2. Follow appropriate migration pattern (A, B, or C)
3. Update checkbox in this file
4. Run `npm run build` to verify
5. Commit changes
