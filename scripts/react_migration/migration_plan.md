# React Migration Plan - Template Audit Report

**Generated:** 2025-12-07T00:11:41.883773
**Total Templates:** 191

## Summary Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| Templates with jQuery | 37 | 19% |
| Templates with Chart.js | 7 | 3% |
| Templates with DataTables | 6 | 3% |
| Templates with FullCalendar | 3 | 1% |
| Templates already using React | 1 | 0% |

## Suggested React Components

Based on pattern analysis, the following React components should be created:

- `Calendar`
- `Chart`
- `ConfirmDialog`
- `DataTable`
- `DragDropList`
- `Form`
- `FormField`
- `InfiniteList`
- `KPICard`
- `KanbanBoard`
- `LeadsChart`
- `LoadMoreButton`
- `Modal`
- `ReactForm`
- `RevenueChart`
- `ScheduleView`
- `SortableTable`
- `TabPanel`
- `Tabs`

## Migration Phases by Priority

### Phase 1: Critical (High-Traffic/Revenue Impact)

**31 templates**

| Template | Lines | Complexity | Components Needed |
|----------|-------|------------|-------------------|
| `base.html` | 299 | 10/10 | Calendar, Form, FormField |
| `admin/dashboard.html` | 689 | 8/10 | Chart, Form, FormField |
| `shop/product.html` | 292 | 7/10 | Form, FormField, ReactForm |
| `admin/analytics/dashboard.html` | 287 | 7/10 | Chart, KPICard, LeadsChart |
| `index.html` | 330 | 5/10 | ConfirmDialog, Form, FormField |
| `UserDashboard/customer_portal.html` | 611 | 4/10 | Chart, KPICard |
| `UserDashboard/saved_items.html` | 148 | 4/10 | Chart, Form, FormField |
| `shop/review_form.html` | 155 | 4/10 | Form, FormField, ReactForm |
| `shop/cart.html` | 352 | 4/10 | Form, FormField, ReactForm |
| `booking/book.html` | 135 | 4/10 | Form, FormField, ReactForm |
| `UserDashboard/user_dashboard.html` | 443 | 3/10 | Chart, KPICard |
| `UserDashboard/order_detail.html` | 385 | 3/10 | Chart, KPICard |
| `admin/dashboards/operations.html` | 346 | 3/10 | Chart, KPICard |
| `admin/dashboards/sales.html` | 330 | 3/10 | Chart, KPICard |
| `admin/dashboards/owner.html` | 220 | 3/10 | Chart, KPICard |
| `admin/tasks/dashboard.html` | 210 | 3/10 | Chart, KPICard |
| `UserDashboard/preferences.html` | 194 | 2/10 | Chart, Form, FormField |
| `UserDashboard/commercial_dashboard.html` | 152 | 2/10 | Chart, KPICard |
| `shop/checkout_success.html` | 105 | 2/10 | - |
| `shop/reviews.html` | 193 | 2/10 | Form, FormField, InfiniteList |
| `shop/my_downloads.html` | 152 | 2/10 | Form, FormField, ReactForm |
| `employee/dashboard.html` | 142 | 2/10 | Chart, Form, FormField |
| `shop/collections/detail.html` | 134 | 2/10 | Form, FormField, ReactForm |
| `shop/partials/cart_drawer.html` | 145 | 2/10 | Form, FormField, ReactForm |
| `shop/bundles/detail.html` | 137 | 2/10 | Form, FormField, ReactForm |
| `UserDashboard/activity_feed.html` | 70 | 1/10 | Chart, InfiniteList, KPICard |
| `shop/index.html` | 34 | 1/10 | - |
| `shop/wishlist.html` | 96 | 1/10 | DataTable, Form, FormField |
| `shop/success.html` | 10 | 1/10 | - |
| `booking/index.html` | 54 | 1/10 | - |
| `shop/collections/index.html` | 57 | 1/10 | - |

### Phase 2: Important (Admin/Employee Tools)

**139 templates**

