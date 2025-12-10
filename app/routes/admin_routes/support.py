"""
Phase 23: Support Ticketing System Routes

Public and admin routes for customer support ticket management.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.models import SupportTicket, TicketReply, User, Task
from app.database import db
from app.modules.auth_manager import admin_required
from app.modules.decorators import role_required
from app.modules.audit import log_audit_event
from app.forms import CSRFTokenForm
from datetime import datetime
import json

support_bp = Blueprint('support', __name__, url_prefix='/support')


# =============================================================================
# Public Routes (Customer-facing)
# =============================================================================

@support_bp.route('/')
def index():
    """Support center landing page."""
    return render_template('support/index.html')


@support_bp.route('/new', methods=['GET', 'POST'])
def create_ticket():
    """Create a new support ticket (logged in or guest)."""
    form = CSRFTokenForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        subject = request.form.get('subject', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'general')
        priority = request.form.get('priority', 'normal')
        
        if not subject or not description:
            flash('Subject and description are required.', 'error')
            return render_template('support/create.html', form=form)
        
        ticket = SupportTicket(
            ticket_number=SupportTicket.generate_ticket_number(),
            subject=subject,
            description=description,
            category=category,
            priority=priority,
        )
        
        # Set customer info
        if current_user.is_authenticated:
            ticket.user_id = current_user.id
            ticket.email = current_user.email
        else:
            ticket.email = request.form.get('email', '').strip()
            ticket.name = request.form.get('name', '').strip()
            if not ticket.email:
                flash('Email is required for guest submissions.', 'error')
                return render_template('support/create.html', form=form)
        
        db.session.add(ticket)
        db.session.commit()
        
        # Queue notification task
        task = Task(
            name='new_support_ticket',
            payload={
                'ticket_id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'subject': ticket.subject,
                'email': ticket.get_customer_email()
            }
        )
        db.session.add(task)
        db.session.commit()
        
        flash(f'Ticket {ticket.ticket_number} created successfully! We\'ll respond soon.', 'success')
        
        if current_user.is_authenticated:
            return redirect(url_for('support.view_ticket', ticket_number=ticket.ticket_number))
        else:
            return redirect(url_for('support.ticket_submitted', ticket_number=ticket.ticket_number))
    
    return render_template('support/create.html', form=form)


@support_bp.route('/ticket/<ticket_number>')
def view_ticket(ticket_number):
    """View a single support ticket."""
    ticket = SupportTicket.query.filter_by(ticket_number=ticket_number).first_or_404()
    
    # Access control: user must own ticket or be admin
    if current_user.is_authenticated:
        if ticket.user_id != current_user.id and not current_user.has_role('admin'):
            abort(403)
    else:
        # Guest access - maybe via email link with token (future enhancement)
        abort(403)
    
    form = CSRFTokenForm()
    replies = ticket.replies.filter_by(is_internal=False).all()
    
    return render_template('support/view.html', ticket=ticket, replies=replies, form=form)


@support_bp.route('/ticket/<ticket_number>/reply', methods=['POST'])
@login_required
def add_reply(ticket_number):
    """Add a reply to a ticket (customer or staff)."""
    ticket = SupportTicket.query.filter_by(ticket_number=ticket_number).first_or_404()
    
    # Access control
    is_staff = current_user.has_role('admin') or current_user.has_role('support')
    if ticket.user_id != current_user.id and not is_staff:
        abort(403)
    
    content = request.form.get('content', '').strip()
    if not content:
        flash('Reply cannot be empty.', 'error')
        return redirect(url_for('support.view_ticket', ticket_number=ticket_number))
    
    reply = TicketReply(
        ticket_id=ticket.id,
        user_id=current_user.id,
        content=content,
        is_from_customer=not is_staff,
        is_internal=False
    )
    db.session.add(reply)
    
    # Update ticket timestamps
    ticket.updated_at = datetime.utcnow()
    if is_staff and not ticket.first_response_at:
        ticket.first_response_at = datetime.utcnow()
    
    # If customer replied on waiting ticket, move to in_progress
    if ticket.status == 'waiting' and not is_staff:
        ticket.status = 'in_progress'
    
    db.session.commit()
    
    flash('Reply added successfully.', 'success')
    
    if is_staff:
        return redirect(url_for('support.admin_view_ticket', ticket_id=ticket.id))
    return redirect(url_for('support.view_ticket', ticket_number=ticket_number))


@support_bp.route('/submitted/<ticket_number>')
def ticket_submitted(ticket_number):
    """Confirmation page for guest ticket submission."""
    ticket = SupportTicket.query.filter_by(ticket_number=ticket_number).first_or_404()
    return render_template('support/submitted.html', ticket=ticket)


@support_bp.route('/my-tickets')
@login_required
def my_tickets():
    """List user's support tickets."""
    tickets = SupportTicket.query.filter_by(user_id=current_user.id)\
        .order_by(SupportTicket.created_at.desc()).all()
    return render_template('support/my_tickets.html', tickets=tickets)


