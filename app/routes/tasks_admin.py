"""
Phase 8: Task Queue Admin Routes

Admin dashboard for task queue management including:
- Task queue dashboard with status counts
- Dead letter queue management
- Cron task administration
- Worker status monitoring
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Task, CronTask, WorkerHeartbeat, db
from app.modules.decorators import role_required
from datetime import datetime, timedelta
from sqlalchemy import func

tasks_admin_bp = Blueprint('tasks_admin', __name__, url_prefix='/admin/tasks')


@tasks_admin_bp.route('/')
@login_required
@role_required('admin')
def dashboard():
    """Task queue dashboard with KPI cards and recent tasks."""
    now = datetime.utcnow()
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    # Status counts
    pending_count = Task.query.filter_by(status='pending').count()
    processing_count = Task.query.filter_by(status='processing').count()
    completed_count = Task.query.filter(
        Task.status == 'completed',
        Task.completed_at >= twenty_four_hours_ago
    ).count()
    failed_count = Task.query.filter(
        Task.status == 'failed',
        Task.completed_at >= twenty_four_hours_ago
    ).count()
    dead_letter_count = Task.query.filter_by(status='dead_letter').count()
    
    # Recent tasks (last 20)
    recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(20).all()
    
    # Active cron tasks
    cron_tasks = CronTask.query.filter_by(is_active=True).order_by(CronTask.next_run.asc()).all()
    
    # Worker status
    workers = WorkerHeartbeat.query.order_by(WorkerHeartbeat.last_heartbeat.desc()).all()
    
    return render_template('admin/tasks/dashboard.html',
        pending_count=pending_count,
        processing_count=processing_count,
        completed_count=completed_count,
        failed_count=failed_count,
        dead_letter_count=dead_letter_count,
        recent_tasks=recent_tasks,
        cron_tasks=cron_tasks,
        workers=workers,
        now=now
    )


@tasks_admin_bp.route('/queue')
@login_required
@role_required('admin')
def queue():
    """View pending and processing tasks."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    
    valid_statuses = ['pending', 'processing', 'completed', 'failed', 'dead_letter']
    if status not in valid_statuses:
        status = 'pending'
    
    tasks = Task.query.filter_by(status=status).order_by(
        Task.priority.desc(),
        Task.created_at.desc()
    ).paginate(page=page, per_page=50, error_out=False)
    
    # Get counts for tabs
    status_counts = {
        'pending': Task.query.filter_by(status='pending').count(),
        'processing': Task.query.filter_by(status='processing').count(),
        'completed': Task.query.filter_by(status='completed').count(),
        'failed': Task.query.filter_by(status='failed').count(),
        'dead_letter': Task.query.filter_by(status='dead_letter').count(),
    }
    
    return render_template('admin/tasks/queue.html',
        tasks=tasks,
        current_status=status,
        status_counts=status_counts
    )


@tasks_admin_bp.route('/dead-letter')
@login_required
@role_required('admin')
def dead_letter():
    """View and manage dead letter tasks."""
    page = request.args.get('page', 1, type=int)
    
    tasks = Task.query.filter_by(status='dead_letter').order_by(
        Task.completed_at.desc()
    ).paginate(page=page, per_page=50, error_out=False)
    
    return render_template('admin/tasks/dead_letter.html', tasks=tasks)


@tasks_admin_bp.route('/<int:task_id>/retry', methods=['POST'])
@login_required
@role_required('admin')
def retry_task(task_id):
    """Retry a dead letter or failed task."""
    task = Task.query.get_or_404(task_id)
    
    if task.status not in ['dead_letter', 'failed']:
        flash('Only failed or dead letter tasks can be retried.', 'warning')
        return redirect(url_for('tasks_admin.dead_letter'))
    
    # Reset task for retry
    task.status = 'pending'
    task.retry_count = 0
    task.next_retry_at = None
    task.error = None
    task.started_at = None
    task.completed_at = None
    
    db.session.commit()
    
    flash(f'Task {task.id} ({task.name}) has been queued for retry.', 'success')
    return redirect(url_for('tasks_admin.dead_letter'))