| Template | Lines | Complexity | Components Needed |
|----------|-------|------------|-------------------|
| `admin/list_users.html` | 308 | 9/10 | DataTable, Form, FormField |
| `messaging/channel.html` | 705 | 8/10 | Form, FormField, ReactForm |
| `employee/calendar.html` | 237 | 8/10 | Calendar, Form, FormField |
| `admin/forms/index.html` | 131 | 8/10 | DataTable, Form, FormField |
| `admin/ecommerce/discounts/index.html` | 125 | 8/10 | DataTable, Form, FormField |
| `admin/ecommerce/collections/index.html` | 107 | 8/10 | DataTable, Form, FormField |
| `admin/shop/orders.html` | 272 | 7/10 | Form, FormField, InfiniteList |
| `admin/analytics/sessions.html` | 203 | 7/10 | LeadsChart, RevenueChart |
| `admin/analytics/visitors.html` | 202 | 7/10 | LeadsChart, RevenueChart |
| `admin/crm/lead_detail.html` | 240 | 7/10 | Form, FormField, ReactForm |
| `admin/reports/customers.html` | 204 | 7/10 | Form, FormField, LeadsChart |
| `admin/reports/revenue.html` | 214 | 7/10 | Form, FormField, LeadsChart |
| `admin/ecommerce/collections/form.html` | 241 | 7/10 | Form, FormField, ReactForm |
| `admin/ecommerce/gift-cards/index.html` | 136 | 7/10 | DataTable, Form, FormField |
| `admin/calendar.html` | 63 | 6/10 | Calendar, DragDropList, KanbanBoard |
| `admin/new_user.html` | 103 | 6/10 | Form, FormField, ReactForm |
| `admin/edit_user.html` | 144 | 6/10 | Form, FormField, ReactForm |
| `admin/shop/order_detail.html` | 367 | 6/10 | Form, FormField, ReactForm |
| `admin/crm/templates.html` | 137 | 6/10 | Form, FormField, ReactForm |
| `admin/crm/pipeline_settings.html` | 161 | 6/10 | Form, FormField, ReactForm |
| `admin/forms/submission_detail.html` | 202 | 6/10 | Form, FormField, ReactForm |
| `admin/reports/products.html` | 147 | 6/10 | Form, FormField, LeadsChart |
| `admin/ecommerce/discounts/form.html` | 214 | 6/10 | Form, FormField, ReactForm |
| `admin/ecommerce/gift-cards/form.html` | 110 | 6/10 | Form, FormField, ReactForm |
| `register.html` | 163 | 5/10 | Form, FormField, ReactForm |
| `admin/edit_role.html` | 73 | 5/10 | Form, FormField, ReactForm |
| `admin/audit_logs.html` | 114 | 5/10 | Form, FormField, InfiniteList |
| `admin/new_role.html` | 72 | 5/10 | Form, FormField, ReactForm |
| `admin/theme_editor.html` | 459 | 5/10 | Form, FormField, ReactForm |
| `admin/forms/edit.html` | 397 | 5/10 | ConfirmDialog, Form, FormField |
| `admin/forms/create.html` | 404 | 5/10 | ConfirmDialog, Form, FormField |
| `admin/reports/builder/index.html` | 211 | 5/10 | Form, FormField, ReactForm |
| `admin/email/suppression/index.html` | 151 | 5/10 | ConfirmDialog, Form, FormField |
| `admin/email/segments/form.html` | 208 | 5/10 | Form, FormField, ReactForm |
| `contact.html` | 69 | 4/10 | Form, FormField, ReactForm |
| `estimate_submitted.html` | 124 | 4/10 | - |
| `admin/service.html` | 125 | 4/10 | Form, FormField, ReactForm |
| `admin/edit_page.html` | 136 | 4/10 | Form, FormField, ReactForm |
| `admin/list_api_keys.html` | 77 | 4/10 | DataTable, Form, FormField |
| `admin/estimator_form.html` | 106 | 4/10 | Form, FormField, ReactForm |
| `forms/form.html` | 196 | 4/10 | Form, FormField, ReactForm |
| `admin/automation/edit.html` | 198 | 4/10 | ConfirmDialog, Form, FormField |
| `admin/availability/list_exceptions.html` | 155 | 4/10 | DataTable, Form, FormField |
| `admin/crm/kanban.html` | 140 | 4/10 | DragDropList, KanbanBoard |
| `admin/surveys/create.html` | 189 | 4/10 | Form, FormField, ReactForm |
| `admin/api/webhook_form.html` | 162 | 4/10 | Form, FormField, ReactForm |
| `admin/observability/metrics.html` | 362 | 4/10 | - |
| `admin/reviews/detail.html` | 247 | 4/10 | ConfirmDialog, Form, FormField |
| `admin/reports/tax.html` | 134 | 4/10 | Form, FormField, ReactForm |
| `admin/hr/org_chart.html` | 162 | 4/10 | Form, FormField, ReactForm |
| `admin/analytics/funnels/create.html` | 125 | 4/10 | Form, FormField, ReactForm |
| `admin/email/campaigns/stats.html` | 246 | 4/10 | Form, FormField, ReactForm |
| `admin/email/sequences/form.html` | 178 | 4/10 | Form, FormField, ReactForm |
| `admin/email/templates/preview.html` | 153 | 4/10 | Form, FormField, ReactForm |
| `admin/email/templates/index.html` | 97 | 4/10 | Form, FormField, ReactForm |
| `aboutus.html` | 166 | 3/10 | - |
| `accept_terms.html` | 26 | 3/10 | Form, FormField, ReactForm |
| `messaging/index.html` | 277 | 3/10 | Form, FormField, ReactForm |
| `messaging/members.html` | 160 | 3/10 | Form, FormField, ReactForm |
| `onboarding/preferences.html` | 239 | 3/10 | Form, FormField, ReactForm |
| `onboarding/profile.html` | 230 | 3/10 | Form, FormField, ReactForm |
| `onboarding/welcome.html` | 218 | 3/10 | Form, FormField, ReactForm |
| `admin/new_api_key.html` | 52 | 3/10 | Form, FormField, ReactForm |
| `admin/theme_preview.html` | 284 | 3/10 | Form, FormField, ReactForm |
| `admin/page_custom_fields.html` | 133 | 3/10 | Form, FormField, ReactForm |
| `admin/list_roles.html` | 99 | 3/10 | DataTable, Form, FormField |
| `admin/reschedule_requests.html` | 139 | 3/10 | ConfirmDialog, Form, FormField |
| `admin/business_config.html` | 129 | 3/10 | Form, FormField, ReactForm |
| `admin/search.html` | 238 | 3/10 | Form, FormField, ReactForm |
| `admin/new_location.html` | 41 | 3/10 | Form, FormField, ReactForm |
| `notifications/index.html` | 222 | 3/10 | Form, FormField, InfiniteList |
| `admin/availability/edit_availability.html` | 121 | 3/10 | Form, FormField, ReactForm |
| `admin/surveys/index.html` | 141 | 3/10 | Form, FormField, ReactForm |
| `admin/api/webhooks.html` | 190 | 3/10 | Form, FormField, ReactForm |
| `admin/reviews/index.html` | 202 | 3/10 | Form, FormField, InfiniteList |
| `admin/hr/leave_balances.html` | 98 | 3/10 | Form, FormField, ReactForm |
| `admin/analytics/goals/index.html` | 116 | 3/10 | Form, FormField, ReactForm |
| `admin/email/campaigns/index.html` | 145 | 3/10 | Form, FormField, ReactForm |
| `admin/revision_history.html` | 97 | 2/10 | Form, FormField, ReactForm |
| `admin/data_management.html` | 89 | 2/10 | Form, FormField, ReactForm |
| `admin/list_pages.html` | 72 | 2/10 | DataTable, Form, FormField |
| `notifications/preferences.html` | 108 | 2/10 | Form, FormField, ReactForm |
| `employee/org_chart.html` | 128 | 2/10 | - |
| `employee/timesheet.html` | 102 | 2/10 | - |
| `admin/automation/index.html` | 70 | 2/10 | Form, FormField, ReactForm |
| `admin/shop/products.html` | 58 | 2/10 | Form, FormField, ReactForm |
| `admin/shop/categories.html` | 73 | 2/10 | Form, FormField, ReactForm |
| `admin/analytics/traffic.html` | 191 | 2/10 | - |
| `admin/crm/analytics.html` | 151 | 2/10 | - |
| `admin/surveys/detail.html` | 196 | 2/10 | Form, FormField, ReactForm |
| `admin/newsletter/index.html` | 51 | 2/10 | Form, FormField, ReactForm |
| `admin/tasks/detail.html` | 120 | 2/10 | Form, FormField, ReactForm |
| `admin/tasks/dead_letter.html` | 105 | 2/10 | Form, FormField, InfiniteList |
| `admin/tasks/queue.html` | 145 | 2/10 | Form, FormField, InfiniteList |
| `admin/forms/submissions.html` | 179 | 2/10 | Form, FormField, InfiniteList |
| `admin/hr/leave_requests.html` | 175 | 2/10 | ConfirmDialog, Form, FormField |
| `admin/reports/saved/index.html` | 89 | 2/10 | Form, FormField, ReactForm |
| `admin/reports/saved/view.html` | 165 | 2/10 | - |
| `admin/analytics/funnels/index.html` | 91 | 2/10 | Form, FormField, ReactForm |
| `admin/analytics/funnels/detail.html` | 127 | 2/10 | - |
| `admin/email/campaigns/form.html` | 137 | 2/10 | Form, FormField, ReactForm |
| `admin/email/sequences/index.html` | 90 | 2/10 | Form, FormField, ReactForm |
| `admin/email/templates/form.html` | 140 | 2/10 | Form, FormField, ReactForm |
| `admin/email/segments/index.html` | 90 | 2/10 | Form, FormField, ReactForm |
| `unsubscribe_success.html` | 13 | 1/10 | - |
| `contact_confirmation.html` | 29 | 1/10 | - |
| `page.html` | 18 | 1/10 | - |
| `confirmation.html` | 25 | 1/10 | - |
| `accessibility.html` | 55 | 1/10 | - |
| `login.html` | 55 | 1/10 | Form, FormField, ReactForm |
| `resend_verification.html` | 55 | 1/10 | Form, FormField, ReactForm |
| `services.html` | 10 | 1/10 | - |
| `offline.html` | 14 | 1/10 | - |
| `form_macros.html` | 16 | 1/10 | ReactForm |
| `admin/list_locations.html` | 44 | 1/10 | DataTable |
| `forms/thank_you.html` | 25 | 1/10 | ReactForm |
| `employee/shared_docs.html` | 85 | 1/10 | Form, FormField, ReactForm |
| `employee/directory.html` | 87 | 1/10 | Form, FormField, ReactForm |
| `admin/automation/new.html` | 46 | 1/10 | Form, FormField, ReactForm |
| `admin/availability/list_estimators.html` | 45 | 1/10 | DataTable |
| `admin/shop/category_form.html` | 58 | 1/10 | Form, FormField, ReactForm |
| `admin/shop/edit_product.html` | 66 | 1/10 | Form, FormField, ReactForm |
| `admin/shop/create_product.html` | 57 | 1/10 | Form, FormField, ReactForm |
| `admin/scheduling/capacity.html` | 44 | 1/10 | - |
| `admin/crm/duplicates.html` | 45 | 1/10 | - |
| `admin/newsletter/view.html` | 37 | 1/10 | - |
| `admin/newsletter/create.html` | 23 | 1/10 | Form, FormField, ReactForm |
| `admin/tasks/cron.html` | 78 | 1/10 | Form, FormField, ReactForm |
| `admin/tasks/worker_status.html` | 74 | 1/10 | - |
| `admin/hr/timesheets.html` | 84 | 1/10 | - |
| `admin/reports/saved/create.html` | 86 | 1/10 | Form, FormField, ReactForm |
| `admin/scheduling/resources/form.html` | 49 | 1/10 | Form, FormField, ReactForm |
| `admin/scheduling/resources/index.html` | 60 | 1/10 | - |
| `admin/scheduling/types/form.html` | 60 | 1/10 | Form, FormField, ReactForm |
| `admin/scheduling/types/index.html` | 66 | 1/10 | - |
| `admin/scheduling/waitlist/index.html` | 87 | 1/10 | DataTable, Form, FormField |
| `admin/analytics/goals/edit.html` | 88 | 1/10 | Form, FormField, ReactForm |
| `admin/analytics/goals/create.html` | 84 | 1/10 | Form, FormField, ReactForm |
| `admin/email/segments/preview.html` | 65 | 1/10 | - |

