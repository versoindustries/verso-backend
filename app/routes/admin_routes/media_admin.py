"""
Media Admin Routes

Admin interface for browsing, uploading, and managing media files.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.database import db
from app.models import Media
from app.modules.decorators import role_required
from app.modules.file_manager import save_media, delete_media, allowed_file
from datetime import datetime

media_admin_bp = Blueprint('media_admin', __name__, url_prefix='/admin/media')


# =============================================================================
# Media Browser
# =============================================================================

@media_admin_bp.route('/')
@login_required
@role_required('admin')
def list_media():
    """List all media with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 24, type=int)
    search = request.args.get('search', '')
    mimetype_filter = request.args.get('type', '')
    
    query = Media.query
    
    # Search by filename
    if search:
        query = query.filter(Media.filename.ilike(f'%{search}%'))
    
    # Filter by mimetype category
    if mimetype_filter == 'images':
        query = query.filter(Media.mimetype.like('image/%'))
    elif mimetype_filter == 'documents':
        query = query.filter(
            db.or_(
                Media.mimetype.like('application/pdf%'),
                Media.mimetype.like('application/msword%'),
                Media.mimetype.like('application/vnd.%'),
                Media.mimetype.like('text/%')
            )
        )
    
    # Order by newest first
    query = query.order_by(Media.created_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate stats
    total_size = db.session.query(db.func.sum(Media.size)).scalar() or 0
    total_count = Media.query.count()
    
    return render_template('admin/media/index.html',
                          media=pagination.items,
                          pagination=pagination,
                          search=search,
                          mimetype_filter=mimetype_filter,
                          total_size=total_size,
                          total_count=total_count)


@media_admin_bp.route('/upload', methods=['POST'])
@login_required
@role_required('admin')
def upload_media():
    """Upload one or more media files."""
    if 'files' not in request.files:
        flash('No files selected.', 'warning')
        return redirect(url_for('media_admin.list_media'))
    
    files = request.files.getlist('files')
    uploaded = 0
    errors = 0
    
    for file in files:
        if file and file.filename:
            if allowed_file(file.filename):
                media = save_media(file, user_id=current_user.id)
                if media:
                    uploaded += 1
                else:
                    errors += 1
            else:
                errors += 1
    
    if uploaded > 0:
        flash(f'{uploaded} file(s) uploaded successfully.', 'success')
    if errors > 0:
        flash(f'{errors} file(s) failed to upload.', 'danger')
    
    # AJAX response for dropzone
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'uploaded': uploaded, 'errors': errors})
    
    return redirect(url_for('media_admin.list_media'))


@media_admin_bp.route('/<int:id>')
@login_required
@role_required('admin')
def media_detail(id):
    """View media details."""
    media = Media.query.get_or_404(id)
    return render_template('admin/media/detail.html', media=media)


@media_admin_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_media_item(id):
    """Delete a media item."""
    media = Media.query.get_or_404(id)
    filename = media.filename
    
    if delete_media(id):
        flash(f'"{filename}" deleted.', 'success')
    else:
        flash('Failed to delete media.', 'danger')
    
    # AJAX response
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'success': True})
    
    return redirect(url_for('media_admin.list_media'))


@media_admin_bp.route('/bulk-delete', methods=['POST'])
@login_required
@role_required('admin')
def bulk_delete_media():
    """Delete multiple media items."""
    ids = request.form.getlist('ids[]')
    
    if not ids:
        data = request.get_json()
        if data:
            ids = data.get('ids', [])
    
    deleted = 0
    for id_str in ids:
        try:
            if delete_media(int(id_str)):
                deleted += 1
        except (ValueError, TypeError):
            continue
    
    flash(f'{deleted} item(s) deleted.', 'success')
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'deleted': deleted})
    
    return redirect(url_for('media_admin.list_media'))


@media_admin_bp.route('/api/browse')
@login_required
@role_required('admin')
def api_browse_media():
    """API endpoint for media browser (for modals/pickers)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    images_only = request.args.get('images_only', 'false') == 'true'
    
    query = Media.query
    
    if images_only:
        query = query.filter(Media.mimetype.like('image/%'))
    
    query = query.order_by(Media.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    items = []
    for media in pagination.items:
        items.append({
            'id': media.id,
            'filename': media.filename,
            'mimetype': media.mimetype,
            'size': media.size,
            'url': url_for('media_bp.serve_media', media_id=media.id),
            'created_at': media.created_at.isoformat() if media.created_at else None
        })
    
    return jsonify({
        'items': items,
        'page': pagination.page,
        'pages': pagination.pages,
        'total': pagination.total,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


def format_file_size(size_bytes):
    """Format file size for display."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
