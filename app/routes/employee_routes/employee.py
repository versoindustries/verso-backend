from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort, jsonify
from flask_login import login_required, current_user
from app.models import (LeaveRequest, EncryptedDocument, Appointment, Estimator, RescheduleRequest,
                         LeaveBalance, DocumentShare, TimeEntry, User, Role)
from app.forms import (RescheduleRequestForm, AppointmentNotesForm, CSRFTokenForm, LeaveRequestForm,
                        DocumentShareForm, DocumentUploadForm, TimeEntryForm, EmployeeSearchForm, EmployeeProfileForm)
from app.database import db
from app.modules.encryption import encrypt_data, decrypt_data
from datetime import datetime, timedelta
import io
import pytz
import json

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


@employee_bp.route('/dashboard')
@login_required
def dashboard():
    """Enhanced employee dashboard with leave balances and time tracking."""
    leave_requests = LeaveRequest.query.filter_by(user_id=current_user.id).order_by(LeaveRequest.created_at.desc()).limit(10).all()
    documents = EncryptedDocument.query.filter_by(user_id=current_user.id).order_by(EncryptedDocument.created_at.desc()).limit(5).all()
    
    # Phase 5: Get leave balances for current year
    current_year = datetime.utcnow().year
    leave_balances = LeaveBalance.query.filter_by(user_id=current_user.id, year=current_year).all()
    
    # Phase 5: Check if currently clocked in
    today = datetime.utcnow().date()
    active_time_entry = TimeEntry.query.filter_by(
        user_id=current_user.id,
        date=today,
        clock_out=None
    ).first()
    
    # Phase 5: Get recent time entries
    recent_time_entries = TimeEntry.query.filter_by(user_id=current_user.id).order_by(TimeEntry.date.desc()).limit(5).all()
    
    # Phase 5: Get shared documents
    shared_docs_count = DocumentShare.query.filter_by(shared_with_user_id=current_user.id).count()
    
    # Get estimator profile for calendar
    estimator = None
    if hasattr(current_user, 'estimator_profile') and current_user.estimator_profile:
        estimator = current_user.estimator_profile
    
    leave_form = LeaveRequestForm()
    doc_form = DocumentUploadForm()
    time_form = TimeEntryForm()
    profile_form = EmployeeProfileForm(obj=current_user)
    
    # Serialize initial data for React component
    initial_stats = {
        'today_appointments': 0,
        'week_appointments': 0,
        'pending_leave': 0,
        'hours_this_week': 0,
        'is_clocked_in': active_time_entry is not None,
        'clock_in_time': active_time_entry.clock_in.isoformat() if active_time_entry else None,
    }
    
    # Calculate appointment stats if estimator
    if estimator:
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        today_end = today_start + timedelta(days=1)
        week_end = today_start + timedelta(days=7)
        
        initial_stats['today_appointments'] = Appointment.query.filter(
            Appointment.estimator_id == estimator.id,
            Appointment.preferred_date_time >= today_start,
            Appointment.preferred_date_time < today_end
        ).count()
        
        initial_stats['week_appointments'] = Appointment.query.filter(
            Appointment.estimator_id == estimator.id,
            Appointment.preferred_date_time >= today_start,
            Appointment.preferred_date_time < week_end
        ).count()
    
    # Pending leave requests
    initial_stats['pending_leave'] = LeaveRequest.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).count()
    
    # Hours this week
    week_start = today - timedelta(days=today.weekday())
    week_entries = TimeEntry.query.filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.date >= week_start
    ).all()
    initial_stats['hours_this_week'] = round(sum(e.duration_minutes or 0 for e in week_entries) / 60, 1)
    
    # Serialize upcoming appointments
    upcoming_appointments = []
    if estimator:
        upcoming = Appointment.query.filter(
            Appointment.estimator_id == estimator.id,
            Appointment.preferred_date_time >= datetime.utcnow()
        ).order_by(Appointment.preferred_date_time).limit(5).all()
        
        for appt in upcoming:
            upcoming_appointments.append({
                'id': appt.id,
                'name': f"{appt.first_name} {appt.last_name}",
                'datetime': appt.preferred_date_time.isoformat(),
                'service': appt.service.name if appt.service else 'N/A',
                'status': appt.status,
                'checked_in': appt.checked_in_at is not None,
                'checked_out': appt.checked_out_at is not None
            })
    
    # Serialize leave balances
    leave_balances_data = [
        {
            'type': lb.leave_type,
            'total': lb.total_days,
            'used': lb.used_days,
            'remaining': lb.total_days - lb.used_days
        }
        for lb in leave_balances
    ]
    
    return render_template('employee/dashboard.html', 
                           leave_requests=leave_requests, 
                           documents=documents,
                           leave_balances=leave_balances,
                           active_time_entry=active_time_entry,
                           recent_time_entries=recent_time_entries,
                           shared_docs_count=shared_docs_count,
                           leave_form=leave_form,
                           doc_form=doc_form,
                           time_form=time_form,
                           profile_form=profile_form,
                           estimator=estimator,
                           initial_stats_json=json.dumps(initial_stats),
                           upcoming_appointments_json=json.dumps(upcoming_appointments),
                           leave_balances_json=json.dumps(leave_balances_data))