### Phase 3: Standard (Content/Utilities)

**18 templates**

| Template | Lines | Complexity | Components Needed |
|----------|-------|------------|-------------------|
| `blog/edit.html` | 197 | 6/10 | Form, FormField, ReactForm |
| `blog/new_post.html` | 172 | 6/10 | Form, FormField, ReactForm |
| `blog/admin/comment_moderation.html` | 132 | 6/10 | Form, FormField, InfiniteList |
| `blog/admin/manage_categories.html` | 131 | 6/10 | Form, FormField, ReactForm |
| `blog/admin/manage_series.html` | 132 | 6/10 | Form, FormField, ReactForm |
| `blog/post.html` | 304 | 5/10 | Form, FormField, ReactForm |
| `blog/admin/manage_tags.html` | 98 | 5/10 | Form, FormField, ReactForm |
| `blog/manage_posts.html` | 162 | 4/10 | Form, FormField, InfiniteList |
| `blog/blog_search.html` | 145 | 4/10 | Form, FormField, InfiniteList |
| `blog/blog.html` | 163 | 4/10 | Form, FormField, InfiniteList |
| `setup/wizard.html` | 98 | 2/10 | Form, FormField, ReactForm |
| `blog/blog_tag.html` | 117 | 2/10 | InfiniteList, LoadMoreButton |
| `blog/blog_category.html` | 148 | 2/10 | InfiniteList, LoadMoreButton |
| `surveys/survey.html` | 136 | 2/10 | Form, FormField, ReactForm |
| `account/subscriptions.html` | 78 | 2/10 | Form, FormField, ReactForm |
| `blog/admin/editorial_calendar.html` | 137 | 2/10 | - |
| `blog/blog_series.html` | 82 | 1/10 | - |
| `surveys/thank_you.html` | 25 | 1/10 | - |

