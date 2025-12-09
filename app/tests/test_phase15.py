"""
Phase 15: Communication Hub Expansion Tests

Tests for email marketing, tracking, push notifications, and audience segmentation.
"""

import pytest
import json
from datetime import datetime, timedelta
from app import create_app
from app.database import db
from app.models import (
    User, Role, EmailTemplate, EmailCampaign, EmailSend, 
    Audience, AudienceMember, DripSequence, SequenceEnrollment,
    PushSubscription, EmailSuppressionList, EmailClickTrack
)


@pytest.fixture
def app():
    """Create test application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Get or create admin role
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            db.session.commit()
        
        admin = User(
            username='admin',
            email='admin@test.com',
            password='password'
        )
        admin.confirmed = True
        admin.roles.append(admin_role)
        db.session.add(admin)
        
        # Create test users
        for i in range(5):
            user = User(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='password'
            )
            user.confirmed = True
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
    """Create logged-in test client."""
    with client.session_transaction() as sess:
        # Login as admin
        admin = User.query.filter_by(username='admin').first()
        sess['_user_id'] = str(admin.id)
        sess['_fresh'] = True
    return client


class TestEmailTemplate:
    """Tests for EmailTemplate model and routes."""
    
    def test_create_template(self, app):
        """Test creating an email template."""
        with app.app_context():
            template = EmailTemplate(
                name='Test Template',
                subject='Hello {{first_name}}!',
                body_html='<html><body>Hello {{first_name}}!</body></html>',
                body_text='Hello {{first_name}}!',
                template_type='marketing',
                variables_schema={'first_name': {'default': 'Friend'}}
            )
            db.session.add(template)
            db.session.commit()
            
            assert template.id is not None
            assert template.name == 'Test Template'
    
    def test_template_render(self, app):
        """Test template variable substitution."""
        with app.app_context():
            template = EmailTemplate(
                name='Test',
                subject='Hello {{first_name}}!',
                body_html='<p>Hi {{first_name}}, your email is {{email}}</p>',
                body_text='Hi {{first_name}}',
                variables_schema={'first_name': {'default': 'Friend'}}
            )
            db.session.add(template)
            db.session.commit()
            
            # Test with context
            html, text = template.render({'first_name': 'John', 'email': 'john@test.com'})
            assert 'John' in html
            assert 'john@test.com' in html
            
            # Test with default
            html, text = template.render({'email': 'test@test.com'})
            assert 'Friend' in html  # Default value
    
    def test_template_list_route(self, app, logged_in_client):
        """Test template list admin route."""
        response = logged_in_client.get('/admin/email/templates')
        assert response.status_code == 200
    
    def test_template_create_route(self, app, logged_in_client):
        """Test template creation via route."""
        response = logged_in_client.post('/admin/email/templates/new', data={
            'name': 'Welcome Email',
            'subject': 'Welcome to our platform!',
            'body_html': '<h1>Welcome!</h1>',
            'template_type': 'welcome'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            template = EmailTemplate.query.filter_by(name='Welcome Email').first()
            assert template is not None


class TestAudience:
    """Tests for Audience segmentation."""
    
    def test_create_static_audience(self, app):
        """Test creating a static audience."""
        with app.app_context():
            audience = Audience(
                name='Test Segment',
                description='A test segment',
                is_dynamic=False
            )
            db.session.add(audience)
            db.session.commit()
            
            # Add member
            user = User.query.first()
            member = AudienceMember(
                audience_id=audience.id,
                user_id=user.id,
                email=user.email
            )
            db.session.add(member)
            db.session.commit()
            
            assert audience.members.count() == 1
    
    def test_create_dynamic_audience(self, app):
        """Test creating a dynamic audience with filter rules."""
        with app.app_context():
            audience = Audience(
                name='Recent Users',
                is_dynamic=True,
                filter_rules=[
                    {'field': 'email', 'operator': 'contains', 'value': '@test.com'}
                ]
            )
            db.session.add(audience)
            db.session.commit()
            
            assert audience.is_dynamic is True
            assert len(audience.filter_rules) == 1
    
    def test_audience_segmentation(self, app):
        """Test audience member calculation."""
        from app.modules.email_marketing import get_audience_members
        
        with app.app_context():
            audience = Audience(
                name='All Test Users',
                is_dynamic=True,
                filter_rules=[
                    {'field': 'email', 'operator': 'contains', 'value': '@test.com'}
                ]
            )
            db.session.add(audience)
            db.session.commit()
            
            members = get_audience_members(audience)
            # Should include all test users (admin + 5 users)
            assert len(members) >= 5


class TestEmailCampaign:
    """Tests for EmailCampaign model."""
    
    def test_create_campaign(self, app):
        """Test creating an email campaign."""
        with app.app_context():
            # Create template first
            template = EmailTemplate(
                name='Campaign Template',
                subject='Test Campaign',
                body_html='<p>Test</p>'
            )
            db.session.add(template)
            db.session.commit()
            
            campaign = EmailCampaign(
                name='Test Campaign',
                template_id=template.id,
                status='draft'
            )
            db.session.add(campaign)
            db.session.commit()
            
            assert campaign.id is not None
            assert campaign.status == 'draft'
    
    def test_campaign_stats(self, app):
        """Test campaign statistics calculation."""
        with app.app_context():
            template = EmailTemplate(
                name='Stats Template',
                subject='Stats Test',
                body_html='<p>Test</p>'
            )
            db.session.add(template)
            db.session.commit()
            
            campaign = EmailCampaign(
                name='Stats Campaign',
                template_id=template.id,
                status='sent'
            )
            db.session.add(campaign)
            db.session.commit()
            
            # Create some sends
            from app.modules.email_marketing import generate_tracking_token
            
            for i in range(10):
                send = EmailSend(
                    campaign_id=campaign.id,
                    recipient_email=f'recipient{i}@test.com',
                    tracking_token=generate_tracking_token()
                )
                if i < 5:  # 50% open rate
                    send.first_opened_at = datetime.utcnow()
                    send.open_count = 1
                if i < 2:  # 20% click rate
                    send.first_clicked_at = datetime.utcnow()
                    send.click_count = 1
                db.session.add(send)
            
            db.session.commit()
            
            from app.modules.email_marketing import calculate_campaign_stats
            stats = calculate_campaign_stats(campaign)
            
            assert stats['sent'] == 10
            assert stats['unique_opens'] == 5
            assert stats['unique_clicks'] == 2


class TestEmailTracking:
    """Tests for email tracking endpoints."""
    
    def test_tracking_pixel(self, app, client):
        """Test open tracking pixel."""
        with app.app_context():
            template = EmailTemplate(
                name='Tracking Template',
                subject='Tracking Test',
                body_html='<p>Test</p>'
            )
            db.session.add(template)
            db.session.commit()
            
            from app.modules.email_marketing import generate_tracking_token
            token = generate_tracking_token()
            
            send = EmailSend(
                template_id=template.id,
                recipient_email='test@test.com',
                tracking_token=token
            )
            db.session.add(send)
            db.session.commit()
            send_id = send.id
        
        # Request tracking pixel
        response = client.get(f'/t/o/{token}')
        assert response.status_code == 200
        assert response.content_type == 'image/gif'
        
        # Verify open was recorded
        with app.app_context():
            send = EmailSend.query.get(send_id)
            assert send.open_count == 1
            assert send.first_opened_at is not None
    
    def test_click_tracking(self, app, client):
        """Test click tracking redirect."""
        import base64
        
        with app.app_context():
            template = EmailTemplate(
                name='Click Template',
                subject='Click Test',
                body_html='<p>Test</p>'
            )
            db.session.add(template)
            db.session.commit()
            
            from app.modules.email_marketing import generate_tracking_token
            token = generate_tracking_token()
            
            send = EmailSend(
                template_id=template.id,
                recipient_email='test@test.com',
                tracking_token=token
            )
            db.session.add(send)
            db.session.commit()
            send_id = send.id
        
        # Request click tracking
        original_url = 'https://example.com/page'
        encoded_url = base64.urlsafe_b64encode(original_url.encode()).decode()
        
        response = client.get(f'/t/c/{token}/0?url={encoded_url}')
        assert response.status_code == 302  # Redirect
        assert 'example.com' in response.location
        
        # Verify click was recorded
        with app.app_context():
            send = EmailSend.query.get(send_id)
            assert send.click_count == 1


class TestEmailSuppression:
    """Tests for email suppression list."""
    
    def test_add_to_suppression(self, app):
        """Test adding email to suppression list."""
        from app.modules.email_marketing import add_to_suppression_list, is_email_suppressed
        
        with app.app_context():
            add_to_suppression_list('blocked@test.com', 'hard_bounce')
            
            assert is_email_suppressed('blocked@test.com') is True
            assert is_email_suppressed('allowed@test.com') is False
    
    def test_unsubscribe_route(self, app, client):
        """Test unsubscribe endpoint."""
        with app.app_context():
            from app.modules.email_marketing import generate_tracking_token
            token = generate_tracking_token()
            
            template = EmailTemplate(
                name='Unsub Template',
                subject='Test',
                body_html='<p>Test</p>'
            )
            db.session.add(template)
            db.session.commit()
            
            send = EmailSend(
                template_id=template.id,
                recipient_email='unsub@test.com',
                tracking_token=token
            )
            db.session.add(send)
            db.session.commit()
        
        # Submit unsubscribe
        response = client.post(f'/t/u/{token}', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify unsubscribe was recorded
        with app.app_context():
            suppressed = EmailSuppressionList.query.filter_by(
                email='unsub@test.com'
            ).first()
            assert suppressed is not None


class TestDripSequence:
    """Tests for drip sequence functionality."""
    
    def test_create_sequence(self, app):
        """Test creating a drip sequence."""
        with app.app_context():
            template1 = EmailTemplate(name='Step1', subject='Step 1', body_html='<p>1</p>')
            template2 = EmailTemplate(name='Step2', subject='Step 2', body_html='<p>2</p>')
            db.session.add_all([template1, template2])
            db.session.commit()
            
            sequence = DripSequence(
                name='Welcome Series',
                trigger_event='user_signup',
                steps_config=[
                    {'order': 1, 'template_id': template1.id, 'delay_hours': 0},
                    {'order': 2, 'template_id': template2.id, 'delay_hours': 24}
                ]
            )
            db.session.add(sequence)
            db.session.commit()
            
            assert sequence.id is not None
            assert len(sequence.steps_config) == 2
    
    def test_sequence_enrollment(self, app):
        """Test enrolling in a sequence."""
        from app.modules.email_marketing import enroll_in_sequence
        
        with app.app_context():
            template = EmailTemplate(name='Seq', subject='Seq', body_html='<p>Seq</p>')
            db.session.add(template)
            db.session.commit()
            
            sequence = DripSequence(
                name='Test Seq',
                trigger_event='manual',
                steps_config=[
                    {'order': 1, 'template_id': template.id, 'delay_hours': 0}
                ],
                is_active=True
            )
            db.session.add(sequence)
            db.session.commit()
            
            user = User.query.first()
            enrollment = enroll_in_sequence(sequence, user_id=user.id)
            
            assert enrollment.id is not None
            assert enrollment.status == 'active'
            assert enrollment.current_step == 0


class TestPushNotification:
    """Tests for push notification functionality."""
    
    def test_create_subscription(self, app):
        """Test creating a push subscription."""
        with app.app_context():
            user = User.query.first()
            
            sub = PushSubscription(
                user_id=user.id,
                endpoint='https://push.example.com/endpoint',
                p256dh_key='test_p256dh_key',
                auth_key='test_auth_key',
                categories=['orders', 'messages']
            )
            db.session.add(sub)
            db.session.commit()
            
            assert sub.id is not None
            assert sub.is_active is True
    
    def test_subscription_to_webpush_dict(self, app):
        """Test converting subscription to webpush format."""
        with app.app_context():
            user = User.query.first()
            
            sub = PushSubscription(
                user_id=user.id,
                endpoint='https://push.example.com/endpoint',
                p256dh_key='test_p256dh_key',
                auth_key='test_auth_key'
            )
            db.session.add(sub)
            db.session.commit()
            
            webpush_dict = sub.to_webpush_dict()
            
            assert webpush_dict['endpoint'] == 'https://push.example.com/endpoint'
            assert 'keys' in webpush_dict
            assert webpush_dict['keys']['p256dh'] == 'test_p256dh_key'
    
    def test_push_subscribe_route(self, app, logged_in_client):
        """Test push subscription API route."""
        response = logged_in_client.post('/api/push/subscribe', 
            json={
                'endpoint': 'https://test.push/endpoint',
                'keys': {
                    'p256dh': 'test_key',
                    'auth': 'test_auth'
                }
            },
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True


class TestEmailValidation:
    """Tests for email validation utilities."""
    
    def test_valid_email(self):
        """Test valid email addresses."""
        from app.modules.email_marketing import validate_email_syntax
        
        valid, error = validate_email_syntax('test@example.com')
        assert valid is True
        
        valid, error = validate_email_syntax('user.name+tag@domain.co.uk')
        assert valid is True
    
    def test_invalid_email(self):
        """Test invalid email addresses."""
        from app.modules.email_marketing import validate_email_syntax
        
        valid, error = validate_email_syntax('')
        assert valid is False
        
        valid, error = validate_email_syntax('not-an-email')
        assert valid is False
        
        valid, error = validate_email_syntax('test@.com')
        assert valid is False
    
    def test_disposable_email(self):
        """Test disposable email detection."""
        from app.modules.email_marketing import is_disposable_email
        
        assert is_disposable_email('test@mailinator.com') is True
        assert is_disposable_email('test@gmail.com') is False


class TestBounceClassification:
    """Tests for bounce classification."""
    
    def test_hard_bounce(self):
        """Test hard bounce detection."""
        from app.modules.email_marketing import classify_bounce
        
        assert classify_bounce('User unknown') == 'hard'
        assert classify_bounce('Mailbox not found') == 'hard'
        assert classify_bounce('', 550) == 'hard'
    
    def test_soft_bounce(self):
        """Test soft bounce detection."""
        from app.modules.email_marketing import classify_bounce
        
        assert classify_bounce('Mailbox full') == 'soft'
        assert classify_bounce('Try again later') == 'soft'
        assert classify_bounce('', 451) == 'soft'


class TestLinkTracking:
    """Tests for link wrapping and tracking."""
    
    def test_wrap_links(self):
        """Test link wrapping for tracking."""
        from app.modules.email_marketing import wrap_links_for_tracking
        
        html = '<a href="https://example.com">Click here</a>'
        wrapped = wrap_links_for_tracking(html, 'test_token')
        
        assert '/t/c/test_token/' in wrapped
        assert 'https://example.com' not in wrapped  # Original URL should be replaced
    
    def test_skip_mailto_links(self):
        """Test that mailto links are not wrapped."""
        from app.modules.email_marketing import wrap_links_for_tracking
        
        html = '<a href="mailto:test@test.com">Email us</a>'
        wrapped = wrap_links_for_tracking(html, 'test_token')
        
        assert 'mailto:test@test.com' in wrapped
    
    def test_inject_tracking_pixel(self):
        """Test tracking pixel injection."""
        from app.modules.email_marketing import inject_tracking_pixel
        
        html = '<html><body><p>Content</p></body></html>'
        with_pixel = inject_tracking_pixel(html, 'test_token')
        
        assert '/t/o/test_token' in with_pixel
        assert 'width="1"' in with_pixel