@employee_bp.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    """JSON API for dashboard statistics - used by React component."""
    today = datetime.utcnow().date()
    now = datetime.utcnow()
    
    # Clock status
    active_time_entry = TimeEntry.query.filter_by(
        user_id=current_user.id,
        date=today,
        clock_out=None
    ).first()
    
    stats = {
        'is_clocked_in': active_time_entry is not None,
        'clock_in_time': active_time_entry.clock_in.isoformat() if active_time_entry else None,
        'today_appointments': 0,
        'week_appointments': 0,
        'pending_leave': 0,
        'hours_this_week': 0,
    }
    
    # Estimator appointments
    estimator = getattr(current_user, 'estimator_profile', None)
    if estimator:
        today_start = datetime(now.year, now.month, now.day)
        today_end = today_start + timedelta(days=1)
        week_end = today_start + timedelta(days=7)
        
        stats['today_appointments'] = Appointment.query.filter(
            Appointment.estimator_id == estimator.id,
            Appointment.preferred_date_time >= today_start,
            Appointment.preferred_date_time < today_end
        ).count()
        
        stats['week_appointments'] = Appointment.query.filter(
            Appointment.estimator_id == estimator.id,
            Appointment.preferred_date_time >= today_start,
            Appointment.preferred_date_time < week_end
        ).count()
    
    # Leave
    stats['pending_leave'] = LeaveRequest.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).count()
    
    # Hours
    week_start = today - timedelta(days=today.weekday())
    week_entries = TimeEntry.query.filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.date >= week_start
    ).all()
    stats['hours_this_week'] = round(sum(e.duration_minutes or 0 for e in week_entries) / 60, 1)
    
    return jsonify(stats)


# ============================================================================
# JSON API Endpoints for React Dashboard
# ============================================================================

@employee_bp.route('/api/clock-in', methods=['POST'])
@login_required
def api_clock_in():
    """JSON API: Clock in for the day."""
    today = datetime.utcnow().date()
    now = datetime.utcnow()
    
    # Check if already clocked in
    existing = TimeEntry.query.filter_by(
        user_id=current_user.id,
        date=today,
        clock_out=None
    ).first()
    
    if existing:
        return jsonify({
            'success': False,
            'message': 'You are already clocked in.',
            'clock_in_time': existing.clock_in.isoformat()
        })
    
    entry = TimeEntry(
        user_id=current_user.id,
        clock_in=now,
        date=today
    )
    db.session.add(entry)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Clocked in at {now.strftime("%H:%M")}.',
        'clock_in_time': now.isoformat()
    })


@employee_bp.route('/api/clock-out', methods=['POST'])
@login_required
def api_clock_out():
    """JSON API: Clock out for the day."""
    today = datetime.utcnow().date()
    now = datetime.utcnow()
    
    entry = TimeEntry.query.filter_by(
        user_id=current_user.id,
        date=today,
        clock_out=None
    ).first()
    
    if not entry:
        return jsonify({
            'success': False,
            'message': 'You are not clocked in.'
        })
    
    entry.clock_out = now
    entry.duration_minutes = entry.calculate_duration()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Clocked out at {now.strftime("%H:%M")}. Total: {entry.duration_minutes} minutes.',
        'duration_minutes': entry.duration_minutes
    })