# =============================================================================
# Admin Routes
# =============================================================================

@support_bp.route('/admin')
@login_required
@role_required('admin')
def admin_queue():
    """Admin ticket queue with filtering."""
    status_filter = request.args.get('status', 'open')
    priority_filter = request.args.get('priority')
    
    query = SupportTicket.query
    
    if status_filter and status_filter != 'all':
        if status_filter == 'active':
            query = query.filter(SupportTicket.status.in_(['open', 'in_progress', 'waiting']))
        else:
            query = query.filter_by(status=status_filter)
    
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    
    # Sort by priority (urgent first) then date
    priority_order = db.case(
        (SupportTicket.priority == 'urgent', 1),
        (SupportTicket.priority == 'high', 2),
        (SupportTicket.priority == 'normal', 3),
        (SupportTicket.priority == 'low', 4),
        else_=5
    )
    tickets = query.order_by(priority_order, SupportTicket.created_at.desc()).all()
    
    # Stats
    stats = {
        'total': SupportTicket.query.count(),
        'open': SupportTicket.query.filter_by(status='open').count(),
        'in_progress': SupportTicket.query.filter_by(status='in_progress').count(),
        'waiting': SupportTicket.query.filter_by(status='waiting').count(),
        'resolved': SupportTicket.query.filter_by(status='resolved').count(),
    }
    
    form = CSRFTokenForm()
    
    # Serialize for AdminDataTable
    tickets_json = json.dumps([{
        'id': t.id,
        'ticket_number': f'<a href="{url_for("support.admin_view_ticket", ticket_id=t.id)}"><strong>{t.ticket_number}</strong></a>',
        'subject': t.subject[:50] + ('...' if len(t.subject) > 50 else ''),
        'customer': t.get_customer_display_name(),
        'priority': f'<span class="badge bg-{"danger" if t.priority == "urgent" else "warning" if t.priority == "high" else "info" if t.priority == "normal" else "secondary"}">{t.priority}</span>',
        'status': f'<span class="badge bg-{"success" if t.status == "resolved" else "primary" if t.status == "in_progress" else "warning" if t.status == "waiting" else "info"}">{t.status.replace("_", " ")}</span>',
        'created': t.created_at.strftime('%Y-%m-%d %H:%M'),
        'assigned': t.assigned_to.username if t.assigned_to else '<em class="text-muted">Unassigned</em>',
    } for t in tickets])
    
    return render_template('support/admin/queue.html', 
        tickets=tickets, 
        tickets_json=tickets_json,
        stats=stats, 
        status_filter=status_filter,
        form=form
    )


