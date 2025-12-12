---
description: Systematic deployment fixes - complete all needed_fixes.md items with browser testing
---

# Deployment Fixes Workflow

**CRITICAL DIRECTIVE**: Follow `docs/needed_fixes.md` EXACTLY as written. Do NOT create a watered-down roadmap. Complete each item fully before moving to the next. Hard focus one item at a time.

## Global Directives (from needed_fixes.md lines 1-4)
- All React and Jinja2 should be **Enterprise Level UX** and **World Class Design Theory UI**
- Before performing any work, **fully analyze all relating code**
- Use existing glassmorphism patterns from `base.css` and `admin-dashboard.css`

## Prerequisites
// turbo
1. Restart Flask server in debug mode:
   ```bash
   source env/bin/activate && python -m flask run --host=0.0.0.0 --debug 2>&1
   ```

// turbo
2. Restart Stripe CLI:
   ```bash
   stripe listen --forward-to localhost:5000/stripe/webhook
   ```

// turbo
3. Ensure npm build is current:
   ```bash
   npm run build
   ```

---

## ITEM 1: /my-account?tab=appointments (Lines 6-8)
**URL**: http://localhost:5000/my-account?tab=appointments
**Notes**: User needs to be able to reschedule, cancel, etc on this page. Currently they cannot.

### Execution Steps:
1. Analyze current implementation of appointments tab in customer_portal.html
2. Analyze React components involved
3. Create API endpoints for reschedule/cancel if missing
4. Build Enterprise UI for appointment management with reschedule/cancel modals
5. **BROWSER TEST**: Verify all functionality works

---

## ITEM 2: /admin/booking (Lines 10-12)
**URL**: http://localhost:5000/admin/booking
**Notes**: Does not appear to be fully designed with CSS within the React. Still appears generic. Should use base reference color schemes that tie into base.css. Enterprise Level UI required.

### Execution Steps:
1. Analyze BookingAdmin.tsx component
2. Update CSS to use base.css color variables
3. Apply full glassmorphism Enterprise styling
4. **BROWSER TEST**: Verify Enterprise UI

---

## ITEM 3: /admin/data-management (Lines 14-16)
**URL**: http://localhost:5000/admin/data-management
**Notes**: Needs full redesign with Enterprise Level UX and UI.

### Execution Steps:
1. Analyze current implementation
2. Create React dashboard with Enterprise glassmorphism
3. **BROWSER TEST**: Verify redesign

---

## ITEM 4: /messaging/ (Lines 18-20)
**URL**: http://localhost:5000/messaging/
**Notes**: Needs full redesign + enterprise enhancement:
- Private channels (role/user-based access)
- Public channel role-based access controls
- Regular users can only access assigned channels (cannot create)
- Fully analyze and put together feature enhancement

### Execution Steps:
1. Fully analyze messaging system code
2. Create feature enhancement plan
3. Implement channel permissions system
4. Redesign with Enterprise UI
5. **BROWSER TEST**: Verify all new features

---

## ITEM 5: Analytics Pages (Lines 22-28)
**URLs**:
- http://localhost:5000/admin/analytics/
- http://localhost:5000/admin/analytics/traffic
- http://localhost:5000/admin/analytics/visitors
- http://localhost:5000/admin/analytics/sessions
- http://localhost:5000/admin/analytics/funnels

**Notes**: All 5 need full redesign and unification. Enhance controls. Fix broken functionality. Fully analyze and execute.

### Execution Steps:
1. Analyze all 5 analytics routes
2. Unify into single React dashboard
3. Fix broken functionality
4. Add enhanced controls
5. Apply Enterprise UI
6. **BROWSER TEST**: Verify all tabs/sections work

---

## ITEM 6: /admin/dashboard Calendar (Lines 30-32)
**URL**: http://localhost:5000/admin/dashboard
**Notes**: Appointments calendar needs enhanced to look like /calendar/view which is far more enhanced. Enterprise UI required.

### Execution Steps:
1. Analyze /calendar/view implementation
2. Port enhanced styling to admin dashboard calendar
3. **BROWSER TEST**: Verify calendar matches /calendar/view quality

---

