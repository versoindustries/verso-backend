"""
Phase 25: Backup Administration Routes

Admin routes for managing backups, schedules, and restores.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required, current_user

from app.database import db
from app.models import Backup, BackupSchedule, FeatureFlag, DeploymentLog
from app.modules.backup_service import backup_service, BackupScheduler
from app.modules.deployment import feature_flags, deployment_manager


backup_bp = Blueprint('backup', __name__, url_prefix='/admin/backups')


def admin_required(f):
    """Decorator to require admin role."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# Backup Management Routes
# ============================================================================

@backup_bp.route('/')
@login_required
@admin_required
def list_backups():
    """List all backups."""
    import json
    
    backup_type = request.args.get('type')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = Backup.query.order_by(Backup.started_at.desc())
    if backup_type:
        query = query.filter(Backup.backup_type == backup_type)
    
    backups = query.paginate(page=page, per_page=per_page)
    schedules = BackupSchedule.query.filter_by(is_active=True).all()
    
    # Helper functions for generating HTML
    def get_type_badge(btype):
        color = 'primary' if btype == 'database' else 'success' if btype == 'media' else 'warning'
        return f'<span class="badge bg-{color}">{btype}</span>'
    
    def get_status_badge(status):
        color_map = {'completed': 'success', 'in_progress': 'info', 'failed': 'danger'}
        color = color_map.get(status, 'secondary')
        return f'<span class="badge bg-{color}">{status.replace("_", " ").title()}</span>'
    
    def build_actions(backup):
        actions = f'''<div class="btn-group btn-group-sm">
            <a href="{url_for('backup.backup_detail', backup_id=backup.id)}" class="btn btn-outline-primary">
                <i class="bi bi-eye"></i>
            </a>'''
        if backup.status == 'completed' and backup.file_path:
            actions += f'''<a href="{url_for('backup.download_backup', backup_id=backup.id)}" class="btn btn-outline-success">
                <i class="bi bi-download"></i>
            </a>'''
        actions += f'''<form action="{url_for('backup.delete_backup', backup_id=backup.id)}" method="post" class="d-inline" onsubmit="return confirm('Are you sure?')">
            <button type="submit" class="btn btn-outline-danger">
                <i class="bi bi-trash"></i>
            </button>
        </form></div>'''
        return actions
    
    # Serialize backups for React AdminDataTable
    backups_json = json.dumps([{
        'id': f'#{backup.id}',
        'type': get_type_badge(backup.backup_type),
        'status': get_status_badge(backup.status),
        'size': f'{round(backup.file_size_bytes / 1024 / 1024, 2)} MB' if backup.file_size_bytes else '-',
        'started': backup.started_at.strftime('%Y-%m-%d %H:%M') if backup.started_at else '-',
        'verified': '<i class="bi bi-check-circle-fill text-success"></i>' if backup.verified else '<i class="bi bi-x-circle text-muted"></i>',
        'actions': build_actions(backup)
    } for backup in backups.items])
    
    return render_template('admin/backups/index.html',
                          backups=backups,
                          backups_json=backups_json,
                          schedules=schedules,
                          current_type=backup_type)


@backup_bp.route('/create', methods=['POST'])
@login_required
@admin_required
def create_backup():
    """Trigger a manual backup."""
    backup_type = request.form.get('backup_type', 'database')
    compress = request.form.get('compress', 'true') == 'true'
    
    # Create backup record
    backup = Backup(
        backup_type=backup_type,
        status='in_progress',
        created_by_id=current_user.id,
    )
    db.session.add(backup)
    db.session.commit()
    
    try:
        # Perform backup
        if backup_type == 'database':
            file_path, file_size, checksum = backup_service.create_database_backup(compress=compress)
        elif backup_type == 'media':
            file_path, file_size, checksum = backup_service.create_media_backup(compress=compress)
        elif backup_type == 'full':
            file_path, file_size, checksum = backup_service.create_full_backup(compress=compress)
        else:
            raise ValueError(f"Unknown backup type: {backup_type}")
        
        # Update backup record
        backup.status = 'completed'
        backup.file_path = file_path
        backup.file_size_bytes = file_size
        backup.checksum = checksum
        backup.completed_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Backup created successfully: {file_path}', 'success')
        
    except Exception as e:
        backup.status = 'failed'
        backup.error_message = str(e)
        backup.completed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Backup failed: {str(e)}', 'danger')
    
    return redirect(url_for('backup.list_backups'))


@backup_bp.route('/<int:backup_id>')
@login_required
@admin_required
def backup_detail(backup_id):
    """View backup details."""
    backup = Backup.query.get_or_404(backup_id)
    return render_template('admin/backups/detail.html', backup=backup)


