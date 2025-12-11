---
description: Complete booking system overhaul - fixes time slots, adds payment flow, consolidates admin UI
---

# Enterprise Booking System Overhaul Workflow

This workflow rewrites the booking system to enterprise standards with self-auditing at each step.

## Prerequisites

Ensure the Flask server is running:
```bash
source env/bin/activate && FLASK_APP=run.py flask run --host=0.0.0.0 --debug
```

Ensure Stripe listener is running (if testing payments):
```bash
stripe listen --forward-to localhost:5000/webhook/stripe
```

---

## Phase 1: Database Verification & Seeding

1. **Verify Required Roles Exist**
   ```bash
   flask shell -c "
   from app.models import Role
   roles = ['Admin', 'Employee', 'Manager', 'User']
   for r in roles:
       role = Role.query.filter_by(name=r).first()
       print(f'{r}: {\"✓\" if role else \"✗\"}')"
   ```

2. **Create Employee Role If Missing**
   ```bash
   flask shell -c "
   from app.models import Role, db
   if not Role.query.filter_by(name='Employee').first():
       db.session.add(Role(name='Employee'))
       db.session.commit()
       print('Created Employee role')
   else:
       print('Employee role already exists')"
   ```

// turbo
3. **Seed Test Estimator with Availability**
   ```bash
   flask shell -c "
   from app.models import User, Role, Estimator, Availability, db
   from datetime import time
   
   emp_role = Role.query.filter_by(name='Employee').first()
   emp_user = User.query.filter(User.roles.contains(emp_role)).first() if emp_role else None
   
   if emp_user:
       est = Estimator.query.filter_by(user_id=emp_user.id).first()
       if not est:
           est = Estimator(name=emp_user.username, user_id=emp_user.id, is_active=True)
           db.session.add(est)
           db.session.commit()
           print(f'Created estimator: {est.name}')
       
       if not Availability.query.filter_by(estimator_id=est.id).first():
           for day in range(5):
               avail = Availability(estimator_id=est.id, day_of_week=day, start_time=time(9,0), end_time=time(17,0))
               db.session.add(avail)
           db.session.commit()
           print(f'Created Mon-Fri 9-5 availability for {est.name}')
       else:
           print(f'Estimator {est.name} already has availability')
   else:
       est = Estimator.query.first()
       if est:
           if not Availability.query.filter_by(estimator_id=est.id).first():
               for day in range(5):
                   avail = Availability(estimator_id=est.id, day_of_week=day, start_time=time(9,0), end_time=time(17,0))
                   db.session.add(avail)
               db.session.commit()
               print(f'Created Mon-Fri 9-5 availability for existing estimator {est.name}')
       else:
           print('No estimators found - create one first')"
   ```

4. **Verify Services Exist**
   ```bash
   flask shell -c "
   from app.models import Service
   services = Service.query.all()
   print(f'Found {len(services)} services')
   for s in services:
       payment = '💰 PAID' if s.requires_payment and s.price else 'FREE'
       print(f'  - {s.name} ({payment})')"
   ```

---

## Phase 2: Backend Implementation

5. **Create Unified Booking Admin Template**
   - File: `app/templates/admin/booking.html`
   - Mount `BookingAdmin` React component
   - Include tabs for Services, Staff, Scheduling, Forms, Settings

6. **Add Availability API Endpoints in booking_admin.py**
   - `GET /api/admin/booking/availability/<staff_id>`
   - `POST /api/admin/booking/availability/<staff_id>`
   - Auto-seed availability on staff creation

7. **Update Admin Routes to Redirect**
   - `admin_estimator()` → redirect to `/admin/booking?tab=staff`
   - `services()` → redirect to `/admin/booking?tab=services`

8. **Enhance Slot Generation Debugging**
   - In `booking_api.py:get_slots()` - return reason when no slots
   - Add logging for availability lookup

---

## Phase 3: React Admin Dashboard

9. **Update BookingAdmin.tsx Settings Tab**
   - Business hours start/end time
   - Buffer time configuration
   - Timezone selection

10. **Update BookingAdmin.tsx Staff Tab**
    - Show linked employee user info
    - Weekly availability calendar grid
    - "Seed Default Hours" button

11. **Add Form Builder Tab**
    - List existing intake forms
    - Create/edit form with field types
    - Drag-and-drop reordering

