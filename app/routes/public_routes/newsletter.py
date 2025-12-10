from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models import Newsletter, UnsubscribedEmail, ContactFormSubmission, User, Task, db
from app.modules.decorators import role_required
from app.forms import CSRFTokenForm
from datetime import datetime
import json

newsletter_bp = Blueprint('newsletter', __name__, url_prefix='/admin/newsletter')

@newsletter_bp.route('/')
@login_required
@role_required('admin')
def index():
    newsletters = Newsletter.query.order_by(Newsletter.created_at.desc()).all()
    form = CSRFTokenForm()
    
    # Status color mapping
    status_colors = {'sent': 'success', 'queued': 'warning', 'draft': 'secondary'}
    
    # Serialize for AdminDataTable
    newsletters_json = json.dumps([{
        'id': n.id,
        'subject': n.subject,
        'status': f'<span class="badge bg-{status_colors.get(n.status, "secondary")}">{n.status}</span>',
        'tags': ', '.join(n.recipient_tags) if n.recipient_tags else '-',
        'created_at': n.created_at.strftime('%Y-%m-%d') if n.created_at else '-',
        'actions': (
            f'<form action="{url_for("newsletter.send", id=n.id)}" method="POST" class="d-inline" onsubmit="return confirm(\'Broadcast this newsletter?\');"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}" /><button type="submit" class="btn btn-sm btn-success"><i class="fas fa-paper-plane"></i> Send</button></form> ' if n.status == 'draft' else ''
        ) + f'<a href="{url_for("newsletter.view_online", id=n.id)}" class="btn btn-sm btn-info" target="_blank"><i class="fas fa-eye"></i> View</a>'
    } for n in newsletters])
    
    return render_template('admin/newsletter/index.html', newsletters=newsletters, newsletters_json=newsletters_json)

@newsletter_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    if request.method == 'POST':
        subject = request.form.get('subject')
        content = request.form.get('content') # Markdown or HTML from CKEditor
        tags = request.form.get('tags') # Comma separated
        
        recipient_tags_list = [t.strip() for t in tags.split(',')] if tags else []
        
        newsletter = Newsletter(
            subject=subject,
            content=content,
            recipient_tags=recipient_tags_list,
            status='draft'
        )
        db.session.add(newsletter)
        db.session.commit()
        flash('Newsletter draft created.', 'success')
        return redirect(url_for('newsletter.index'))
        
    return render_template('admin/newsletter/create.html')

@newsletter_bp.route('/<int:id>/send', methods=['POST'])
@login_required
@role_required('admin')
def send(id):
    newsletter = Newsletter.query.get_or_404(id)
    if newsletter.status == 'sent':
        flash('Newsletter already sent.', 'warning')
        return redirect(url_for('newsletter.index'))
        
    # Trigger background task
    task = Task(name='send_newsletter_broadcast', payload={'newsletter_id': newsletter.id})
    db.session.add(task)
    
    newsletter.status = 'queued'
    db.session.commit()
    
    flash('Newsletter queued for sending!', 'success')
    return redirect(url_for('newsletter.index'))

# Public Unsubscribe Route
@newsletter_bp.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    # This route might be outside admin prefix ideally, but we can register it separately or handle redirect
    # Wait, blueprint has prefix /admin/newsletter. 
    # Unsubscribe link should generally be public.
    # We should move this to main_routes or create a new blueprint for public marketing actions.
    # For now, I'll put it here but users will access /admin/newsletter/unsubscribe?email=... which is weird.
    # I'll register a separate route in main_routes or a new public blueprint.
    pass

# Public route for view in browser
@newsletter_bp.route('/<int:id>/view')
def view_online(id):
    newsletter = Newsletter.query.get_or_404(id)
    return render_template('admin/newsletter/view.html', newsletter=newsletter)