@support_bp.route('/admin/ticket/<int:ticket_id>')
@login_required
@role_required('admin')
def admin_view_ticket(ticket_id):
    """Admin view/manage a single ticket."""
    ticket = SupportTicket.query.get_or_404(ticket_id)
    form = CSRFTokenForm()
    
    # Get all replies including internal notes
    replies = ticket.replies.all()
    
    # Get agents for assignment dropdown
    agents = User.query.join(User.roles).filter_by(name='admin').all()
    
    return render_template('support/admin/view.html', 
        ticket=ticket, 
        replies=replies, 
        agents=agents,
        form=form
    )


@support_bp.route('/admin/ticket/<int:ticket_id>/update', methods=['POST'])
@login_required
@role_required('admin')
def admin_update_ticket(ticket_id):
    """Update ticket status/assignment."""
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    action = request.form.get('action')
    
    if action == 'assign':
        assigned_to_id = request.form.get('assigned_to_id', type=int)
        if assigned_to_id == 0:
            ticket.assigned_to_id = None
        else:
            ticket.assigned_to_id = assigned_to_id
        flash('Ticket assignment updated.', 'success')
    
    elif action == 'status':
        new_status = request.form.get('status')
        if new_status in ['open', 'in_progress', 'waiting', 'resolved', 'closed']:
            old_status = ticket.status
            ticket.status = new_status
            
            if new_status == 'resolved' and not ticket.resolved_at:
                ticket.resolved_at = datetime.utcnow()
            if new_status == 'closed' and not ticket.closed_at:
                ticket.closed_at = datetime.utcnow()
            
            flash(f'Ticket status changed from {old_status} to {new_status}.', 'success')
    
    elif action == 'priority':
        new_priority = request.form.get('priority')
        if new_priority in ['low', 'normal', 'high', 'urgent']:
            ticket.priority = new_priority
            flash('Ticket priority updated.', 'success')
    
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    
    log_audit_event(current_user.id, f'ticket_{action}', 'SupportTicket', ticket_id, 
                   {'action': action}, request.remote_addr)
    
    return redirect(url_for('support.admin_view_ticket', ticket_id=ticket_id))


@support_bp.route('/admin/ticket/<int:ticket_id>/internal-note', methods=['POST'])
@login_required
@role_required('admin')
def add_internal_note(ticket_id):
    """Add internal staff note (not visible to customer)."""
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    content = request.form.get('content', '').strip()
    if not content:
        flash('Note cannot be empty.', 'error')
        return redirect(url_for('support.admin_view_ticket', ticket_id=ticket_id))
    
    reply = TicketReply(
        ticket_id=ticket.id,
        user_id=current_user.id,
        content=content,
        is_from_customer=False,
        is_internal=True  # Internal note
    )
    db.session.add(reply)
    db.session.commit()
    
    flash('Internal note added.', 'success')
    return redirect(url_for('support.admin_view_ticket', ticket_id=ticket_id))


@support_bp.route('/admin/ticket/<int:ticket_id>/reply', methods=['POST'])
@login_required
@role_required('admin')
def admin_reply(ticket_id):
    """Admin reply to ticket (visible to customer)."""
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    content = request.form.get('content', '').strip()
    if not content:
        flash('Reply cannot be empty.', 'error')
        return redirect(url_for('support.admin_view_ticket', ticket_id=ticket_id))
    
    reply = TicketReply(
        ticket_id=ticket.id,
        user_id=current_user.id,
        content=content,
        is_from_customer=False,
        is_internal=False
    )
    db.session.add(reply)
    
    # Update first response time if this is the first staff reply
    if not ticket.first_response_at:
        ticket.first_response_at = datetime.utcnow()
    
    # Move to in_progress if open
    if ticket.status == 'open':
        ticket.status = 'in_progress'
    
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Queue email notification to customer
    task = Task(
        name='ticket_reply_notification',
        payload={
            'ticket_id': ticket.id,
            'reply_id': reply.id,
            'email': ticket.get_customer_email()
        }
    )
    db.session.add(task)
    db.session.commit()
    
    flash('Reply sent to customer.', 'success')
    return redirect(url_for('support.admin_view_ticket', ticket_id=ticket_id))
