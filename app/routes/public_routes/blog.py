from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from flask import current_app as app
from app import db, mail, bcrypt
from app.models import User, Role, Post, Tag, BlogCategory, PostSeries, PostRevision, Comment
from app.forms import (RegistrationForm, LoginForm, EstimateRequestForm, CreatePostForm, 
                       EditPostForm, CSRFTokenForm, CommentForm, BlogCategoryForm, TagForm,
                       PostSeriesForm, BlogSearchForm, CommentModerationForm)
from app.modules.auth_manager import blogger_required, admin_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_
import logging
import io
import bleach
import hashlib
from datetime import datetime

# Allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt']
}

# Configure logging
logger = logging.getLogger(__name__)

blog_blueprint = Blueprint('blog', __name__, template_folder='templates/')
news_update = Blueprint('news', __name__, template_folder='templates/')
updates_blueprint = Blueprint('updates', __name__, template_folder='templates')

# Context processors for consistent form inclusion
@blog_blueprint.context_processor
def combined_context_processor():
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form, hide_estimate_form=True)

@news_update.context_processor
def combined_context_processor():
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form, hide_estimate_form=True)

@updates_blueprint.context_processor
def combined_context_processor():
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form, hide_estimate_form=True)

# Serve post image
@blog_blueprint.route('/blog/image/<int:post_id>')
def serve_image(post_id):
    """Serve the image for a blog post."""
    try:
        post = Post.query.get_or_404(post_id)
        if not post.image or not post.image_mime_type:
            logger.debug(f"No image found for post ID {post_id}")
            return Response(status=404)
        logger.debug(f"Serving image for post ID {post_id}")
        return Response(post.image, mimetype=post.image_mime_type)
    except Exception as e:
        logger.error(f"Error serving image for post ID {post_id}: {e}")
        return Response(status=500)

# Public blog list route
@blog_blueprint.route('/blog')
def show_blog():
    """Display a paginated list of published blog posts."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        logger.debug(f"Retrieved {posts.total} published posts for page {page}")
        return render_template('blog/blog.html', posts=posts)
    except Exception as e:
        logger.error(f"Error fetching blog posts: {e}")
        flash('An error occurred while loading the blog.', 'danger')
        return render_template('blog/blog.html', posts=None)

# Individual blog post route
@blog_blueprint.route('/blog/<string:slug>')
def show_post(slug):
    """Display an individual blog post by slug."""
    try:
        post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
        logger.debug(f"Retrieved post with slug: {slug}")
        return render_template('blog/post.html', post=post)
    except Exception as e:
        logger.error(f"Error fetching post with slug {slug}: {e}")
        flash('The requested post could not be found.', 'danger')
        return render_template('errors/404.html'), 404

@blog_blueprint.route('/blog/manage')
@login_required
@blogger_required
def manage_posts():
    """Display a paginated list of all posts for management."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50  # Increased for client-side table
        # Show all posts for the current user or admins
        if current_user.has_role('admin'):
            posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        else:
            posts = Post.query.filter_by(author_id=current_user.id).order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        form = CSRFTokenForm()
        
        # Serialize posts for AdminDataTable
        import json
        posts_json = []
        for post in posts.items:
            # Create thumbnail HTML
            if post.image and post.image_mime_type:
                thumbnail = f'<img src="{url_for("blog.serve_image", post_id=post.id)}" alt="{post.title}" class="img-thumbnail" style="max-width: 60px; max-height: 40px;">'
            else:
                thumbnail = '<span class="text-muted"><i class="fas fa-image"></i></span>'
            
            # Create title link
            title = f'<a href="{url_for("blog.show_post", slug=post.slug)}"><strong>{post.title}</strong></a>'
            
            # Status badge
            if post.is_published:
                status = '<span class="badge bg-success">Published</span>'
            elif post.publish_at:
                status = f'<span class="badge bg-warning">Scheduled</span>'
            else:
                status = '<span class="badge bg-secondary">Draft</span>'
            
            # Action buttons
            view_url = url_for('blog.show_post', slug=post.slug)
            edit_url = url_for('blog.edit_post', post_id=post.id)
            delete_url = url_for('blog.delete_post', id=post.id)
            actions = f'''
                <a href="{view_url}" class="btn btn-sm btn-outline-secondary" title="View"><i class="fas fa-eye"></i></a>
                <a href="{edit_url}" class="btn btn-sm btn-outline-primary" title="Edit"><i class="fas fa-edit"></i></a>
                <form action="{delete_url}" method="POST" class="d-inline delete-form">
                    <input type="hidden" name="csrf_token" value="{form.csrf_token._value()}">
                    <button type="submit" class="btn btn-sm btn-outline-danger" title="Delete"><i class="fas fa-trash"></i></button>
                </form>
            '''
            
            posts_json.append({
                'thumbnail': thumbnail,
                'title': title,
                'author': post.author.username if post.author else 'Unknown',
                'date': post.created_at.strftime('%Y-%m-%d') if post.created_at else '-',
                'status': status,
                'actions': actions
            })
        
        logger.debug(f"Retrieved {posts.total} posts for management by user {current_user.username}")
        return render_template('blog/manage_posts.html', posts=posts, form=form, 
                             posts_json=json.dumps(posts_json),
                             is_admin=current_user.has_role('admin'))
    except Exception as e:
        logger.error(f"Error fetching posts for management: {e}")
        flash('An error occurred while loading your posts.', 'danger')
        return render_template('blog/manage_posts.html', posts=None, form=CSRFTokenForm(), 
                             posts_json='[]', is_admin=False)

