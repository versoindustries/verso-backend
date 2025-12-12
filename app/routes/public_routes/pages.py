from flask import Blueprint, render_template, abort, request, jsonify
from flask_login import login_required, current_user
from markupsafe import Markup
from app.models import Page, PageRender
from app.database import db
from app.modules.auth_manager import role_required
import bleach

pages_bp = Blueprint('pages', __name__)


# Allowed HTML tags for content sanitization
ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'ul', 'ol', 'li', 'br',
    'strong', 'em', 'u', 'blockquote', 'code', 'pre', 'img', 'div', 'span',
    'table', 'thead', 'tbody', 'tr', 'th', 'td'
]
ALLOWED_ATTRS = {
    '*': ['class', 'id', 'style'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height']
}


@pages_bp.route('/<slug>')
def show_page(slug):
    # Try to find the page
    page = Page.query.filter_by(slug=slug, is_published=True).first()
    
    if not page:
        abort(404)

    # Check for cached render
    if page.render:
        return page.render.rendered_html
    
    # Render dynamically
    # Check if html_content is safe (it should be coming from admin CKEditor)
    return render_template('page.html', page=page, page_content=Markup(page.html_content))


@pages_bp.route('/api/page/<int:id>/content', methods=['PATCH'])
@login_required
@role_required('Admin', 'Manager', 'Marketing', 'Owner')
def update_page_content(id):
    """
    Update page content via inline editor.
    Accessible to Admin, Manager, Marketing, and Owner roles.
    """
    page = Page.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update title if provided
    if 'title' in data and data['title']:
        page.title = bleach.clean(data['title'], tags=[], strip=True)
    
    # Update content if provided (sanitize HTML)
    if 'content' in data and data['content']:
        page.html_content = bleach.clean(
            data['content'], 
            tags=ALLOWED_TAGS, 
            attributes=ALLOWED_ATTRS,
            strip=True
        )
    
    # Update SEO fields
    if 'metaTitle' in data:
        page.meta_title = bleach.clean(data['metaTitle'], tags=[], strip=True)[:70]
    
    if 'metaDescription' in data:
        page.meta_description = bleach.clean(data['metaDescription'], tags=[], strip=True)[:200]
    
    if 'slug' in data and data['slug']:
        # Validate slug format
        new_slug = bleach.clean(data['slug'], tags=[], strip=True)
        new_slug = new_slug.lower().replace(' ', '-')
        # Check for duplicate slugs
        existing = Page.query.filter_by(slug=new_slug).filter(Page.id != id).first()
        if not existing:
            page.slug = new_slug
    
    # Update Open Graph fields if page model supports them
    if hasattr(page, 'og_title') and 'ogTitle' in data:
        page.og_title = bleach.clean(data['ogTitle'], tags=[], strip=True)
    
    if hasattr(page, 'og_description') and 'ogDescription' in data:
        page.og_description = bleach.clean(data['ogDescription'], tags=[], strip=True)
    
    if hasattr(page, 'og_image') and 'ogImage' in data:
        page.og_image = bleach.clean(data['ogImage'], tags=[], strip=True)
    
    # Invalidate cached render
    if page.render:
        db.session.delete(page.render)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Page updated successfully',
        'page': {
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'meta_title': page.meta_title,
            'meta_description': page.meta_description
        }
    })