### Phase 4: Low (Email/Background)

**3 templates**

| Template | Lines | Complexity | Components Needed |
|----------|-------|------------|-------------------|
| `email/unsubscribe_success.html` | 31 | 1/10 | - |
| `email/unsubscribe_confirm.html` | 44 | 1/10 | Form, FormField, ReactForm |
| `email/preferences.html` | 84 | 1/10 | Form, FormField, ReactForm |

## Templates by Category

### Userdashboard (7 templates)

- `UserDashboard/activity_feed.html` (P1, C1)
- `UserDashboard/commercial_dashboard.html` (P1, C2)
- `UserDashboard/customer_portal.html` (P1, C4)
- `UserDashboard/order_detail.html` (P1, C3)
- `UserDashboard/preferences.html` (P1, C2)
- `UserDashboard/saved_items.html` (P1, C4)
- `UserDashboard/user_dashboard.html` (P1, C3)

### Account (1 templates)

- `account/subscriptions.html` (P3, C2)

### Admin (115 templates)

- `admin/analytics/dashboard.html` (P1, C7) [Charts]
- `admin/analytics/funnels/create.html` (P2, C4)
- `admin/analytics/funnels/detail.html` (P2, C2)
- `admin/analytics/funnels/index.html` (P2, C2)
- `admin/analytics/goals/create.html` (P2, C1)
- `admin/analytics/goals/edit.html` (P2, C1)
- `admin/analytics/goals/index.html` (P2, C3)
- `admin/analytics/sessions.html` (P2, C7) [Charts]
- `admin/analytics/traffic.html` (P2, C2)
- `admin/analytics/visitors.html` (P2, C7) [Charts]
- `admin/api/webhook_form.html` (P2, C4)
- `admin/api/webhooks.html` (P2, C3)
- `admin/audit_logs.html` (P2, C5) [jQuery]
- `admin/automation/edit.html` (P2, C4)
- `admin/automation/index.html` (P2, C2)
- `admin/automation/new.html` (P2, C1)
- `admin/availability/edit_availability.html` (P2, C3)
- `admin/availability/list_estimators.html` (P2, C1)
- `admin/availability/list_exceptions.html` (P2, C4)
- `admin/business_config.html` (P2, C3)
- `admin/calendar.html` (P2, C6) [Calendar]
- `admin/crm/analytics.html` (P2, C2)
- `admin/crm/duplicates.html` (P2, C1)
- `admin/crm/kanban.html` (P2, C4)
- `admin/crm/lead_detail.html` (P2, C7) [jQuery]
- `admin/crm/pipeline_settings.html` (P2, C6) [jQuery]
- `admin/crm/templates.html` (P2, C6) [jQuery]
- `admin/dashboard.html` (P1, C8) [Charts]
- `admin/dashboards/operations.html` (P1, C3)
- `admin/dashboards/owner.html` (P1, C3)
- `admin/dashboards/sales.html` (P1, C3)
- `admin/data_management.html` (P2, C2)
- `admin/ecommerce/collections/form.html` (P2, C7) [jQuery]
- `admin/ecommerce/collections/index.html` (P2, C8) [jQuery, DataTables]
- `admin/ecommerce/discounts/form.html` (P2, C6) [jQuery]
- `admin/ecommerce/discounts/index.html` (P2, C8) [jQuery, DataTables]
- `admin/ecommerce/gift-cards/form.html` (P2, C6) [jQuery]
- `admin/ecommerce/gift-cards/index.html` (P2, C7) [jQuery, DataTables]
- `admin/edit_page.html` (P2, C4) [jQuery]
- `admin/edit_role.html` (P2, C5) [jQuery]
- `admin/edit_user.html` (P2, C6) [jQuery]
- `admin/email/campaigns/form.html` (P2, C2)
- `admin/email/campaigns/index.html` (P2, C3)
- `admin/email/campaigns/stats.html` (P2, C4)
- `admin/email/segments/form.html` (P2, C5)
- `admin/email/segments/index.html` (P2, C2)
- `admin/email/segments/preview.html` (P2, C1)
- `admin/email/sequences/form.html` (P2, C4)
- `admin/email/sequences/index.html` (P2, C2)
- `admin/email/suppression/index.html` (P2, C5) [jQuery]
- `admin/email/templates/form.html` (P2, C2)
- `admin/email/templates/index.html` (P2, C4) [jQuery]
- `admin/email/templates/preview.html` (P2, C4)
- `admin/estimator_form.html` (P2, C4)
- `admin/forms/create.html` (P2, C5)
- `admin/forms/edit.html` (P2, C5)
- `admin/forms/index.html` (P2, C8) [jQuery, DataTables]
- `admin/forms/submission_detail.html` (P2, C6) [jQuery]
- `admin/forms/submissions.html` (P2, C2)
- `admin/hr/leave_balances.html` (P2, C3) [jQuery]
- `admin/hr/leave_requests.html` (P2, C2)
- `admin/hr/org_chart.html` (P2, C4)
- `admin/hr/timesheets.html` (P2, C1)
- `admin/list_api_keys.html` (P2, C4) [DataTables]
- `admin/list_locations.html` (P2, C1)
- `admin/list_pages.html` (P2, C2)
- `admin/list_roles.html` (P2, C3)
- `admin/list_users.html` (P2, C9) [jQuery, DataTables]
- `admin/new_api_key.html` (P2, C3) [jQuery]
- `admin/new_location.html` (P2, C3) [jQuery]
- `admin/new_role.html` (P2, C5) [jQuery]
- `admin/new_user.html` (P2, C6) [jQuery]
- `admin/newsletter/create.html` (P2, C1)
- `admin/newsletter/index.html` (P2, C2)
- `admin/newsletter/view.html` (P2, C1)
- `admin/observability/metrics.html` (P2, C4)
- `admin/page_custom_fields.html` (P2, C3)
- `admin/reports/builder/index.html` (P2, C5)
- `admin/reports/customers.html` (P2, C7) [Charts]
- `admin/reports/products.html` (P2, C6) [Charts]
- `admin/reports/revenue.html` (P2, C7) [Charts]
- `admin/reports/saved/create.html` (P2, C1)
- `admin/reports/saved/index.html` (P2, C2)
- `admin/reports/saved/view.html` (P2, C2)
- `admin/reports/tax.html` (P2, C4)
- `admin/reschedule_requests.html` (P2, C3)
- `admin/reviews/detail.html` (P2, C4)
- `admin/reviews/index.html` (P2, C3)
- `admin/revision_history.html` (P2, C2)
- `admin/scheduling/capacity.html` (P2, C1)
- `admin/scheduling/resources/form.html` (P2, C1)
- `admin/scheduling/resources/index.html` (P2, C1)
- `admin/scheduling/types/form.html` (P2, C1)
- `admin/scheduling/types/index.html` (P2, C1)
- `admin/scheduling/waitlist/index.html` (P2, C1)
- `admin/search.html` (P2, C3)
- `admin/service.html` (P2, C4)
- `admin/shop/categories.html` (P2, C2)
- `admin/shop/category_form.html` (P2, C1)
- `admin/shop/create_product.html` (P2, C1)
- `admin/shop/edit_product.html` (P2, C1)
- `admin/shop/order_detail.html` (P2, C6) [jQuery]
- `admin/shop/orders.html` (P2, C7) [jQuery]
- `admin/shop/products.html` (P2, C2)
- `admin/surveys/create.html` (P2, C4)
- `admin/surveys/detail.html` (P2, C2)
- `admin/surveys/index.html` (P2, C3)
- `admin/tasks/cron.html` (P2, C1)
- `admin/tasks/dashboard.html` (P1, C3)
- `admin/tasks/dead_letter.html` (P2, C2)
- `admin/tasks/detail.html` (P2, C2)
- `admin/tasks/queue.html` (P2, C2)
- `admin/tasks/worker_status.html` (P2, C1)
- `admin/theme_editor.html` (P2, C5)
- `admin/theme_preview.html` (P2, C3)

