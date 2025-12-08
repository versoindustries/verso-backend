"""
Phase 12: Content Management Enhancement Tests

Tests for:
- Page revision history (create, view, restore)
- Custom fields API (CRUD operations)
- Staging workflow (draft -> review -> published)
- SEO features (sitemap.xml, robots.txt)
"""
import pytest
from app import create_app
from app.database import db
from app.models import User, Role, Page, PageRevision, PageCustomField, Post


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create roles if they don't exist
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
        
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user')
            db.session.add(user_role)
        
        db.session.commit()
        
        # Create admin user if doesn't exist
        admin = User.query.filter_by(email='admin@test.com').first()
        if not admin:
            admin = User(username='testadmin', email='admin@test.com', password='password123')
            admin.roles.append(admin_role)
            db.session.add(admin)
        
        # Create regular user if doesn't exist
        user = User.query.filter_by(email='user@test.com').first()
        if not user:
            user = User(username='testuser', email='user@test.com', password='password123')
            user.roles.append(user_role)
            db.session.add(user)
        
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def logged_in_admin(client, app):
    """Login as admin user."""
    with app.app_context():
        client.post('/login', data={
            'email': 'admin@test.com',
            'password': 'password123'
        }, follow_redirects=True)
    return client


@pytest.fixture
def logged_in_user(client, app):
    """Login as regular user."""
    with app.app_context():
        client.post('/login', data={
            'email': 'user@test.com',
            'password': 'password123'
        }, follow_redirects=True)
    return client


# ============================================================================
# Page Model Tests
# ============================================================================

class TestPageModel:
    """Tests for enhanced Page model."""
    
    def test_page_is_visible(self, app):
        """Test is_visible method."""
        with app.app_context():
            draft_page = Page(slug='draft', title='Draft', status='draft')
            published_page = Page(slug='pub', title='Published', status='published')
            
            db.session.add_all([draft_page, published_page])
            db.session.commit()
            
            assert draft_page.is_visible() == False
            assert published_page.is_visible() == True


# ============================================================================
# Page Revision Tests
# ============================================================================

class TestPageRevisions:
    """Tests for page revision history."""
    
    def test_create_page_creates_revision(self, logged_in_admin, app):
        """Test creating a page also creates an initial revision."""
        with app.app_context():
            response = logged_in_admin.post('/admin/page/new', data={
                'title': 'Revision Test Page',
                'slug': 'revision-test',
                'content': '<p>Initial content</p>',
                'meta_description': 'Test description',
                'status': 'draft',
                'schema_type': 'WebPage'
            }, follow_redirects=True)
            
            page = Page.query.filter_by(slug='revision-test').first()
            assert page is not None
            
            revisions = PageRevision.query.filter_by(page_id=page.id).all()
            assert len(revisions) >= 1
    
    def test_edit_page_creates_revision(self, logged_in_admin, app):
        """Test editing a page creates a new revision."""
        with app.app_context():
            # First create a page
            admin = User.query.filter_by(username='testadmin').first()
            page = Page(slug='edit-test', title='Edit Test', html_content='Original', author_id=admin.id, status='draft')
            db.session.add(page)
            db.session.commit()
            page_id = page.id
            
            # Edit the page
            response = logged_in_admin.post(f'/admin/page/{page_id}/edit', data={
                'title': 'Updated Title',
                'slug': 'edit-test',
                'content': '<p>Updated content</p>',
                'meta_description': 'Updated desc',
                'status': 'review',
                'schema_type': 'WebPage',
                'revision_note': 'Made some updates'
            }, follow_redirects=True)
            
            revisions = PageRevision.query.filter_by(page_id=page_id).all()
            assert len(revisions) >= 1
    
    def test_revision_history_page_loads(self, logged_in_admin, app):
        """Test revision history page displays correctly."""
        with app.app_context():
            admin = User.query.filter_by(username='testadmin').first()
            page = Page(slug='history-test', title='History Test', status='draft', author_id=admin.id)
            db.session.add(page)
            db.session.commit()
            
            response = logged_in_admin.get(f'/admin/page/{page.id}/revisions')
            assert response.status_code == 200
            assert b'Revision History' in response.data


# ============================================================================
# Custom Fields Tests
# ============================================================================