@backup_bp.route('/<int:backup_id>/download')
@login_required
@admin_required
def download_backup(backup_id):
    """Download a backup file."""
    import os
    
    backup = Backup.query.get_or_404(backup_id)
    
    if not backup.file_path or not os.path.exists(backup.file_path):
        flash('Backup file not found.', 'danger')
        return redirect(url_for('backup.list_backups'))
    
    return send_file(
        backup.file_path,
        as_attachment=True,
        download_name=os.path.basename(backup.file_path)
    )


@backup_bp.route('/<int:backup_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_backup(backup_id):
    """Verify backup integrity."""
    backup = Backup.query.get_or_404(backup_id)
    
    if not backup.file_path or not backup.checksum:
        flash('Cannot verify backup: missing file path or checksum.', 'danger')
        return redirect(url_for('backup.backup_detail', backup_id=backup_id))
    
    is_valid = backup_service.verify_backup(backup.file_path, backup.checksum)
    
    backup.verified = is_valid
    backup.verification_date = datetime.utcnow()
    db.session.commit()
    
    if is_valid:
        flash('Backup verified successfully.', 'success')
    else:
        flash('Backup verification failed! Checksum mismatch.', 'danger')
    
    return redirect(url_for('backup.backup_detail', backup_id=backup_id))


@backup_bp.route('/<int:backup_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_backup(backup_id):
    """Restore from a backup."""
    backup = Backup.query.get_or_404(backup_id)
    
    if backup.backup_type != 'database':
        flash('Only database backups can be restored through this interface.', 'warning')
        return redirect(url_for('backup.backup_detail', backup_id=backup_id))
    
    confirm = request.form.get('confirm')
    if confirm != 'RESTORE':
        flash('Please type RESTORE to confirm.', 'warning')
        return redirect(url_for('backup.backup_detail', backup_id=backup_id))
    
    try:
        backup_service.restore_database_backup(backup.file_path)
        flash('Database restored successfully. Application restart may be required.', 'success')
    except Exception as e:
        flash(f'Restore failed: {str(e)}', 'danger')
    
    return redirect(url_for('backup.backup_detail', backup_id=backup_id))


@backup_bp.route('/<int:backup_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_backup(backup_id):
    """Delete a backup."""
    import os
    
    backup = Backup.query.get_or_404(backup_id)
    
    # Delete file if exists
    if backup.file_path and os.path.exists(backup.file_path):
        try:
            os.remove(backup.file_path)
        except OSError:
            pass
    
    db.session.delete(backup)
    db.session.commit()
    
    flash('Backup deleted.', 'success')
    return redirect(url_for('backup.list_backups'))


# ============================================================================
# Schedule Management Routes
# ============================================================================

@backup_bp.route('/schedules')
@login_required
@admin_required
def list_schedules():
    """List backup schedules."""
    schedules = BackupSchedule.query.order_by(BackupSchedule.name).all()
    return render_template('admin/backups/schedules.html', schedules=schedules)


@backup_bp.route('/schedules/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_schedule():
    """Create a new backup schedule."""
    if request.method == 'POST':
        schedule = BackupSchedule(
            name=request.form.get('name'),
            backup_type=request.form.get('backup_type', 'database'),
            frequency=request.form.get('frequency', 'daily'),
            retention_days=int(request.form.get('retention_days', 30)),
            storage_location=request.form.get('storage_location', 'local'),
            encryption_enabled=request.form.get('encryption_enabled') == 'true',
            is_active=request.form.get('is_active') == 'true',
            cron_expression=request.form.get('cron_expression') or None,
        )
        db.session.add(schedule)
        db.session.commit()
        
        flash('Backup schedule created.', 'success')
        return redirect(url_for('backup.list_schedules'))
    
    return render_template('admin/backups/schedule_form.html', schedule=None)


@backup_bp.route('/schedules/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_schedule(schedule_id):
    """Edit a backup schedule."""
    schedule = BackupSchedule.query.get_or_404(schedule_id)
    
    if request.method == 'POST':
        schedule.name = request.form.get('name')
        schedule.backup_type = request.form.get('backup_type', 'database')
        schedule.frequency = request.form.get('frequency', 'daily')
        schedule.retention_days = int(request.form.get('retention_days', 30))
        schedule.storage_location = request.form.get('storage_location', 'local')
        schedule.encryption_enabled = request.form.get('encryption_enabled') == 'true'
        schedule.is_active = request.form.get('is_active') == 'true'
        schedule.cron_expression = request.form.get('cron_expression') or None
        
        db.session.commit()
        flash('Schedule updated.', 'success')
        return redirect(url_for('backup.list_schedules'))
    
    return render_template('admin/backups/schedule_form.html', schedule=schedule)


@backup_bp.route('/schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_schedule(schedule_id):
    """Delete a backup schedule."""
    schedule = BackupSchedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    
    flash('Schedule deleted.', 'success')
    return redirect(url_for('backup.list_schedules'))


@backup_bp.route('/schedules/<int:schedule_id>/run', methods=['POST'])
@login_required
@admin_required
def run_schedule(schedule_id):
    """Manually run a backup schedule."""
    scheduler = BackupScheduler(backup_service)
    
    try:
        backup_id = scheduler.run_scheduled_backup(schedule_id)
        if backup_id:
            flash('Scheduled backup completed successfully.', 'success')
        else:
            flash('Schedule not found or inactive.', 'warning')
    except Exception as e:
        flash(f'Backup failed: {str(e)}', 'danger')
    
    return redirect(url_for('backup.list_schedules'))


# ============================================================================
# Feature Flags Routes
# ============================================================================

@backup_bp.route('/feature-flags')
@login_required
@admin_required
def list_feature_flags():
    """List all feature flags."""
    flags = FeatureFlag.query.order_by(FeatureFlag.name).all()
    return render_template('admin/backups/feature_flags.html', flags=flags)


@backup_bp.route('/feature-flags/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_feature_flag():
    """Create a new feature flag."""
    if request.method == 'POST':
        flag = FeatureFlag(
            name=request.form.get('name'),
            description=request.form.get('description'),
            is_enabled=request.form.get('is_enabled') == 'true',
            rollout_percentage=int(request.form.get('rollout_percentage', 0)),
            created_by_id=current_user.id,
        )
        db.session.add(flag)
        db.session.commit()
        
        feature_flags.invalidate_cache()
        flash('Feature flag created.', 'success')
        return redirect(url_for('backup.list_feature_flags'))
    
    return render_template('admin/backups/feature_flag_form.html', flag=None)


@backup_bp.route('/feature-flags/<int:flag_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_feature_flag(flag_id):
    """Edit a feature flag."""
    flag = FeatureFlag.query.get_or_404(flag_id)
    
    if request.method == 'POST':
        flag.name = request.form.get('name')
        flag.description = request.form.get('description')
        flag.is_enabled = request.form.get('is_enabled') == 'true'
        flag.rollout_percentage = int(request.form.get('rollout_percentage', 0))
        
        db.session.commit()
        feature_flags.invalidate_cache()
        flash('Feature flag updated.', 'success')
        return redirect(url_for('backup.list_feature_flags'))
    
    return render_template('admin/backups/feature_flag_form.html', flag=flag)


@backup_bp.route('/feature-flags/<int:flag_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_feature_flag(flag_id):
    """Toggle a feature flag on/off."""
    flag = FeatureFlag.query.get_or_404(flag_id)
    flag.is_enabled = not flag.is_enabled
    db.session.commit()
    
    feature_flags.invalidate_cache()
    
    status = 'enabled' if flag.is_enabled else 'disabled'
    flash(f'Feature flag "{flag.name}" {status}.', 'success')
    return redirect(url_for('backup.list_feature_flags'))


@backup_bp.route('/feature-flags/<int:flag_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_feature_flag(flag_id):
    """Delete a feature flag."""
    flag = FeatureFlag.query.get_or_404(flag_id)
    db.session.delete(flag)
    db.session.commit()
    
    feature_flags.invalidate_cache()
    flash('Feature flag deleted.', 'success')
    return redirect(url_for('backup.list_feature_flags'))


# ============================================================================
# Deployment Log Routes
# ============================================================================

@backup_bp.route('/deployments')
@login_required
@admin_required
def list_deployments():
    """List deployment history."""
    environment = request.args.get('environment')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = DeploymentLog.query.order_by(DeploymentLog.started_at.desc())
    if environment:
        query = query.filter(DeploymentLog.environment == environment)
    
    deployments = query.paginate(page=page, per_page=per_page)
    
    return render_template('admin/backups/deployments.html',
                          deployments=deployments,
                          current_environment=environment)


@backup_bp.route('/deployments/<int:deployment_id>')
@login_required
@admin_required
def deployment_detail(deployment_id):
    """View deployment details."""
    deployment = DeploymentLog.query.get_or_404(deployment_id)
    return render_template('admin/backups/deployment_detail.html', deployment=deployment)


# ============================================================================
# API Endpoints
# ============================================================================

@backup_bp.route('/api/status')
@login_required
@admin_required
def api_backup_status():
    """Get backup system status."""
    recent_backups = Backup.query.filter_by(status='completed').order_by(
        Backup.completed_at.desc()
    ).limit(5).all()
    
    active_schedules = BackupSchedule.query.filter_by(is_active=True).count()
    
    return jsonify({
        'status': 'ok',
        'recent_backups': [{
            'id': b.id,
            'type': b.backup_type,
            'completed_at': b.completed_at.isoformat() if b.completed_at else None,
            'size_mb': round(b.file_size_bytes / (1024 * 1024), 2) if b.file_size_bytes else None,
        } for b in recent_backups],
        'active_schedules': active_schedules,
    })