# Create new post (blogger role required)
@blog_blueprint.route('/blog/new', methods=['GET', 'POST'])
@login_required
@blogger_required
def new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        try:
            # Initialize image fields
            image_data = None
            image_mime_type = None
            if form.image.data:
                # Reset file pointer to ensure the stream is readable
                form.image.data.seek(0)
                image_data = form.image.data.read()
                image_mime_type = form.image.data.mimetype
            # Sanitize the content
            sanitized_content = bleach.clean(
                form.content.data,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True
            )
            
            # Generate slug
            slug = form.title.data.lower().replace(' ', '-')
            
            # Phase 3: Handle scheduled publishing
            is_published = form.is_published.data
            publish_at = form.publish_at.data
            if publish_at and publish_at > datetime.utcnow():
                is_published = False  # Will be published by worker at scheduled time
            
            post = Post(
                title=form.title.data,
                content=sanitized_content,
                category=form.category.data,  # Legacy field
                is_published=is_published,
                author_id=current_user.id,
                slug=slug,
                image=image_data,
                image_mime_type=image_mime_type,
                # Phase 3 fields
                blog_category_id=form.blog_category_id.data if form.blog_category_id.data else None,
                is_featured=form.is_featured.data,
                series_id=form.series_id.data if form.series_id.data else None,
                series_order=form.series_order.data or 0,
                publish_at=publish_at,
                meta_description=form.meta_description.data
            )
            
            # Calculate read time
            post.read_time_minutes = post.calculate_read_time()
            
            db.session.add(post)
            db.session.flush()  # Get post.id before handling tags
            
            # Phase 3: Handle tags
            if form.tags_input.data:
                tag_names = [t.strip() for t in form.tags_input.data.split(',') if t.strip()]
                for tag_name in tag_names:
                    tag_slug = tag_name.lower().replace(' ', '-')
                    tag = Tag.query.filter_by(slug=tag_slug).first()
                    if not tag:
                        tag = Tag(name=tag_name, slug=tag_slug)
                        db.session.add(tag)
                    post.tags.append(tag)
            
            # Create initial revision
            revision = PostRevision(
                post_id=post.id,
                title=post.title,
                content=post.content,
                user_id=current_user.id,
                revision_note='Initial version'
            )
            db.session.add(revision)
            
            db.session.commit()
            logger.info(f"New post created by {current_user.username}: {post.title}")
            flash('Post created successfully.', 'success')
            return redirect(url_for('blog.manage_posts'))
        except IntegrityError:
            db.session.rollback()
            logger.error(f"Duplicate slug detected for post: {form.title.data}")
            flash('A post with this title already exists. Please choose a different title.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error creating post: {e}")
            flash('An error occurred while creating the post.', 'danger')
    if form.errors:
        logger.debug(f"Form validation errors: {form.errors}")
    return render_template('blog/new_post.html', form=form)

@blog_blueprint.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
@blogger_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id and not current_user.has_role('admin'):
        logger.warning(f"Unauthorized edit attempt by {current_user.username} on post ID {post_id}")
        flash('You are not authorized to edit this post.', 'danger')
        return render_template('errors/403.html'), 403
    
    form = EditPostForm(obj=post)
    
    # Pre-populate Phase 3 fields on GET
    if request.method == 'GET':
        form.blog_category_id.data = post.blog_category_id or 0
        form.series_id.data = post.series_id or 0
        form.tags_input.data = ', '.join([t.name for t in post.tags]) if post.tags else ''
        form.is_featured.data = post.is_featured
        form.publish_at.data = post.publish_at
        form.meta_description.data = post.meta_description
        form.series_order.data = post.series_order
    
    if form.validate_on_submit():
        try:
            # Store old content for revision
            old_title = post.title
            old_content = post.content
            
            post.title = form.title.data
            # Sanitize the content
            post.content = bleach.clean(
                form.content.data,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True
            )
            post.category = form.category.data  # Legacy field
            post.slug = form.title.data.lower().replace(' ', '-')
            
            # Phase 3: Handle scheduled publishing
            if form.publish_at.data and form.publish_at.data > datetime.utcnow():
                post.is_published = False
                post.publish_at = form.publish_at.data
            else:
                post.is_published = form.is_published.data
                post.publish_at = form.publish_at.data
            
            # Phase 3 fields
            post.blog_category_id = form.blog_category_id.data if form.blog_category_id.data else None
            post.is_featured = form.is_featured.data
            post.series_id = form.series_id.data if form.series_id.data else None
            post.series_order = form.series_order.data or 0
            post.meta_description = form.meta_description.data
            
            # Recalculate read time
            post.read_time_minutes = post.calculate_read_time()
            
            if form.image.data:
                form.image.data.seek(0)
                post.image = form.image.data.read()
                post.image_mime_type = form.image.data.mimetype
            
            # Phase 3: Update tags
            post.tags.clear()
            if form.tags_input.data:
                tag_names = [t.strip() for t in form.tags_input.data.split(',') if t.strip()]
                for tag_name in tag_names:
                    tag_slug = tag_name.lower().replace(' ', '-')
                    tag = Tag.query.filter_by(slug=tag_slug).first()
                    if not tag:
                        tag = Tag(name=tag_name, slug=tag_slug)
                        db.session.add(tag)
                    post.tags.append(tag)
            
            # Create revision if content changed
            if old_title != post.title or old_content != post.content:
                revision = PostRevision(
                    post_id=post.id,
                    title=post.title,
                    content=post.content,
                    user_id=current_user.id,
                    revision_note=f'Updated by {current_user.username}'
                )
                db.session.add(revision)
            
            db.session.commit()
            logger.info(f'"{post.title}" updated successfully by {current_user.username}')
            flash('Record updated successfully.', 'success')
            return redirect(url_for('blog.manage_posts'))
        except IntegrityError:
            db.session.rollback()
            logger.error(f"Duplicate slug detected for post ID {post_id}")
            flash('A post with this title already exists. Please choose a different title.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating post ID {post_id}: {e}")
            flash('Error updating record. Please try again.', 'error')
    elif request.method == 'POST':
        logger.debug(f"Form validation failed: {form.errors}")
    return render_template('blog/edit.html', form=form, post=post, id=post_id)

# Delete post (blogger role required)
@blog_blueprint.route('/blog/delete/<int:id>', methods=['POST'])
@login_required
@blogger_required
def delete_post(id):
    """Delete a blog post by ID."""
    post = Post.query.get_or_404(id)
    # Restrict access to post author or admins
    if post.author_id != current_user.id and not current_user.has_role('admin'):
        logger.warning(f"Unauthorized delete attempt by {current_user.username} on post ID {id}")
        flash('You are not authorized to delete this post.', 'danger')
        return render_template('errors/403.html'), 403
    
    csrf_form = CSRFTokenForm()
    if csrf_form.validate_on_submit():
        try:
            db.session.delete(post)
            db.session.commit()
            logger.info(f"Post ID {id} deleted by {current_user.username}")
            flash('Post deleted successfully.', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error deleting post ID {id}: {e}")
            flash('An error occurred while deleting the post.', 'danger')
    else:
        logger.debug(f"CSRF validation failed for delete post ID {id}")
        flash('Invalid request.', 'danger')
    
    return redirect(url_for('blog.manage_posts'))


# ============================================================================
# Phase 3: Blog Platform Enhancement Routes
# ============================================================================

# Blog Search
@blog_blueprint.route('/blog/search')
def search():
    """Search blog posts by title and content."""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if not query or len(query) < 2:
        flash('Please enter at least 2 characters to search.', 'warning')
        return redirect(url_for('blog.show_blog'))
    
    try:
        search_term = f'%{query}%'
        posts = Post.query.filter(
            Post.is_published == True,
            or_(
                Post.title.ilike(search_term),
                Post.content.ilike(search_term),
                Post.meta_description.ilike(search_term)
            )
        ).order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        logger.debug(f"Search for '{query}' returned {posts.total} results")
        return render_template('blog/blog_search.html', posts=posts, query=query)
    except Exception as e:
        logger.error(f"Error searching posts: {e}")
        flash('An error occurred while searching.', 'danger')
        return redirect(url_for('blog.show_blog'))


# Tag Archive
@blog_blueprint.route('/blog/tag/<string:slug>')
def posts_by_tag(slug):
    """Display posts filtered by tag."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    try:
        tag = Tag.query.filter_by(slug=slug).first_or_404()
        posts = Post.query.filter(
            Post.is_published == True,
            Post.tags.contains(tag)
        ).order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        logger.debug(f"Tag '{tag.name}' has {posts.total} posts")
        return render_template('blog/blog_tag.html', posts=posts, tag=tag)
    except Exception as e:
        logger.error(f"Error fetching posts by tag {slug}: {e}")
        flash('Tag not found.', 'danger')
        return redirect(url_for('blog.show_blog'))


# Category Archive
@blog_blueprint.route('/blog/category/<string:slug>')
def posts_by_category(slug):
    """Display posts filtered by category."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    try:
        category = BlogCategory.query.filter_by(slug=slug).first_or_404()
        posts = Post.query.filter(
            Post.is_published == True,
            Post.blog_category_id == category.id
        ).order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        
        logger.debug(f"Category '{category.name}' has {posts.total} posts")
        return render_template('blog/blog_category.html', posts=posts, category=category)
    except Exception as e:
        logger.error(f"Error fetching posts by category {slug}: {e}")
        flash('Category not found.', 'danger')
        return redirect(url_for('blog.show_blog'))


# RSS Feed
@blog_blueprint.route('/blog/rss')
def rss_feed():
    """Generate RSS feed for blog posts."""
    try:
        posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(20).all()
        
        # Build RSS XML manually
        rss_items = []
        for post in posts:
            item = f'''<item>
                <title><![CDATA[{post.title}]]></title>
                <link>{request.host_url.rstrip('/')}{url_for('blog.show_post', slug=post.slug)}</link>
                <pubDate>{post.created_at.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
                <description><![CDATA[{post.meta_description or post.content[:200]}...]]></description>
                <guid>{request.host_url.rstrip('/')}{url_for('blog.show_post', slug=post.slug)}</guid>
            </item>'''
            rss_items.append(item)
        
        rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>Blog RSS Feed</title>
        <link>{request.host_url.rstrip('/')}/blog</link>
        <description>Latest blog posts</description>
        <atom:link href="{request.host_url.rstrip('/')}{url_for('blog.rss_feed')}" rel="self" type="application/rss+xml"/>
        {''.join(rss_items)}
    </channel>
</rss>'''
        
        return Response(rss_content, mimetype='application/rss+xml')
    except Exception as e:
        logger.error(f"Error generating RSS feed: {e}")
        return Response(status=500)


# Comment Submission
@blog_blueprint.route('/blog/<string:slug>/comment', methods=['POST'])
def submit_comment(slug):
    """Submit a comment on a blog post."""
    post = Post.query.filter_by(slug=slug, is_published=True).first_or_404()
    form = CommentForm()
    
    if form.validate_on_submit():
        try:
            # Hash IP for spam detection
            ip_hash = hashlib.sha256(request.remote_addr.encode('utf-8')).hexdigest()
            
            comment = Comment(
                post_id=post.id,
                user_id=current_user.id if current_user.is_authenticated else None,
                author_name=form.author_name.data if not current_user.is_authenticated else None,
                author_email=form.author_email.data if not current_user.is_authenticated else None,
                content=bleach.clean(form.content.data, tags=['p', 'br', 'strong', 'em'], strip=True),
                parent_id=int(form.parent_id.data) if form.parent_id.data else None,
                ip_hash=ip_hash,
                status='pending'  # Require moderation
            )
            db.session.add(comment)
            db.session.commit()
            
            logger.info(f"Comment submitted on post '{post.title}' by {form.author_name.data or current_user.username}")
            flash('Your comment has been submitted and is awaiting moderation.', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error submitting comment: {e}")
            flash('An error occurred while submitting your comment.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('blog.show_post', slug=slug))


# Draft Preview (blogger only)
@blog_blueprint.route('/blog/preview/<int:post_id>')
@login_required
@blogger_required
def preview_post(post_id):
    """Preview a draft post (not yet published)."""
    post = Post.query.get_or_404(post_id)
    
    # Only author or admin can preview
    if post.author_id != current_user.id and not current_user.has_role('admin'):
        flash('You are not authorized to preview this post.', 'danger')
        return redirect(url_for('blog.manage_posts'))
    
    return render_template('blog/post.html', post=post, is_preview=True)


# Featured Posts (for homepage widgets)
@blog_blueprint.route('/blog/featured')
def featured_posts():
    """Get featured posts (JSON for AJAX or render template)."""
    try:
        posts = Post.query.filter_by(is_published=True, is_featured=True).order_by(Post.created_at.desc()).limit(5).all()
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify([{
                'id': p.id,
                'title': p.title,
                'slug': p.slug,
                'created_at': p.created_at.isoformat(),
                'image_url': url_for('blog.serve_image', post_id=p.id) if p.image else None
            } for p in posts])
        
        return render_template('blog/featured.html', posts=posts)
    except Exception as e:
        logger.error(f"Error fetching featured posts: {e}")
        return jsonify([]) if request.headers.get('Accept') == 'application/json' else redirect(url_for('blog.show_blog'))


# Series Navigation
@blog_blueprint.route('/blog/series/<string:slug>')
def show_series(slug):
    """Display all posts in a series."""
    try:
        series = PostSeries.query.filter_by(slug=slug).first_or_404()
        posts = Post.query.filter(
            Post.series_id == series.id,
            Post.is_published == True
        ).order_by(Post.series_order).all()
        
        return render_template('blog/blog_series.html', series=series, posts=posts)
    except Exception as e:
        logger.error(f"Error fetching series {slug}: {e}")
        flash('Series not found.', 'danger')
        return redirect(url_for('blog.show_blog'))


# ============================================================================
# Phase 3: Admin Routes for Blog Management
# ============================================================================

# Comment Moderation Queue
@blog_blueprint.route('/blog/admin/comments')
@login_required
@blogger_required
def comment_moderation():
    """Display comments pending moderation."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')
    
    comments = Comment.query.filter_by(status=status).order_by(Comment.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    form = CommentModerationForm()
    
    return render_template('blog/admin/comment_moderation.html', comments=comments, form=form, current_status=status)


# Comment Moderation Action
@blog_blueprint.route('/blog/admin/comments/action', methods=['POST'])
@login_required
@blogger_required
def comment_action():
    """Handle comment moderation actions (approve, reject, spam, delete)."""
    form = CommentModerationForm()
    comment_ids = request.form.getlist('comment_ids')
    
    if form.validate_on_submit() and comment_ids:
        try:
            action = form.action.data
            for comment_id in comment_ids:
                comment = Comment.query.get(int(comment_id))
                if comment:
                    if action == 'delete':
                        db.session.delete(comment)
                    else:
                        comment.status = action if action != 'approve' else 'approved'
            
            db.session.commit()
            flash(f'Comments {action}d successfully.', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error moderating comments: {e}")
            flash('An error occurred.', 'danger')
    
    return redirect(url_for('blog.comment_moderation'))


# Category Management
@blog_blueprint.route('/blog/admin/categories')
@login_required
@blogger_required
def manage_categories():
    """Display blog categories for management."""
    categories = BlogCategory.query.order_by(BlogCategory.display_order, BlogCategory.name).all()
    form = BlogCategoryForm()
    return render_template('blog/admin/manage_categories.html', categories=categories, form=form)


@blog_blueprint.route('/blog/admin/categories/new', methods=['POST'])
@login_required
@blogger_required
def new_category():
    """Create a new blog category."""
    form = BlogCategoryForm()
    if form.validate_on_submit():
        try:
            category = BlogCategory(
                name=form.name.data,
                slug=form.slug.data.lower().replace(' ', '-'),
                description=form.description.data,
                parent_id=form.parent_id.data if form.parent_id.data else None,
                display_order=form.display_order.data or 0
            )
            db.session.add(category)
            db.session.commit()
            flash('Category created successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('A category with this slug already exists.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating category: {e}")
            flash('An error occurred.', 'danger')
    return redirect(url_for('blog.manage_categories'))


@blog_blueprint.route('/blog/admin/categories/<int:id>/delete', methods=['POST'])
@login_required
@blogger_required
def delete_category(id):
    """Delete a blog category."""
    csrf_form = CSRFTokenForm()
    if csrf_form.validate_on_submit():
        category = BlogCategory.query.get_or_404(id)
        try:
            db.session.delete(category)
            db.session.commit()
            flash('Category deleted successfully.', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error deleting category: {e}")
            flash('An error occurred.', 'danger')
    return redirect(url_for('blog.manage_categories'))


# Tag Management
@blog_blueprint.route('/blog/admin/tags')
@login_required
@blogger_required
def manage_tags():
    """Display blog tags for management."""
    tags = Tag.query.order_by(Tag.name).all()
    form = TagForm()
    return render_template('blog/admin/manage_tags.html', tags=tags, form=form)


@blog_blueprint.route('/blog/admin/tags/new', methods=['POST'])
@login_required
@blogger_required
def new_tag():
    """Create a new blog tag."""
    form = TagForm()
    if form.validate_on_submit():
        try:
            tag = Tag(
                name=form.name.data,
                slug=form.slug.data.lower().replace(' ', '-')
            )
            db.session.add(tag)
            db.session.commit()
            flash('Tag created successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('A tag with this slug already exists.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating tag: {e}")
            flash('An error occurred.', 'danger')
    return redirect(url_for('blog.manage_tags'))


@blog_blueprint.route('/blog/admin/tags/<int:id>/delete', methods=['POST'])
@login_required
@blogger_required
def delete_tag(id):
    """Delete a blog tag."""
    csrf_form = CSRFTokenForm()
    if csrf_form.validate_on_submit():
        tag = Tag.query.get_or_404(id)
        try:
            db.session.delete(tag)
            db.session.commit()
            flash('Tag deleted successfully.', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error deleting tag: {e}")
            flash('An error occurred.', 'danger')
    return redirect(url_for('blog.manage_tags'))


# Series Management
@blog_blueprint.route('/blog/admin/series')
@login_required
@blogger_required
def manage_series():
    """Display post series for management."""
    series_list = PostSeries.query.order_by(PostSeries.title).all()
    form = PostSeriesForm()
    return render_template('blog/admin/manage_series.html', series_list=series_list, form=form)


@blog_blueprint.route('/blog/admin/series/new', methods=['POST'])
@login_required
@blogger_required
def new_series():
    """Create a new post series."""
    form = PostSeriesForm()
    if form.validate_on_submit():
        try:
            series = PostSeries(
                title=form.title.data,
                slug=form.slug.data.lower().replace(' ', '-'),
                description=form.description.data
            )
            db.session.add(series)
            db.session.commit()
            flash('Series created successfully.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('A series with this slug already exists.', 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating series: {e}")
            flash('An error occurred.', 'danger')
    return redirect(url_for('blog.manage_series'))


@blog_blueprint.route('/blog/admin/series/<int:id>/delete', methods=['POST'])
@login_required
@blogger_required
def delete_series(id):
    """Delete a post series."""
    csrf_form = CSRFTokenForm()
    if csrf_form.validate_on_submit():
        series = PostSeries.query.get_or_404(id)
        try:
            db.session.delete(series)
            db.session.commit()
            flash('Series deleted successfully.', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error deleting series: {e}")
            flash('An error occurred.', 'danger')
    return redirect(url_for('blog.manage_series'))


# Editorial Calendar
@blog_blueprint.route('/blog/admin/calendar')
@login_required
@blogger_required
def editorial_calendar():
    """Display editorial calendar with scheduled posts."""
    try:
        # Get all posts with publish_at set (scheduled) or recent published posts
        scheduled_posts = Post.query.filter(
            Post.publish_at != None,
            Post.is_published == False
        ).order_by(Post.publish_at).all()
        
        recent_published = Post.query.filter(
            Post.is_published == True
        ).order_by(Post.created_at.desc()).limit(20).all()
        
        return render_template('blog/admin/editorial_calendar.html', 
                             scheduled_posts=scheduled_posts, 
                             recent_published=recent_published)
    except Exception as e:
        logger.error(f"Error loading editorial calendar: {e}")
        flash('An error occurred.', 'danger')
        return redirect(url_for('blog.manage_posts'))