@employee_bp.route('/api/leave-balances')
@login_required
def api_leave_balances():
    """JSON API: Get leave balances and requests."""
    current_year = datetime.utcnow().year
    balances = LeaveBalance.query.filter_by(user_id=current_user.id, year=current_year).all()
    
    # Get all leave requests for this year
    year_start = datetime(current_year, 1, 1).date()
    year_end = datetime(current_year, 12, 31).date()
    leave_requests = LeaveRequest.query.filter(
        LeaveRequest.user_id == current_user.id,
        LeaveRequest.start_date >= year_start,
        LeaveRequest.start_date <= year_end
    ).order_by(LeaveRequest.start_date.desc()).all()
    
    return jsonify({
        'year': current_year,
        'balances': [
            {
                'id': lb.id,
                'leave_type': lb.leave_type,
                'total_days': lb.total_days,
                'used_days': lb.used_days,
                'remaining_days': lb.total_days - lb.used_days
            }
            for lb in balances
        ],
        'requests': [
            {
                'id': lr.id,
                'leave_type': lr.leave_type,
                'start_date': lr.start_date.isoformat() if lr.start_date else None,
                'end_date': lr.end_date.isoformat() if lr.end_date else None,
                'status': lr.status,
                'reason': lr.reason,
                'created_at': lr.created_at.isoformat() if lr.created_at else None
            }
            for lr in leave_requests
        ]
    })


@employee_bp.route('/api/time-history')
@login_required
def api_time_history():
    """JSON API: Get time entries for a given period."""
    month = request.args.get('month', datetime.utcnow().month, type=int)
    year = request.args.get('year', datetime.utcnow().year, type=int)
    
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    entries = TimeEntry.query.filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.date >= start_date,
        TimeEntry.date < end_date
    ).order_by(TimeEntry.date.desc()).all()
    
    # Calculate totals
    total_minutes = sum(e.duration_minutes or 0 for e in entries)
    total_hours = round(total_minutes / 60, 2)
    
    return jsonify({
        'month': month,
        'year': year,
        'month_name': ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December'][month - 1],
        'entries': [
            {
                'id': e.id,
                'date': e.date.isoformat() if e.date else None,
                'clock_in': e.clock_in.strftime('%H:%M') if e.clock_in else None,
                'clock_out': e.clock_out.strftime('%H:%M') if e.clock_out else None,
                'duration_minutes': e.duration_minutes,
                'notes': e.notes,
                'is_active': e.clock_out is None
            }
            for e in entries
        ],
        'summary': {
            'total_hours': total_hours,
            'total_minutes': total_minutes,
            'days_worked': len([e for e in entries if e.duration_minutes]),
            'avg_hours_per_day': round(total_hours / len([e for e in entries if e.duration_minutes]), 2) if [e for e in entries if e.duration_minutes] else 0
        }
    })


# ============================================================================
# Phase 5: Leave Management
# ============================================================================

@employee_bp.route('/leave/request', methods=['GET', 'POST'])
@login_required
def request_leave():
    """Enhanced leave request with leave type selection."""
    form = LeaveRequestForm()
    
    if form.validate_on_submit():
        leave = LeaveRequest(
            user_id=current_user.id,
            leave_type=form.leave_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            reason=form.reason.data
        )
        db.session.add(leave)
        db.session.commit()
        flash('Leave request submitted successfully.', 'success')
        return redirect(url_for('employee.dashboard'))
    
    # Handle GET or form errors via POST with validation failures
    if request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('employee.dashboard'))


@employee_bp.route('/leave/balances')
@login_required
def leave_balances():
    """View leave balances by type."""
    current_year = datetime.utcnow().year
    balances = LeaveBalance.query.filter_by(user_id=current_user.id, year=current_year).all()
    
    # Get all leave requests for this year
    year_start = datetime(current_year, 1, 1).date()
    year_end = datetime(current_year, 12, 31).date()
    leave_requests = LeaveRequest.query.filter(
        LeaveRequest.user_id == current_user.id,
        LeaveRequest.start_date >= year_start,
        LeaveRequest.start_date <= year_end
    ).order_by(LeaveRequest.start_date).all()
    
    return render_template('employee/leave_balances.html', 
                           balances=balances, 
                           leave_requests=leave_requests,
                           year=current_year)