class TestPageCustomFields:
    """Tests for page custom fields API."""
    
    def test_add_custom_field(self, logged_in_admin, app):
        """Test adding a custom field to a page."""
        with app.app_context():
            admin = User.query.filter_by(username='testadmin').first()
            page = Page(slug='field-test', title='Field Test', status='draft', author_id=admin.id)
            db.session.add(page)
            db.session.commit()
            
            response = logged_in_admin.post(f'/admin/page/{page.id}/custom-fields', data={
                'field_name': 'test_field',
                'field_type': 'text',
                'field_value': 'Hello World',
                'display_order': 0
            }, follow_redirects=True)
            
            field = PageCustomField.query.filter_by(page_id=page.id, field_name='test_field').first()
            assert field is not None
            assert field.field_value == 'Hello World'
    
    def test_custom_field_typed_value(self, app):
        """Test custom field type conversion."""
        with app.app_context():
            page = Page(slug='typed-test', title='Typed Test', status='draft')
            db.session.add(page)
            db.session.commit()
            
            number_field = PageCustomField(
                page_id=page.id,
                field_name='price',
                field_type='number',
                field_value='99.99'
            )
            bool_field = PageCustomField(
                page_id=page.id,
                field_name='featured',
                field_type='boolean',
                field_value='true'
            )
            db.session.add_all([number_field, bool_field])
            db.session.commit()
            
            assert number_field.get_typed_value() == 99.99
            assert bool_field.get_typed_value() == True
    
    def test_delete_custom_field(self, logged_in_admin, app):
        """Test deleting a custom field."""
        with app.app_context():
            admin = User.query.filter_by(username='testadmin').first()
            page = Page(slug='delete-field-test', title='Delete Field Test', status='draft', author_id=admin.id)
            db.session.add(page)
            db.session.flush()
            
            field = PageCustomField(page_id=page.id, field_name='to_delete', field_type='text')
            db.session.add(field)
            db.session.commit()
            field_id = field.id
            
            response = logged_in_admin.post(f'/admin/page/custom-field/{field_id}/delete', follow_redirects=True)
            
            deleted = PageCustomField.query.get(field_id)
            assert deleted is None


# ============================================================================
# Staging Workflow Tests
# ============================================================================

class TestStagingWorkflow:
    """Tests for page staging workflow."""
    
    def test_page_status_transitions(self, app):
        """Test page can transition through draft -> review -> published."""
        with app.app_context():
            page = Page(slug='staging-test', title='Staging Test', status='draft')
            db.session.add(page)
            db.session.commit()
            
            assert page.status == 'draft'
            assert page.is_visible() == False
            
            page.status = 'review'
            db.session.commit()
            assert page.status == 'review'
            
            page.status = 'published'
            db.session.commit()
            assert page.status == 'published'
            assert page.is_visible() == True
    
    def test_published_pages_in_list(self, logged_in_admin, app):
        """Test admin page list shows all statuses."""
        with app.app_context():
            admin = User.query.filter_by(username='testadmin').first()
            draft = Page(slug='list-draft', title='Draft', status='draft', author_id=admin.id)
            review = Page(slug='list-review', title='Review', status='review', author_id=admin.id)
            published = Page(slug='list-pub', title='Published', status='published', author_id=admin.id)
            db.session.add_all([draft, review, published])
            db.session.commit()
            
            response = logged_in_admin.get('/admin/pages')
            assert response.status_code == 200
            assert b'Draft' in response.data
            assert b'Review' in response.data
            assert b'Published' in response.data


# ============================================================================
# SEO Tests
# ============================================================================

class TestSEOFeatures:
    """Tests for SEO features (sitemap, robots.txt, Schema.org)."""
    
    def test_sitemap_xml_route(self, client, app):
        """Test sitemap.xml is generated and accessible."""
        with app.app_context():
            response = client.get('/sitemap.xml')
            assert response.status_code == 200
            assert response.content_type.startswith('application/xml')
            assert b'<?xml version' in response.data
            assert b'urlset' in response.data
    
    def test_sitemap_includes_published_pages(self, client, app):
        """Test sitemap includes published pages."""
        with app.app_context():
            page = Page(
                slug='sitemap-test',
                title='Sitemap Test',
                status='published',
                is_published=True
            )
            db.session.add(page)
            db.session.commit()
            
            response = client.get('/sitemap.xml')
            assert response.status_code == 200
            # The page slug should be in the sitemap
            assert b'sitemap-test' in response.data
    
    def test_robots_txt_route(self, client, app):
        """Test robots.txt is accessible."""
        with app.app_context():
            response = client.get('/robots.txt')
            assert response.status_code == 200
            assert response.content_type.startswith('text/plain')
            assert b'User-agent: *' in response.data
            assert b'Sitemap:' in response.data
    
    def test_schema_json_ld_generation(self, app):
        """Test Schema.org JSON-LD is generated correctly."""
        with app.app_context():
            from app.modules.seo import generate_schema_json_ld
            
            page = Page(
                slug='schema-test',
                title='Schema Test Page',
                meta_description='A test page for schema',
                schema_type='AboutPage'
            )
            db.session.add(page)
            db.session.commit()
            
            schema = generate_schema_json_ld(page)
            
            assert schema['@context'] == 'https://schema.org'
            assert schema['@type'] == 'AboutPage'
            assert schema['name'] == 'Schema Test Page'
            assert schema['description'] == 'A test page for schema'


# ============================================================================
# Admin Access Control Tests
# ============================================================================

class TestAdminAccess:
    """Tests for admin access controls."""
    
    def test_pages_list_requires_admin(self, logged_in_user, app):
        """Test regular users cannot access page admin."""
        with app.app_context():
            response = logged_in_user.get('/admin/pages')
            assert response.status_code in [302, 403]
    
    def test_revision_history_requires_admin(self, logged_in_user, app):
        """Test regular users cannot access revision history."""
        with app.app_context():
            page = Page(slug='access-test', title='Access Test', status='draft')
            db.session.add(page)
            db.session.commit()
            
            response = logged_in_user.get(f'/admin/page/{page.id}/revisions')
            assert response.status_code in [302, 403]