## ITEM 7: /employee/dashboard (Lines 34-36)
**URL**: http://localhost:5000/employee/dashboard
**Notes**: Full redesign required. Should have calendar view of all appointments/bookings employee is involved in. Fully analyze and execute.

### Execution Steps:
1. Analyze current employee dashboard
2. Add calendar view with employee's appointments
3. Apply Enterprise UI
4. **BROWSER TEST**: Verify calendar shows employee appointments

---

## ITEM 8: Calendar/Appointment Tracking (Lines 38-42)
**URLs**:
- http://localhost:5000/calendar/view
- http://localhost:5000/admin/dashboard
- http://localhost:5000/employee/dashboard

**Notes**: Make sure these all correctly show appointments and tracking is monitored correctly.

### Execution Steps:
1. Test each calendar view
2. Verify appointment data is consistent across all three
3. Fix any tracking issues
4. **BROWSER TEST**: All three views

---

## ITEM 9: Shop Admin Unification (Lines 44-47)
**URLs**:
- http://localhost:5000/admin/shop/orders
- http://localhost:5000/admin/shop/products

**Notes**: Unify into enterprise React dashboard. Remove old code that doesn't relate. Enterprise UI. Fully analyze and execute.

### Execution Steps:
1. Analyze both routes
2. Create unified ShopAdmin React dashboard
3. Apply Enterprise UI
4. Remove deprecated code
5. **BROWSER TEST**: Verify unified experience

---

## ITEM 10: Automation Unification (Lines 49-52)
**URLs**:
- http://localhost:5000/admin/automation/
- http://localhost:5000/admin/automation/new

**Notes**: Unify into enterprise React dashboard. Remove old code. Enterprise UI. Fully analyze and execute.

### Execution Steps:
1. Analyze both routes
2. Create unified Automation React dashboard
3. Apply Enterprise UI
4. Remove deprecated code
5. **BROWSER TEST**: Verify unified experience

---

## ITEM 11: /shop/ (Lines 54-56)
**URL**: http://localhost:5000/shop/
**Notes**: Full redesign with Enterprise UI. Fully analyze and execute.

### Execution Steps:
1. Analyze current shop implementation
2. Redesign storefront with Enterprise UI
3. **BROWSER TEST**: Verify redesign

---

## ITEM 12: /admin/crm/duplicates (Lines 58-60)
**URL**: http://localhost:5000/admin/crm/duplicates
**Notes**: Full redesign with Enterprise UI.

### Execution Steps:
1. Analyze current implementation
2. Apply Enterprise UI redesign
3. **BROWSER TEST**: Verify redesign

---

## ITEM 13: User Management & Locations (Lines 62-67)
**URLs**:
- http://localhost:5000/admin/user-management
- http://localhost:5000/admin/locations

**Notes**:
- Users need location assignment to filter data by location (shop orders, appointments, etc.)
- Booking needs location selection for multi-location business
- Locations page with SEO compliance
- Owner Role: Owner-specific features should only show for Owner role (admin permissions, locations, etc.)
- Enterprise UI. Fully analyze and execute.

### Execution Steps:
1. Analyze user management and locations code
2. Implement location assignment for users
3. Add location filtering for data
4. Update booking for multi-location
5. Create/update locations page with SEO
6. Implement Owner role visibility controls
7. Apply Enterprise UI
8. **BROWSER TEST**: All functionality

---

## ITEM 14: /my-account?tab=orders (Lines 69-71)
**URL**: http://localhost:5000/my-account?tab=orders
**Notes**: Full redesign with Enterprise UI.

### Execution Steps:
1. Analyze orders tab implementation
2. Apply Enterprise UI redesign
3. **BROWSER TEST**: Verify redesign

---

## ITEM 15: /downloads (Lines 73-76)
**URL**: http://localhost:5000/downloads
**Notes**: Was 404. Fixed with redirect. Needs full redesign with Enterprise UI.

### Execution Steps:
1. Verify redirect works
2. Redesign /shop/my-downloads page with Enterprise UI
3. **BROWSER TEST**: Verify redesign

---