### Blog (14 templates)

- `blog/admin/comment_moderation.html` (P3, C6) [jQuery]
- `blog/admin/editorial_calendar.html` (P3, C2)
- `blog/admin/manage_categories.html` (P3, C6) [jQuery]
- `blog/admin/manage_series.html` (P3, C6) [jQuery]
- `blog/admin/manage_tags.html` (P3, C5) [jQuery]
- `blog/blog.html` (P3, C4)
- `blog/blog_category.html` (P3, C2)
- `blog/blog_search.html` (P3, C4)
- `blog/blog_series.html` (P3, C1)
- `blog/blog_tag.html` (P3, C2)
- `blog/edit.html` (P3, C6) [jQuery]
- `blog/manage_posts.html` (P3, C4)
- `blog/new_post.html` (P3, C6) [jQuery]
- `blog/post.html` (P3, C5)

### Booking (2 templates)

- `booking/book.html` (P1, C4)
- `booking/index.html` (P1, C1)

### Email (3 templates)

- `email/preferences.html` (P4, C1)
- `email/unsubscribe_confirm.html` (P4, C1)
- `email/unsubscribe_success.html` (P4, C1)

### Employee (6 templates)

- `employee/calendar.html` (P2, C8) [Calendar]
- `employee/dashboard.html` (P1, C2)
- `employee/directory.html` (P2, C1)
- `employee/org_chart.html` (P2, C2)
- `employee/shared_docs.html` (P2, C1)
- `employee/timesheet.html` (P2, C2)