# ============================================================================
# Phase 5: Document Management
# ============================================================================

@employee_bp.route('/docs/upload', methods=['POST'])
@login_required
def upload_doc():
    """Enhanced document upload with category and expiration."""
    form = DocumentUploadForm()
    
    if form.validate_on_submit():
        file = form.file.data
        file_data = file.read()
        encrypted = encrypt_data(file_data)
        
        doc = EncryptedDocument(
            user_id=current_user.id,
            title=form.title.data,
            blob_data=encrypted,
            category=form.category.data,
            expires_at=form.expires_at.data,
            requires_signature=form.requires_signature.data,
            mimetype=file.mimetype,
            original_filename=file.filename
        )
        db.session.add(doc)
        db.session.commit()
        flash('Document uploaded and encrypted.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('employee.dashboard'))


@employee_bp.route('/docs/view/<int:doc_id>')
@login_required
def view_doc(doc_id):
    """View/download encrypted document with share permission check."""
    doc = EncryptedDocument.query.get_or_404(doc_id)
    
    # Check permissions: owner, admin, or shared with user
    has_access = False
    if doc.user_id == current_user.id:
        has_access = True
    elif current_user.has_role('admin'):
        has_access = True
    else:
        # Check if shared with this user
        share = DocumentShare.query.filter_by(
            document_id=doc_id,
            shared_with_user_id=current_user.id
        ).first()
        if share:
            has_access = True
        else:
            # Check if shared with any of user's roles
            for role in current_user.roles:
                role_share = DocumentShare.query.filter_by(
                    document_id=doc_id,
                    shared_with_role=role.name
                ).first()
                if role_share:
                    has_access = True
                    break
    
    if not has_access:
        abort(403)
    
    decrypted_data = decrypt_data(doc.blob_data)
    
    download_name = doc.original_filename or doc.title
    if not '.' in download_name:
        download_name += '.bin'
    
    return send_file(
        io.BytesIO(decrypted_data),
        download_name=download_name,
        mimetype=doc.mimetype or 'application/octet-stream',
        as_attachment=True
    )


@employee_bp.route('/docs/<int:doc_id>/share', methods=['GET', 'POST'])
@login_required
def share_doc(doc_id):
    """Share a document with another user or role."""
    doc = EncryptedDocument.query.get_or_404(doc_id)
    
    # Only owner or admin can share
    if doc.user_id != current_user.id and not current_user.has_role('admin'):
        abort(403)
    
    form = DocumentShareForm()
    
    if form.validate_on_submit():
        share = DocumentShare(
            document_id=doc_id,
            shared_by_id=current_user.id,
            permissions=form.permissions.data
        )
        
        if form.share_type.data == 'user' and form.shared_with_user_id.data:
            share.shared_with_user_id = form.shared_with_user_id.data
        elif form.share_type.data == 'role' and form.shared_with_role.data:
            share.shared_with_role = form.shared_with_role.data
        else:
            flash('Please select a user or role to share with.', 'error')
            return redirect(url_for('employee.share_doc', doc_id=doc_id))
        
        db.session.add(share)
        db.session.commit()
        flash('Document shared successfully.', 'success')
        return redirect(url_for('employee.dashboard'))
    
    existing_shares = DocumentShare.query.filter_by(document_id=doc_id).all()
    
    return render_template('employee/share_doc.html', 
                           doc=doc, 
                           form=form, 
                           existing_shares=existing_shares)


@employee_bp.route('/docs/shared-with-me')
@login_required
def shared_docs():
    """View documents shared with the current user."""
    # Direct user shares
    user_shares = DocumentShare.query.filter_by(shared_with_user_id=current_user.id).all()
    
    # Role-based shares
    role_names = [role.name for role in current_user.roles]
    role_shares = DocumentShare.query.filter(DocumentShare.shared_with_role.in_(role_names)).all() if role_names else []
    
    # Combine and dedupe
    all_shares = list(user_shares) + [s for s in role_shares if s not in user_shares]
    
    return render_template('employee/shared_docs.html', shares=all_shares)


@employee_bp.route('/docs/<int:doc_id>/sign', methods=['POST'])
@login_required
def sign_doc(doc_id):
    """Sign/acknowledge a document."""
    doc = EncryptedDocument.query.get_or_404(doc_id)
    
    # Check if user has access
    share = DocumentShare.query.filter_by(
        document_id=doc_id,
        shared_with_user_id=current_user.id
    ).first()
    
    if not share and doc.user_id != current_user.id:
        abort(403)
    
    if not doc.requires_signature:
        flash('This document does not require a signature.', 'info')
    elif doc.signed_by_id:
        flash('Document has already been signed.', 'warning')
    else:
        doc.signed_by_id = current_user.id
        doc.signed_at = datetime.utcnow()
        db.session.commit()
        flash('Document signed successfully.', 'success')
    
    return redirect(url_for('employee.shared_docs'))


# ============================================================================
# Phase 5: Employee Directory
# ============================================================================

@employee_bp.route('/directory')
@login_required
def directory():
    """Employee directory with search and filtering."""
    form = EmployeeSearchForm()
    
    query = User.query.filter(User.id != current_user.id)  # Exclude self
    
    # Filter by search query (skills)
    q = request.args.get('q', '').strip()
    if q:
        query = query.filter(User.skills.ilike(f'%{q}%'))
        form.q.data = q
    
    # Filter by department
    department = request.args.get('department', '').strip()
    if department:
        query = query.filter(User.department == department)
        form.department.data = department
    
    employees = query.order_by(User.last_name, User.first_name).all()
    
    return render_template('employee/directory.html', employees=employees, form=form)


@employee_bp.route('/org-chart')
@login_required
def org_chart():
    """Organization chart visualization."""
    # Get all users with their reports_to relationships
    users = User.query.all()
    
    # Build hierarchy
    def build_tree(user):
        return {
            'id': user.id,
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
            'title': user.job_title or 'Employee',
            'department': user.department,
            'children': [build_tree(report) for report in user.direct_reports]
        }
    
    # Find root nodes (users without managers)
    roots = [u for u in users if not u.reports_to_id]
    org_data = [build_tree(root) for root in roots]
    
    return render_template('employee/org_chart.html', org_data=org_data)


# ============================================================================
# Phase 5: Time & Attendance
# ============================================================================

@employee_bp.route('/time/clock-in', methods=['POST'])
@login_required
def clock_in():
    """Clock in for the day."""
    today = datetime.utcnow().date()
    now = datetime.utcnow()
    
    # Check if already clocked in
    existing = TimeEntry.query.filter_by(
        user_id=current_user.id,
        date=today,
        clock_out=None
    ).first()
    
    if existing:
        flash('You are already clocked in.', 'warning')
    else:
        form = TimeEntryForm()
        entry = TimeEntry(
            user_id=current_user.id,
            clock_in=now,
            date=today,
            notes=form.notes.data if form.validate_on_submit() else None
        )
        db.session.add(entry)
        db.session.commit()
        flash(f'Clocked in at {now.strftime("%H:%M")}.', 'success')
    
    return redirect(url_for('employee.dashboard'))


@employee_bp.route('/time/clock-out', methods=['POST'])
@login_required
def clock_out():
    """Clock out for the day."""
    today = datetime.utcnow().date()
    now = datetime.utcnow()
    
    entry = TimeEntry.query.filter_by(
        user_id=current_user.id,
        date=today,
        clock_out=None
    ).first()
    
    if not entry:
        flash('You are not clocked in.', 'warning')
    else:
        entry.clock_out = now
        entry.duration_minutes = entry.calculate_duration()
        db.session.commit()
        flash(f'Clocked out at {now.strftime("%H:%M")}. Total: {entry.duration_minutes} minutes.', 'success')
    
    return redirect(url_for('employee.dashboard'))


@employee_bp.route('/time/history')
@login_required
def time_history():
    """View timesheet history."""
    # Get date range from params or default to current month
    month = request.args.get('month', datetime.utcnow().month, type=int)
    year = request.args.get('year', datetime.utcnow().year, type=int)
    
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    entries = TimeEntry.query.filter(
        TimeEntry.user_id == current_user.id,
        TimeEntry.date >= start_date,
        TimeEntry.date < end_date
    ).order_by(TimeEntry.date.desc()).all()
    
    # Calculate totals
    total_minutes = sum(e.duration_minutes or 0 for e in entries)
    total_hours = total_minutes / 60
    
    return render_template('employee/timesheet.html', 
                           entries=entries, 
                           month=month, 
                           year=year,
                           total_hours=total_hours)


# ============================================================================
# Phase 2: Staff Self-Service Calendar (existing)
# ============================================================================

@employee_bp.route('/calendar')
@login_required
def calendar():
    """
    Staff view of their assigned appointments.
    Shows only appointments for the estimator linked to current user.
    """
    estimator = None
    if hasattr(current_user, 'estimator_profile') and current_user.estimator_profile:
        estimator = current_user.estimator_profile
    
    if not estimator:
        flash('Your user account is not linked to an estimator profile. Please contact an admin.', 'warning')
        return render_template('employee/calendar.html', estimator=None, appointments=[])
    
    now = datetime.utcnow()
    appointments = Appointment.query.filter(
        Appointment.estimator_id == estimator.id,
        Appointment.preferred_date_time >= now - timedelta(days=1)
    ).order_by(Appointment.preferred_date_time).all()
    
    pending_reschedules = RescheduleRequest.query.filter_by(
        user_id=current_user.id,
        status='pending'
    ).all()
    
    # Serialize pending reschedules for React component
    import json
    pending_reschedules_json = json.dumps([
        {
            'id': rr.id,
            'appointment_id': rr.appointment_id,
            'proposed_datetime': rr.proposed_datetime.strftime('%Y-%m-%d %H:%M'),
            'status': rr.status
        }
        for rr in pending_reschedules
    ])
    
    notes_form = AppointmentNotesForm()
    reschedule_form = RescheduleRequestForm()
    csrf_form = CSRFTokenForm()
    
    return render_template(
        'employee/calendar.html',
        estimator=estimator,
        appointments=appointments,
        pending_reschedules=pending_reschedules,
        pending_reschedules_json=pending_reschedules_json,
        notes_form=notes_form,
        reschedule_form=reschedule_form,
        csrf_form=csrf_form
    )


@employee_bp.route('/calendar/api/events')
@login_required
def calendar_events():
    """API endpoint for FullCalendar to fetch events."""
    if not hasattr(current_user, 'estimator_profile') or not current_user.estimator_profile:
        return jsonify([])
    
    estimator = current_user.estimator_profile
    
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    query = Appointment.query.filter(Appointment.estimator_id == estimator.id)
    
    if start_str and end_str:
        start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        query = query.filter(
            Appointment.preferred_date_time >= start_date,
            Appointment.preferred_date_time <= end_date
        )
    
    appointments = query.all()
    events = []
    
    for appt in appointments:
        duration = 60
        if appt.service and appt.service.duration_minutes:
            duration = appt.service.duration_minutes
        
        start = appt.preferred_date_time.isoformat() + 'Z'
        end = (appt.preferred_date_time + timedelta(minutes=duration)).isoformat() + 'Z'
        
        color = '#3788d8'
        if appt.checked_in_at and not appt.checked_out_at:
            color = '#28a745'
        elif appt.checked_out_at:
            color = '#6c757d'
        
        events.append({
            'id': appt.id,
            'title': f"{appt.first_name} {appt.last_name}",
            'start': start,
            'end': end,
            'color': color,
            'extendedProps': {
                'phone': appt.phone,
                'email': appt.email,
                'service': appt.service.name if appt.service else 'N/A',
                'status': appt.status,
                'staff_notes': appt.staff_notes or '',
                'checked_in': bool(appt.checked_in_at),
                'checked_out': bool(appt.checked_out_at)
            }
        })
    
    return jsonify(events)


@employee_bp.route('/appointment/<int:appointment_id>/notes', methods=['POST'])
@login_required
def update_notes(appointment_id):
    """Staff adds internal notes to an appointment."""
    appt = Appointment.query.get_or_404(appointment_id)
    
    if not current_user.estimator_profile or appt.estimator_id != current_user.estimator_profile.id:
        if not current_user.has_role('admin'):
            abort(403)
    
    form = AppointmentNotesForm()
    if form.validate_on_submit():
        appt.staff_notes = form.staff_notes.data
        db.session.commit()
        flash('Notes saved.', 'success')
    
    if request.headers.get('HX-Request'):
        return '<span class="text-success">✓ Saved</span>'
    
    return redirect(url_for('employee.calendar'))


@employee_bp.route('/appointment/<int:appointment_id>/checkin', methods=['POST'])
@login_required
def checkin(appointment_id):
    """Staff marks appointment as started."""
    appt = Appointment.query.get_or_404(appointment_id)
    
    if not current_user.estimator_profile or appt.estimator_id != current_user.estimator_profile.id:
        if not current_user.has_role('admin'):
            abort(403)
    
    if appt.checked_in_at:
        flash('Already checked in.', 'warning')
    else:
        appt.checked_in_at = datetime.utcnow()
        db.session.commit()
        flash('Checked in successfully.', 'success')
    
    if request.headers.get('HX-Request'):
        return f'<span class="badge badge-success">Checked in at {appt.checked_in_at.strftime("%H:%M")}</span>'
    
    return redirect(url_for('employee.calendar'))


@employee_bp.route('/appointment/<int:appointment_id>/checkout', methods=['POST'])
@login_required
def checkout(appointment_id):
    """Staff marks appointment as completed."""
    appt = Appointment.query.get_or_404(appointment_id)
    
    if not current_user.estimator_profile or appt.estimator_id != current_user.estimator_profile.id:
        if not current_user.has_role('admin'):
            abort(403)
    
    if not appt.checked_in_at:
        flash('Must check in before checking out.', 'warning')
    elif appt.checked_out_at:
        flash('Already checked out.', 'warning')
    else:
        appt.checked_out_at = datetime.utcnow()
        db.session.commit()
        flash('Checked out successfully.', 'success')
    
    if request.headers.get('HX-Request'):
        duration = (appt.checked_out_at - appt.checked_in_at).seconds // 60
        return f'<span class="badge badge-secondary">Completed ({duration} min)</span>'
    
    return redirect(url_for('employee.calendar'))


@employee_bp.route('/appointment/<int:appointment_id>/reschedule', methods=['POST'])
@login_required
def request_reschedule(appointment_id):
    """Staff requests reschedule for an appointment."""
    appt = Appointment.query.get_or_404(appointment_id)
    
    if not current_user.estimator_profile or appt.estimator_id != current_user.estimator_profile.id:
        if not current_user.has_role('admin'):
            abort(403)
    
    form = RescheduleRequestForm()
    if form.validate_on_submit():
        proposed_time = datetime.strptime(form.proposed_time.data, '%H:%M').time()
        proposed_datetime = datetime.combine(form.proposed_date.data, proposed_time)
        
        reschedule = RescheduleRequest(
            appointment_id=appointment_id,
            user_id=current_user.id,
            proposed_datetime=proposed_datetime,
            reason=form.reason.data
        )
        db.session.add(reschedule)
        db.session.commit()
        flash('Reschedule request submitted for admin approval.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('employee.calendar'))


# ============================================================================
# Profile Management
# ============================================================================

@employee_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Enhanced profile update with Phase 5 fields."""
    form = EmployeeProfileForm()
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.bio = form.bio.data
        current_user.skills = form.skills.data
        current_user.emergency_contacts = form.emergency_contacts.data
        current_user.job_title = form.job_title.data
        current_user.department = form.department.data
        
        db.session.commit()
        flash('Profile updated successfully.', 'success')
    else:
        # Fallback to form data for backwards compatibility
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.phone = request.form.get('phone')
        current_user.bio = request.form.get('bio')
        current_user.skills = request.form.get('skills')
        current_user.emergency_contacts = request.form.get('emergency_contacts')
        db.session.commit()
        flash('Profile updated successfully.', 'success')
    
    return redirect(url_for('employee.dashboard'))