@tasks_admin_bp.route('/cron')
@login_required
@role_required('admin')
def cron_tasks():
    """View and manage cron tasks."""
    import json
    from app.forms import CSRFTokenForm
    
    tasks = CronTask.query.order_by(CronTask.name.asc()).all()
    form = CSRFTokenForm()
    
    # Serialize for AdminDataTable
    cron_tasks_json = json.dumps([{
        'id': cron.id,
        'name': f'<strong>{cron.name}</strong><br><small class="text-muted">{cron.description or ""}</small>' if cron.description else f'<strong>{cron.name}</strong>',
        'handler': f'<code>{cron.handler}</code>',
        'schedule': f'<span class="badge bg-info">{cron.schedule}</span>',
        'last_run': cron.last_run.strftime('%Y-%m-%d %H:%M') if cron.last_run else 'Never',
        'next_run': cron.next_run.strftime('%Y-%m-%d %H:%M') if cron.next_run else 'Not scheduled',
        'status': '<span class="badge bg-success">Active</span>' if cron.is_active else '<span class="badge bg-secondary">Disabled</span>',
        'actions': (
            f'<form action="{url_for("tasks_admin.toggle_cron", cron_id=cron.id)}" method="POST" style="display:inline;"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}"><button type="submit" class="btn btn-sm {"btn-outline-secondary" if cron.is_active else "btn-outline-success"}">{"Disable" if cron.is_active else "Enable"}</button></form> '
            f'<form action="{url_for("tasks_admin.run_cron_now", cron_id=cron.id)}" method="POST" style="display:inline;"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}"><button type="submit" class="btn btn-sm btn-outline-primary" title="Run Now"><i class="fas fa-play"></i> Run Now</button></form>'
        )
    } for cron in tasks])
    
    return render_template('admin/tasks/cron.html', cron_tasks=tasks, cron_tasks_json=cron_tasks_json)


@tasks_admin_bp.route('/cron/<int:cron_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_cron(cron_id):
    """Toggle cron task active status."""
    cron = CronTask.query.get_or_404(cron_id)
    cron.is_active = not cron.is_active
    db.session.commit()
    
    status = "enabled" if cron.is_active else "disabled"
    flash(f'Cron task "{cron.name}" has been {status}.', 'success')
    return redirect(url_for('tasks_admin.cron_tasks'))


@tasks_admin_bp.route('/cron/<int:cron_id>/run-now', methods=['POST'])
@login_required
@role_required('admin')
def run_cron_now(cron_id):
    """Trigger immediate execution of a cron task."""
    cron = CronTask.query.get_or_404(cron_id)
    
    # Create a Task for immediate execution
    task = Task(
        name=cron.handler,
        payload=cron.payload or {},
        priority=10,  # High priority for manual triggers
    )
    db.session.add(task)
    
    # Update last run time
    cron.last_run = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Cron task "{cron.name}" has been queued for immediate execution.', 'success')
    return redirect(url_for('tasks_admin.cron_tasks'))


@tasks_admin_bp.route('/worker-status')
@login_required
@role_required('admin')
def worker_status():
    """View worker status and health."""
    workers = WorkerHeartbeat.query.order_by(WorkerHeartbeat.last_heartbeat.desc()).all()
    now = datetime.utcnow()
    
    return render_template('admin/tasks/worker_status.html',
        workers=workers,
        now=now
    )


@tasks_admin_bp.route('/api/stats')
@login_required
@role_required('admin')
def api_stats():
    """JSON API for task statistics (for live updates)."""
    now = datetime.utcnow()
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    # Get active workers (heartbeat within last 2 minutes)
    two_minutes_ago = now - timedelta(minutes=2)
    active_workers = WorkerHeartbeat.query.filter(
        WorkerHeartbeat.last_heartbeat >= two_minutes_ago
    ).count()
    
    return jsonify({
        'pending': Task.query.filter_by(status='pending').count(),
        'processing': Task.query.filter_by(status='processing').count(),
        'completed_24h': Task.query.filter(
            Task.status == 'completed',
            Task.completed_at >= twenty_four_hours_ago
        ).count(),
        'failed_24h': Task.query.filter(
            Task.status == 'failed',
            Task.completed_at >= twenty_four_hours_ago
        ).count(),
        'dead_letter': Task.query.filter_by(status='dead_letter').count(),
        'active_workers': active_workers,
        'timestamp': now.isoformat()
    })


@tasks_admin_bp.route('/<int:task_id>')
@login_required
@role_required('admin')
def task_detail(task_id):
    """View task details."""
    task = Task.query.get_or_404(task_id)
    return render_template('admin/tasks/detail.html', task=task)