### Forms (2 templates)

- `forms/form.html` (P2, C4)
- `forms/thank_you.html` (P2, C1)

### Messaging (3 templates)

- `messaging/channel.html` (P2, C8) [jQuery]
- `messaging/index.html` (P2, C3)
- `messaging/members.html` (P2, C3)

### Notifications (2 templates)

- `notifications/index.html` (P2, C3)
- `notifications/preferences.html` (P2, C2)

### Onboarding (3 templates)

- `onboarding/preferences.html` (P2, C3)
- `onboarding/profile.html` (P2, C3)
- `onboarding/welcome.html` (P2, C3)

### Root (17 templates)

- `aboutus.html` (P2, C3)
- `accept_terms.html` (P2, C3) [jQuery]
- `accessibility.html` (P2, C1)
- `base.html` (P1, C10) [jQuery, Calendar, ✓ React]
- `confirmation.html` (P2, C1)
- `contact.html` (P2, C4) [jQuery]
- `contact_confirmation.html` (P2, C1)
- `estimate_submitted.html` (P2, C4)
- `form_macros.html` (P2, C1)
- `index.html` (P1, C5)
- `login.html` (P2, C1)
- `offline.html` (P2, C1)
- `page.html` (P2, C1)
- `register.html` (P2, C5) [jQuery]
- `resend_verification.html` (P2, C1)
- `services.html` (P2, C1)
- `unsubscribe_success.html` (P2, C1)

