"""
Phase 3: Blog Platform Enhancement Tests
Tests for search, tags, categories, comments, and scheduled publishing.
"""
import pytest
from datetime import datetime, timedelta
from flask import url_for
from app import create_app, db
from app.models import User, Role, Post, Tag, BlogCategory, PostSeries, Comment, PostRevision


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'
    
    with app.app_context():
        db.create_all()
        
        # Create test user and blogger role
        blogger_role = Role(name='blogger')
        db.session.add(blogger_role)
        db.session.commit()
        
        user = User(username='testblogger', email='blogger@test.com', password='password123')
        user.roles.append(blogger_role)
        db.session.add(user)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def logged_in_client(app, client):
    """Client with logged in blogger user."""
    with app.app_context():
        user = User.query.filter_by(username='testblogger').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client


class TestBlogSearch:
    """Tests for blog search functionality."""
    
    def test_search_requires_query(self, client, app):
        """Test that empty search redirects to blog."""
        with app.app_context():
            response = client.get('/blog/search')
            assert response.status_code == 302  # Redirect
    
    def test_search_short_query(self, client, app):
        """Test that short query (<2 chars) redirects."""
        with app.app_context():
            response = client.get('/blog/search?q=a')
            assert response.status_code == 302
    
    def test_search_returns_results(self, client, app):
        """Test that valid search returns results page."""
        with app.app_context():
            # Create a published post
            user = User.query.first()
            post = Post(
                title='Test Python Tutorial',
                slug='test-python-tutorial',
                content='Learn Python programming language',
                author_id=user.id,
                is_published=True
            )
            db.session.add(post)
            db.session.commit()
            
            response = client.get('/blog/search?q=Python')
            assert response.status_code == 200
            assert b'Python' in response.data


class TestBlogTags:
    """Tests for blog tag functionality."""
    
    def test_tag_archive(self, client, app):
        """Test tag archive page."""
        with app.app_context():
            # Create tag and post
            tag = Tag(name='Flask', slug='flask')
            user = User.query.first()
            post = Post(
                title='Flask Tutorial',
                slug='flask-tutorial',
                content='Learn Flask',
                author_id=user.id,
                is_published=True
            )
            post.tags.append(tag)
            db.session.add_all([tag, post])
            db.session.commit()
            
            response = client.get('/blog/tag/flask')
            assert response.status_code == 200
            assert b'Flask' in response.data
    
    def test_nonexistent_tag_404(self, client, app):
        """Test that nonexistent tag returns 404."""
        with app.app_context():
            response = client.get('/blog/tag/nonexistent')
            assert response.status_code == 404


class TestBlogCategories:
    """Tests for blog category functionality."""
    
    def test_category_archive(self, client, app):
        """Test category archive page."""
        with app.app_context():
            # Create category and post
            category = BlogCategory(name='Tutorials', slug='tutorials')
            user = User.query.first()
            db.session.add(category)
            db.session.flush()
            
            post = Post(
                title='Getting Started',
                slug='getting-started',
                content='Introduction post',
                author_id=user.id,
                is_published=True,
                blog_category_id=category.id
            )
            db.session.add(post)
            db.session.commit()
            
            response = client.get('/blog/category/tutorials')
            assert response.status_code == 200
            assert b'Tutorials' in response.data


class TestComments:
    """Tests for blog comment functionality."""
    
    def test_comment_submission(self, client, app):
        """Test submitting a comment."""
        with app.app_context():
            user = User.query.first()
            post = Post(
                title='Comment Test Post',
                slug='comment-test-post',
                content='Post for testing comments',
                author_id=user.id,
                is_published=True
            )
            db.session.add(post)
            db.session.commit()
            
            response = client.post(
                '/blog/comment-test-post/comment',
                data={
                    'author_name': 'Test User',
                    'author_email': 'test@example.com',
                    'content': 'This is a test comment with sufficient length.'
                },
                follow_redirects=True
            )
            assert response.status_code == 200
            
            # Check comment was created with pending status
            comment = Comment.query.first()
            assert comment is not None
            assert comment.status == 'pending'
            assert comment.author_name == 'Test User'


class TestScheduledPublishing:
    """Tests for scheduled post publishing."""
    
    def test_scheduled_post_not_visible(self, client, app):
        """Test that scheduled posts aren't visible until publish time."""
        with app.app_context():
            user = User.query.first()
            future_date = datetime.utcnow() + timedelta(days=1)
            post = Post(
                title='Future Post',
                slug='future-post',
                content='This will be published tomorrow',
                author_id=user.id,
                is_published=False,
                publish_at=future_date
            )
            db.session.add(post)
            db.session.commit()
            
            # Post should not be accessible
            response = client.get('/blog/future-post')
            assert response.status_code == 404
    
    def test_scheduled_post_publish_worker(self, app):
        """Test the scheduled post publishing worker."""
        with app.app_context():
            from app.worker import handle_publish_scheduled_posts
            
            user = User.query.first()
            past_date = datetime.utcnow() - timedelta(hours=1)
            post = Post(
                title='Overdue Post',
                slug='overdue-post',
                content='This should have been published',
                author_id=user.id,
                is_published=False,
                publish_at=past_date
            )
            db.session.add(post)
            db.session.commit()
            
            # Run worker task
            handle_publish_scheduled_posts({})
            
            # Check post is now published
            db.session.refresh(post)
            assert post.is_published is True


class TestPostSeries:
    """Tests for blog post series functionality."""
    
    def test_series_page(self, client, app):
        """Test series archive page."""
        with app.app_context():
            user = User.query.first()
            series = PostSeries(
                title='Python Basics',
                slug='python-basics',
                description='Learn Python from scratch'
            )
            db.session.add(series)
            db.session.flush()
            
            post = Post(
                title='Part 1: Introduction',
                slug='part-1-introduction',
                content='Welcome to Python',
                author_id=user.id,
                is_published=True,
                series_id=series.id,
                series_order=1
            )
            db.session.add(post)
            db.session.commit()
            
            response = client.get('/blog/series/python-basics')
            assert response.status_code == 200
            assert b'Python Basics' in response.data


class TestRSSFeed:
    """Tests for RSS feed generation."""
    
    def test_rss_feed(self, client, app):
        """Test RSS feed returns XML."""
        with app.app_context():
            user = User.query.first()
            post = Post(
                title='RSS Test Post',
                slug='rss-test-post',
                content='Post for RSS testing',
                author_id=user.id,
                is_published=True
            )
            db.session.add(post)
            db.session.commit()
            
            response = client.get('/blog/rss')
            assert response.status_code == 200
            assert response.content_type == 'application/rss+xml'
            assert b'<?xml' in response.data
            assert b'RSS Test Post' in response.data


class TestBlogAdmin:
    """Tests for blog admin functionality."""
    
    def test_category_management_requires_login(self, client, app):
        """Test category management requires authentication."""
        with app.app_context():
            response = client.get('/blog/admin/categories')
            assert response.status_code == 302  # Redirect to login
    
    def test_tag_management_requires_login(self, client, app):
        """Test tag management requires authentication."""
        with app.app_context():
            response = client.get('/blog/admin/tags')
            assert response.status_code == 302  # Redirect to login
