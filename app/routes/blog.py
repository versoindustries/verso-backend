from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from flask import current_app as app
from app import db, mail, bcrypt
from app.models import User, Role, Post
from app.forms import RegistrationForm, LoginForm, EstimateRequestForm, CreatePostForm, EditPostForm, CSRFTokenForm
from app.modules.auth_manager import blogger_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
import io
import bleach

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

# Blog management dashboard (blogger role required)
@blog_blueprint.route('/blog/manage')
@login_required
@blogger_required
def manage_posts():
    """Display a paginated list of all posts for management."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        # Show all posts for the current user or admins
        if current_user.has_role('admin'):
            posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        else:
            posts = Post.query.filter_by(author_id=current_user.id).order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        form = CSRFTokenForm()
        logger.debug(f"Retrieved {posts.total} posts for management by user {current_user.username}")
        return render_template('blog/manage_posts.html', posts=posts, form=form)
    except Exception as e:
        logger.error(f"Error fetching posts for management: {e}")
        flash('An error occurred while loading your posts.', 'danger')
        return render_template('blog/manage_posts.html', posts=None, form=CSRFTokenForm())

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
            post = Post(
                title=form.title.data,
                content=sanitized_content,
                category=form.category.data,
                is_published=form.is_published.data,
                author_id=current_user.id,
                slug=form.title.data.lower().replace(' ', '-'),
                image=image_data,
                image_mime_type=image_mime_type
            )
            db.session.add(post)
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
    if form.validate_on_submit():
        try:
            post.title = form.title.data
            # Sanitize the content
            post.content = bleach.clean(
                form.content.data,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRIBUTES,
                strip=True
            )
            post.category = form.category.data
            post.is_published = form.is_published.data
            post.slug = form.title.data.lower().replace(' ', '-')
            if form.image.data:
                post.image = form.image.data.read()
                post.image_mime_type = form.image.data.mimetype
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