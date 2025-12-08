"""
Phase 12: SEO Module

Provides SEO utilities for sitemap generation and Schema.org JSON-LD automation.
"""
from flask import url_for, current_app
from datetime import datetime
import xml.etree.ElementTree as ET


def generate_dynamic_sitemap(base_url=None):
    """
    Generate XML sitemap including all published pages and blog posts.
    
    Returns:
        str: XML sitemap content
    """
    from app.models import Page, Post
    
    if not base_url:
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
    
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Add static routes (homepage, about, contact, etc.)
    static_routes = [
        ('main_routes.index', 1.0, 'weekly'),
        ('main_routes.about_us', 0.8, 'monthly'),
        ('main_routes.contact', 0.7, 'monthly'),
        ('main_routes.privacy_policy', 0.3, 'yearly'),
        ('main_routes.terms_of_service', 0.3, 'yearly'),
        ('blog.blog_home', 0.9, 'daily'),
    ]
    
    for endpoint, priority, changefreq in static_routes:
        try:
            url = url_for(endpoint, _external=True)
            add_url_to_sitemap(urlset, url, priority=priority, changefreq=changefreq)
        except Exception:
            pass  # Skip if route doesn't exist
    
    # Add published pages
    pages = Page.query.filter(
        (Page.status == 'published') | (Page.is_published == True)
    ).all()
    
    for page in pages:
        try:
            url = url_for('pages.show_page', slug=page.slug, _external=True)
            add_url_to_sitemap(
                urlset, 
                url, 
                lastmod=page.updated_at,
                priority=0.7,
                changefreq='monthly'
            )
        except Exception:
            pass
    
    # Add published blog posts
    posts = Post.query.filter_by(is_published=True).all()
    
    for post in posts:
        try:
            url = url_for('blog.view_post', post_id=post.id, _external=True)
            add_url_to_sitemap(
                urlset, 
                url, 
                lastmod=post.updated_at or post.published_at,
                priority=0.8,
                changefreq='weekly'
            )
        except Exception:
            pass
    
    # Generate XML string
    tree = ET.ElementTree(urlset)
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    
    # Convert to string
    import io
    buffer = io.BytesIO()
    tree.write(buffer, encoding='utf-8', xml_declaration=False)
    return xml_declaration + buffer.getvalue().decode('utf-8')


def add_url_to_sitemap(urlset, loc, lastmod=None, changefreq=None, priority=None):
    """Add a URL entry to the sitemap."""
    url_elem = ET.SubElement(urlset, "url")
    
    loc_elem = ET.SubElement(url_elem, "loc")
    loc_elem.text = loc
    
    if lastmod:
        if isinstance(lastmod, datetime):
            lastmod = lastmod.strftime('%Y-%m-%d')
        lastmod_elem = ET.SubElement(url_elem, "lastmod")
        lastmod_elem.text = lastmod
    
    if changefreq:
        changefreq_elem = ET.SubElement(url_elem, "changefreq")
        changefreq_elem.text = changefreq
    
    if priority is not None:
        priority_elem = ET.SubElement(url_elem, "priority")
        priority_elem.text = str(priority)


def generate_schema_json_ld(page_or_post, schema_type=None, additional_data=None):
    """
    Generate Schema.org JSON-LD structured data for a page or post.
    
    Args:
        page_or_post: A Page or Post model instance
        schema_type: Override schema type (default uses page.schema_type or 'Article' for posts)
        additional_data: Additional key-value pairs to include in schema
    
    Returns:
        dict: Schema.org JSON-LD object
    """
    from app.models import Post
    
    is_post = isinstance(page_or_post, Post)
    
    # Determine schema type
    if schema_type is None:
        if is_post:
            schema_type = 'Article'
        else:
            schema_type = getattr(page_or_post, 'schema_type', 'WebPage')
    
    schema = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": page_or_post.title,
        "description": getattr(page_or_post, 'meta_description', None) or '',
    }
    
    # Add URL
    try:
        if is_post:
            schema["url"] = url_for('blog.view_post', post_id=page_or_post.id, _external=True)
        else:
            schema["url"] = url_for('pages.show_page', slug=page_or_post.slug, _external=True)
    except Exception:
        pass
    
    # Add timestamps
    if hasattr(page_or_post, 'created_at') and page_or_post.created_at:
        schema["dateCreated"] = page_or_post.created_at.isoformat()
    
    if hasattr(page_or_post, 'updated_at') and page_or_post.updated_at:
        schema["dateModified"] = page_or_post.updated_at.isoformat()
    
    if is_post and hasattr(page_or_post, 'published_at') and page_or_post.published_at:
        schema["datePublished"] = page_or_post.published_at.isoformat()
    
    # Add author for posts
    if is_post and hasattr(page_or_post, 'author') and page_or_post.author:
        schema["author"] = {
            "@type": "Person",
            "name": f"{page_or_post.author.first_name or ''} {page_or_post.author.last_name or ''}".strip() or page_or_post.author.username
        }
    
    # Add page author if available
    if not is_post and hasattr(page_or_post, 'author') and page_or_post.author:
        schema["author"] = {
            "@type": "Person",
            "name": f"{page_or_post.author.first_name or ''} {page_or_post.author.last_name or ''}".strip() or page_or_post.author.username
        }
    
    # Add custom fields for pages
    if not is_post and hasattr(page_or_post, 'custom_fields'):
        for field in page_or_post.custom_fields:
            if field.field_name.startswith('schema_'):
                # Strip 'schema_' prefix for Schema.org property names
                prop_name = field.field_name[7:]
                schema[prop_name] = field.get_typed_value()
    
    # Merge additional data
    if additional_data:
        schema.update(additional_data)
    
    return schema


def get_robots_txt_content(disallow_paths=None, sitemap_url=None):
    """
    Generate robots.txt content.
    
    Args:
        disallow_paths: List of paths to disallow
        sitemap_url: URL to sitemap.xml
    
    Returns:
        str: robots.txt content
    """
    lines = [
        "User-agent: *",
        "Allow: /",
    ]
    
    # Default disallow paths
    default_disallow = ['/admin/', '/api/', '/login', '/register', '/logout']
    paths = disallow_paths or default_disallow
    
    for path in paths:
        lines.append(f"Disallow: {path}")
    
    lines.append("")  # Blank line before sitemap
    
    if sitemap_url:
        lines.append(f"Sitemap: {sitemap_url}")
    
    return "\n".join(lines)


def init_seo_context_processor(app):
    """Initialize SEO context processor for templates."""
    
    @app.context_processor
    def inject_seo_helpers():
        """Inject SEO helper functions into all templates."""
        return {
            'generate_schema_json_ld': generate_schema_json_ld,
        }