### Setup (1 templates)

- `setup/wizard.html` (P3, C2)

### Shop (13 templates)

- `shop/bundles/detail.html` (P1, C2)
- `shop/cart.html` (P1, C4)
- `shop/checkout_success.html` (P1, C2)
- `shop/collections/detail.html` (P1, C2)
- `shop/collections/index.html` (P1, C1)
- `shop/index.html` (P1, C1)
- `shop/my_downloads.html` (P1, C2)
- `shop/partials/cart_drawer.html` (P1, C2)
- `shop/product.html` (P1, C7) [jQuery]
- `shop/review_form.html` (P1, C4)
- `shop/reviews.html` (P1, C2)
- `shop/success.html` (P1, C1)
- `shop/wishlist.html` (P1, C1)

### Surveys (2 templates)

- `surveys/survey.html` (P3, C2)
- `surveys/thank_you.html` (P3, C1)

## High Complexity Templates (Complexity >= 7)

These templates require special attention during migration:

### `base.html`
- **Complexity:** 10/10
- **Lines:** 299
- **Patterns:** jQuery: True, Charts: False, DataTables: False, Calendar: True
- **Suggested Components:** Calendar, Form, FormField, ReactForm, ScheduleView
- **Jinja Variables:** business_config, category, current_location, current_version, message, rum_script, unread_notifications_count, vite_tags

### `admin/list_users.html`
- **Complexity:** 9/10
- **Lines:** 308
- **Patterns:** jQuery: True, Charts: False, DataTables: True, Calendar: False
- **Suggested Components:** DataTable, Form, FormField, ReactForm, SortableTable
- **Jinja Variables:** description, form, role, title, user

### `admin/dashboard.html`
- **Complexity:** 8/10
- **Lines:** 689
- **Patterns:** jQuery: False, Charts: True, DataTables: False, Calendar: False
- **Suggested Components:** Chart, Form, FormField, KPICard, LeadsChart, ReactForm, RevenueChart
- **Jinja Variables:** appointment, form, kpis, submission

### `messaging/channel.html`
- **Complexity:** 8/10
- **Lines:** 705
- **Patterns:** jQuery: True, Charts: False, DataTables: False, Calendar: False
- **Suggested Components:** Form, FormField, ReactForm
- **Jinja Variables:** channel, current_channel, dm, member, message, reaction