// turbo
12. **Build Frontend**
    ```bash
    cd /home/mike/Documents/Github/verso-backend && npm run build
    ```

---

## Phase 4: Browser Testing - Admin Dashboard

13. **Test Unified Booking Dashboard**
    - Navigate to `http://localhost:5000/admin/booking`
    - Verify all tabs load: Services, Staff, Scheduling, Forms, Settings
    - Screenshot each tab for verification

14. **Test Admin Route Redirects**
    - Navigate to `http://localhost:5000/admin/estimator`
    - **VERIFY**: Redirects to `/admin/booking?tab=staff`
    - Navigate to `http://localhost:5000/admin/service`
    - **VERIFY**: Redirects to `/admin/booking?tab=services`

15. **Test Staff Management**
    - Click "Staff" tab
    - Add new staff member from employee dropdown
    - **VERIFY**: Availability calendar grid appears after add
    - Modify availability hours and save

---

## Phase 5: Browser Testing - Booking Flow

16. **Test Time Slot Generation**
    - Navigate to `http://localhost:5000/onboarding/welcome`
    - Select any service
    - Select a weekday date (Mon-Fri)
    - **VERIFY**: Time slots appear (should show 9am-5pm slots)
    - If no slots: Open DevTools Network tab, check `/api/booking/slots` response

17. **Test Free Booking Flow**
    - Select free service
    - Complete booking form
    - **VERIFY**: Confirmation message appears
    - Check `/admin/calendar` for new appointment

18. **Test Paid Booking Flow (Stripe)**
    - Create paid service: Services tab → Add → Set price → Enable requires_payment
    - Select paid service in booking flow
    - Complete booking form
    - **VERIFY**: Redirects to Stripe checkout
    - Use test card: `4242424242424242`, any future expiry, any CVC
    - **VERIFY**: Returns to success page, appointment confirmed

---

## Phase 6: Calendar View Testing

19. **Test Calendar View**
    - Navigate to `http://localhost:5000/calendar/view`
    - **VERIFY**: Appointments display in calendar
    - **VERIFY**: Click event shows appointment details

20. **Test Location Filtering (if applicable)**
    - If multiple locations configured, verify filter dropdown
    - Select different locations and verify events filter correctly

---

## Phase 7: Automated Tests

// turbo
21. **Run Phase 2 Tests**
    ```bash
    cd /home/mike/Documents/Github/verso-backend && python -m pytest app/tests/test_phase2.py -v
    ```

// turbo
22. **Run TypeScript Type Check**
    ```bash
    cd /home/mike/Documents/Github/verso-backend && npx tsc --noEmit
    ```

---

## Self-Audit Checklist

After completing all phases, verify:

### Backend
- [ ] `/admin/estimator` redirects to unified booking dashboard
- [ ] `/admin/service` redirects to unified booking dashboard
- [ ] Staff creation auto-seeds availability
- [ ] Availability API endpoints return correct data
- [ ] Slot generation returns slots with debug info

### Frontend
- [ ] BookingAdmin.tsx has all tabs: Services, Staff, Scheduling, Forms, Settings
- [ ] Staff panel shows employees with availability grid
- [ ] Services panel has payment toggle
- [ ] No TypeScript errors on build
- [ ] Glassmorphism styling matches admin dashboard

### Booking Flow
- [ ] Estimators load from database (not manual text entry)
- [ ] Time slots display for weekdays
- [ ] Free booking completes with confirmation
- [ ] Paid booking redirects to Stripe and completes

### Calendar
- [ ] Admin calendar displays all appointments
- [ ] Location filter works (if multi-location)
- [ ] Events show correct details on click

---

## Troubleshooting

### No Time Slots Appearing
1. Check if estimator has availability records:
   ```bash
   flask shell -c "
   from app.models import Estimator, Availability
   for e in Estimator.query.filter_by(is_active=True).all():
       avail = Availability.query.filter_by(estimator_id=e.id).count()
       print(f'{e.name}: {avail} availability records')"
   ```

2. If 0 records, seed availability using Phase 1 Step 3

### Stripe Payment Failing
1. Verify Stripe keys in `.env`:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLISHABLE_KEY`
2. Check Stripe listener is running
3. Check Flask logs for Stripe errors

### Staff Not Showing Employees
1. Verify users have Employee role assigned
2. Check `/api/admin/booking/employees` returns users
