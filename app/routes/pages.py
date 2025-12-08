from flask import Blueprint, render_template, abort
from markupsafe import Markup
from app.models import Page, PageRender
from app.database import db

pages_bp = Blueprint('pages', __name__)

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