## ITEM 16: /booking (Lines 78-80)
**URL**: http://localhost:5000/booking
**Notes**: "love this" - just need to hide default booking form in base.html so only the booking page form shows.

**STATUS**: ✅ COMPLETED (hide_estimate_form flag added to booking/standalone.html)

---

## ITEM 17: /subscriptions (Lines 82-85)
**URL**: http://localhost:5000/subscriptions
**Notes**: Was 404. Fixed with redirect. Needs full redesign with Enterprise UI.

### Execution Steps:
1. Verify redirect works
2. Redesign /account/subscriptions page with Enterprise UI
3. **BROWSER TEST**: Verify redesign

---

## ITEM 18: /contact (Lines 87-89)
**URL**: http://localhost:5000/contact
**Notes**: Full React islands redesign. Hide booking form. Enterprise UI. Fully analyze and execute.

**Booking form hidden**: ✅ COMPLETED

### Remaining Steps:
1. Full React islands redesign of contact page
2. Apply Enterprise UI
3. **BROWSER TEST**: Verify redesign

---

## ITEM 19: User Settings Unification (Lines 91-97)
**URLs**:
- http://localhost:5000/settings
- http://localhost:5000/dashboard/preferences
- http://localhost:5000/notifications/preferences
- http://localhost:5000/dashboard/saved-items
- http://localhost:5000/my-account

**Notes**: All need React islands redesign. Unify into single dashboard. Remove old code. Enterprise UI. Fully analyze and execute.

### Execution Steps:
1. Analyze all 5 routes
2. Create unified UserSettings React dashboard
3. Set up redirects from old routes
4. Remove deprecated code
5. Apply Enterprise UI
6. **BROWSER TEST**: All tabs/sections

---

## ITEM 20: Business Config & Theme Unification (Lines 99-102)
**URLs**:
- http://localhost:5000/admin/business_config
- http://localhost:5000/admin/theme

**Notes**: React islands redesign. Unify. Remove old code. Enterprise UI. Fully analyze and execute.

### Execution Steps:
1. Analyze both routes
2. Create unified settings React dashboard
3. Remove deprecated code
4. Apply Enterprise UI
5. **BROWSER TEST**: All settings work

---

## ITEM 21: Footer Language Swapper (Line 104)
**Notes**: Language swapper not changing site language. Fix it. Enterprise UI.

### Execution Steps:
1. Analyze footer language implementation
2. Fix i18n switching
3. Apply Enterprise UI to footer
4. **BROWSER TEST**: Language change works

---

## ITEM 22: Header Enhancements (Line 106)
**Notes**: 
- Notification dropdown needs redesign
- Cart dropdown needs redesign
- About link not selectable - fix it
- Enterprise UI. Fully analyze and execute.

### Execution Steps:
1. Analyze Header component
2. Fix About link accessibility
3. Redesign notification dropdown
4. Redesign cart dropdown
5. Apply Enterprise UI
6. **BROWSER TEST**: All header features

---

## ITEM 23: On-Page Content Editor Widget (Line 108)
**Notes**: Admin/Manager/Marketing/Owner should be able to edit meta tags, copy, and page images on any page via a click-to-edit widget while logged in.

### Execution Steps:
1. Design floating edit widget
2. Create PageEditorWidget React component
3. Create save/load API endpoints
4. Mount in base template for authorized roles
5. **BROWSER TEST**: Edit content on any page

---

## ITEM 24: Client Update System (Lines 110)
**Notes**: WordPress-like update system for non-custom builds. Push updates to client sites. Admin dashboard section for handling this.

### Execution Steps:
1. Design update management system
2. Create admin dashboard update section
3. Implement version checking and update mechanism
4. **BROWSER TEST**: Update section UI

---

## Execution Order

**HARD FOCUS**: Complete each item in order, one at a time. Do not skip or jump ahead.

Current Progress:
- [x] ITEM 16: /booking - hide form (DONE)
- [x] ITEM 18: /contact - hide form part only (DONE)
- [x] ITEM 15: /downloads - 404 redirect (DONE)
- [x] ITEM 17: /subscriptions - 404 redirect (DONE)

Next: ITEM 1 (/my-account?tab=appointments)