### `employee/calendar.html`
- **Complexity:** 8/10
- **Lines:** 237
- **Patterns:** jQuery: False, Charts: False, DataTables: False, Calendar: True
- **Suggested Components:** Calendar, Form, FormField, ReactForm, ScheduleView
- **Jinja Variables:** csrf_form, estimator, notes_form, reschedule_form, rr

### `admin/forms/index.html`
- **Complexity:** 8/10
- **Lines:** 131
- **Patterns:** jQuery: True, Charts: False, DataTables: True, Calendar: False
- **Suggested Components:** DataTable, Form, FormField, ReactForm, SortableTable
- **Jinja Variables:** form, message

### `admin/ecommerce/discounts/index.html`
- **Complexity:** 8/10
- **Lines:** 125
- **Patterns:** jQuery: True, Charts: False, DataTables: True, Calendar: False
- **Suggested Components:** DataTable, Form, FormField, ReactForm, SortableTable
- **Jinja Variables:** category, discount, message

### `admin/ecommerce/collections/index.html`
- **Complexity:** 8/10
- **Lines:** 107
- **Patterns:** jQuery: True, Charts: False, DataTables: True, Calendar: False
- **Suggested Components:** DataTable, Form, FormField, ReactForm, SortableTable
- **Jinja Variables:** category, collection, message

### `shop/product.html`
- **Complexity:** 7/10
- **Lines:** 292
- **Patterns:** jQuery: True, Charts: False, DataTables: False, Calendar: False
- **Suggested Components:** Form, FormField, ReactForm
- **Jinja Variables:** business_config, img, item, product, variant, variants

### `admin/analytics/dashboard.html`
- **Complexity:** 7/10
- **Lines:** 287
- **Patterns:** jQuery: False, Charts: True, DataTables: False, Calendar: False
- **Suggested Components:** Chart, KPICard, LeadsChart, RevenueChart
- **Jinja Variables:** metrics, page, stat

### `admin/shop/orders.html`
- **Complexity:** 7/10
- **Lines:** 272
- **Patterns:** jQuery: True, Charts: False, DataTables: False, Calendar: False
- **Suggested Components:** Form, FormField, InfiniteList, LoadMoreButton, ReactForm
- **Jinja Variables:** current_status, order, orders, status_counts

### `admin/analytics/sessions.html`
- **Complexity:** 7/10
- **Lines:** 203
- **Patterns:** jQuery: False, Charts: True, DataTables: False, Calendar: False
- **Suggested Components:** LeadsChart, RevenueChart
- **Jinja Variables:** bounce_trend, durations, pages_dist

### `admin/analytics/visitors.html`
- **Complexity:** 7/10
- **Lines:** 202
- **Patterns:** jQuery: False, Charts: True, DataTables: False, Calendar: False
- **Suggested Components:** LeadsChart, RevenueChart
- **Jinja Variables:** country, daily_visitors, new_visitors, ref, returning_visitors

### `admin/crm/lead_detail.html`
- **Complexity:** 7/10
- **Lines:** 240
- **Patterns:** jQuery: True, Charts: False, DataTables: False, Calendar: False
- **Suggested Components:** Form, FormField, ReactForm, TabPanel, Tabs
- **Jinja Variables:** activities, activity, assign_form, item, lead_score, lead_type, note, note_form, notes, r

### `admin/reports/customers.html`
- **Complexity:** 7/10
- **Lines:** 204
- **Patterns:** jQuery: False, Charts: True, DataTables: False, Calendar: False
- **Suggested Components:** Form, FormField, LeadsChart, ReactForm, RevenueChart
- **Jinja Variables:** customer, customers, repeat_rate

### `admin/reports/revenue.html`
- **Complexity:** 7/10
- **Lines:** 214
- **Patterns:** jQuery: False, Charts: True, DataTables: False, Calendar: False
- **Suggested Components:** Form, FormField, LeadsChart, ReactForm, RevenueChart
- **Jinja Variables:** daily_data, method, metrics

### `admin/ecommerce/collections/form.html`
- **Complexity:** 7/10
- **Lines:** 241
- **Patterns:** jQuery: True, Charts: False, DataTables: False, Calendar: False
- **Suggested Components:** Form, FormField, ReactForm
- **Jinja Variables:** collection, product, rule

### `admin/ecommerce/gift-cards/index.html`
- **Complexity:** 7/10
- **Lines:** 136
- **Patterns:** jQuery: True, Charts: False, DataTables: True, Calendar: False
- **Suggested Components:** DataTable, Form, FormField, ReactForm, SortableTable
- **Jinja Variables:** category, gc, gift_cards, message
