"""
Tests for Phase 16: Forms & Data Collection Platform

Tests cover:
- Form definitions and builder
- Form submissions and validation
- Survey responses and NPS calculations
- Product reviews and moderation
- Form validation module
- Spam protection
"""

import pytest
from datetime import datetime

from app import create_app
from app.database import db


@pytest.fixture(scope='function')
def app():
    """Create and configure a test application instance."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


# =============================================================================
# Form Definition Tests
# =============================================================================

class TestFormDefinition:
    """Tests for FormDefinition model."""
    
    def test_create_form(self, app):
        """Test creating a form definition."""
        from app.models import FormDefinition
        
        with app.app_context():
            form = FormDefinition(
                name='Contact Form',
                slug='contact-form',
                description='A simple contact form',
                fields_schema=[
                    {'name': 'name', 'type': 'text', 'label': 'Name', 'required': True},
                    {'name': 'email', 'type': 'email', 'label': 'Email', 'required': True},
                    {'name': 'message', 'type': 'textarea', 'label': 'Message', 'required': True},
                ],
                settings={'submit_text': 'Send Message'},
                is_active=True
            )
            db.session.add(form)
            db.session.commit()
            
            assert form.id is not None
            assert form.slug == 'contact-form'
            assert len(form.fields_schema) == 3
    
    def test_get_field(self, app):
        """Test getting a field by name."""
        from app.models import FormDefinition
        
        with app.app_context():
            form = FormDefinition(
                name='Test Form',
                slug='test-form',
                fields_schema=[
                    {'name': 'email', 'type': 'email', 'label': 'Email'},
                    {'name': 'phone', 'type': 'phone', 'label': 'Phone'},
                ],
                is_active=True
            )
            db.session.add(form)
            db.session.commit()
            
            email_field = form.get_field('email')
            assert email_field is not None
            assert email_field['type'] == 'email'
            
            missing_field = form.get_field('nonexistent')
            assert missing_field is None
    
    def test_increment_submissions(self, app):
        """Test submission counter increment."""
        from app.models import FormDefinition
        
        with app.app_context():
            form = FormDefinition(
                name='Counter Test',
                slug='counter-test',
                fields_schema=[],
                is_active=True
            )
            db.session.add(form)
            db.session.commit()
            
            assert form.submissions_count == 0
            form.increment_submissions()
            assert form.submissions_count == 1
            form.increment_submissions()
            assert form.submissions_count == 2


# =============================================================================
# Form Submission Tests
# =============================================================================

class TestFormSubmission:
    """Tests for FormSubmission model."""
    
    def test_create_submission(self, app):
        """Test creating a form submission."""
        from app.models import FormDefinition, FormSubmission
        
        with app.app_context():
            form = FormDefinition(
                name='Test',
                slug='test',
                fields_schema=[
                    {'name': 'name', 'type': 'text', 'label': 'Name'},
                ],
                is_active=True
            )
            db.session.add(form)
            db.session.commit()
            
            submission = FormSubmission(
                form_id=form.id,
                data={'name': 'John Doe'},
                ip_address='127.0.0.1',
                user_agent='Test Browser'
            )
            db.session.add(submission)
            db.session.commit()
            
            assert submission.id is not None
            assert submission.data['name'] == 'John Doe'
            assert submission.status == 'new'
    
    def test_get_field_value(self, app):
        """Test getting field values from submission."""
        from app.models import FormDefinition, FormSubmission
        
        with app.app_context():
            form = FormDefinition(
                name='Test',
                slug='test2',
                fields_schema=[],
                is_active=True
            )
            db.session.add(form)
            db.session.commit()
            
            submission = FormSubmission(
                form_id=form.id,
                data={
                    'email': 'test@example.com',
                    'tags': ['one', 'two']
                }
            )
            db.session.add(submission)
            db.session.commit()
            
            assert submission.get_field_value('email') == 'test@example.com'
            assert submission.get_field_value('missing') is None
            assert submission.get_field_value('tags') == ['one', 'two']


# =============================================================================
# Survey Tests
# =============================================================================

class TestSurvey:
    """Tests for Survey model."""
    
    def test_create_nps_survey(self, app):
        """Test creating an NPS survey."""
        from app.models import Survey
        
        with app.app_context():
            survey = Survey(
                name='Post-Purchase NPS',
                description='How likely are you to recommend us?',
                survey_type='nps',
                questions_schema=[
                    {'id': 'nps_score', 'type': 'rating', 'text': 'Rate 0-10', 'scale': 10}
                ],
                is_active=True
            )
            db.session.add(survey)
            db.session.commit()
            
            assert survey.id is not None
            assert survey.survey_type == 'nps'
    
    def test_calculate_nps(self, app):
        """Test NPS calculation."""
        from app.models import Survey, SurveyResponse
        
        with app.app_context():
            survey = Survey(
                name='NPS Test',
                survey_type='nps',
                questions_schema=[],
                is_active=True
            )
            db.session.add(survey)
            db.session.commit()
            
            # Add responses: 2 promoters (9, 10), 1 passive (8), 1 detractor (5)
            responses = [
                SurveyResponse(survey_id=survey.id, score=10, nps_category='promoter'),
                SurveyResponse(survey_id=survey.id, score=9, nps_category='promoter'),
                SurveyResponse(survey_id=survey.id, score=8, nps_category='passive'),
                SurveyResponse(survey_id=survey.id, score=5, nps_category='detractor'),
            ]
            db.session.add_all(responses)
            db.session.commit()
            
            # NPS = (Promoters - Detractors) / Total * 100
            # NPS = (2 - 1) / 4 * 100 = 25
            nps = survey.calculate_nps()
            assert nps == 25.0


class TestSurveyResponse:
    """Tests for SurveyResponse model."""
    
    def test_classify_nps_promoter(self, app):
        """Test NPS classification for promoter."""
        from app.models import Survey, SurveyResponse
        
        with app.app_context():
            survey = Survey(
                name='Test',
                survey_type='nps',
                questions_schema=[],
                is_active=True
            )
            db.session.add(survey)
            db.session.commit()
            
            response = SurveyResponse(survey_id=survey.id, score=9)
            response.classify_nps()
            assert response.nps_category == 'promoter'
            
            response2 = SurveyResponse(survey_id=survey.id, score=10)
            response2.classify_nps()
            assert response2.nps_category == 'promoter'
    
    def test_classify_nps_passive(self, app):
        """Test NPS classification for passive."""
        from app.models import Survey, SurveyResponse
        
        with app.app_context():
            survey = Survey(
                name='Test',
                survey_type='nps',
                questions_schema=[],
                is_active=True
            )
            db.session.add(survey)
            db.session.commit()
            
            response = SurveyResponse(survey_id=survey.id, score=7)
            response.classify_nps()
            assert response.nps_category == 'passive'
            
            response2 = SurveyResponse(survey_id=survey.id, score=8)
            response2.classify_nps()
            assert response2.nps_category == 'passive'
    
    def test_classify_nps_detractor(self, app):
        """Test NPS classification for detractor."""
        from app.models import Survey, SurveyResponse
        
        with app.app_context():
            survey = Survey(
                name='Test',
                survey_type='nps',
                questions_schema=[],
                is_active=True
            )
            db.session.add(survey)
            db.session.commit()
            
            response = SurveyResponse(survey_id=survey.id, score=6)
            response.classify_nps()
            assert response.nps_category == 'detractor'
            
            response2 = SurveyResponse(survey_id=survey.id, score=0)
            response2.classify_nps()
            assert response2.nps_category == 'detractor'


# =============================================================================
# Review Tests
# =============================================================================

class TestReview:
    """Tests for Review model."""
    
    def test_create_review(self, app):
        """Test creating a product review."""
        from app.models import Review, Product
        
        with app.app_context():
            product = Product(
                name='Test Product',
                price=29.99,
                description='A test product'
            )
            db.session.add(product)
            db.session.commit()
            
            review = Review(
                product_id=product.id,
                rating=5,
                title='Great product!',
                body='I love this product.',
                verified_purchase=True
            )
            db.session.add(review)
            db.session.commit()
            
            assert review.id is not None
            assert review.status == 'pending'
            assert review.rating == 5
    
    def test_approve_review(self, app):
        """Test approving a review."""
        from app.models import Review, Product, User, Role
        
        with app.app_context():
            product = Product(
                name='Test Product',
                price=29.99,
                description='A test product'
            )
            db.session.add(product)
            
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            
            admin = User(
                username='admin',
                email='admin@test.com',
                password='testpass'
            )
            admin.roles.append(admin_role)
            db.session.add(admin)
            db.session.commit()
            
            review = Review(
                product_id=product.id,
                rating=4,
                title='Good',
                body='Pretty good'
            )
            db.session.add(review)
            db.session.commit()
            
            review.approve(admin.id)
            db.session.commit()
            
            assert review.status == 'approved'
            assert review.moderated_by_id == admin.id
            assert review.moderated_at is not None
    
    def test_reject_review(self, app):
        """Test rejecting a review."""
        from app.models import Review, Product, User, Role
        
        with app.app_context():
            product = Product(
                name='Test Product',
                price=29.99,
                description='A test product'
            )
            db.session.add(product)
            
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            
            admin = User(
                username='admin',
                email='admin@test.com',
                password='testpass'
            )
            admin.roles.append(admin_role)
            db.session.add(admin)
            db.session.commit()
            
            review = Review(
                product_id=product.id,
                rating=1,
                title='Spam',
                body='Buy cheap stuff at spam.com'
            )
            db.session.add(review)
            db.session.commit()
            
            review.reject(admin.id, 'Contains spam')
            db.session.commit()
            
            assert review.status == 'rejected'
            assert review.rejection_reason == 'Contains spam'
    
    def test_add_response(self, app):
        """Test adding owner response to review."""
        from app.models import Review, Product, User, Role
        
        with app.app_context():
            product = Product(
                name='Test Product',
                price=29.99,
                description='A test product'
            )
            db.session.add(product)
            
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            
            admin = User(
                username='admin',
                email='admin@test.com',
                password='testpass'
            )
            admin.roles.append(admin_role)
            db.session.add(admin)
            db.session.commit()
            
            review = Review(
                product_id=product.id,
                rating=3,
                title='Okay',
                body='It was okay'
            )
            db.session.add(review)
            db.session.commit()
            
            review.add_response(admin.id, 'Thank you for your feedback!')
            db.session.commit()
            
            assert review.response == 'Thank you for your feedback!'
            assert review.response_by_id == admin.id


class TestReviewVote:
    """Tests for ReviewVote model."""
    
    def test_vote_helpful(self, app):
        """Test voting a review as helpful."""
        from app.models import Review, ReviewVote, Product, User
        
        with app.app_context():
            product = Product(
                name='Test Product',
                price=29.99,
                description='A test product'
            )
            db.session.add(product)
            
            user = User(
                username='testuser',
                email='user@test.com',
                password='testpass'
            )
            db.session.add(user)
            db.session.commit()
            
            review = Review(
                product_id=product.id,
                rating=5,
                title='Amazing',
                body='Best purchase ever'
            )
            db.session.add(review)
            db.session.commit()
            
            vote = ReviewVote(
                review_id=review.id,
                user_id=user.id,
                is_helpful=True
            )
            db.session.add(vote)
            db.session.commit()
            
            assert vote.id is not None
            assert vote.is_helpful is True


# =============================================================================
# Form Validation Tests
# =============================================================================

class TestFormValidation:
    """Tests for form validation module."""
    
    def test_validate_required_field(self, app):
        """Test required field validation."""
        from app.modules.forms import FormValidator
        from app.models import FormDefinition
        
        with app.app_context():
            form = FormDefinition(
                name='Test',
                slug='test-validate',
                fields_schema=[
                    {'name': 'email', 'type': 'email', 'label': 'Email', 'required': True}
                ],
                is_active=True
            )
            db.session.add(form)
            db.session.commit()
            
            validator = FormValidator(form)
            
            # Missing required field
            is_valid, errors = validator.validate({})
            assert not is_valid
            assert 'email' in errors
            
            # Valid submission
            is_valid, errors = validator.validate({'email': 'test@example.com'})
            assert is_valid
            assert len(errors) == 0
    
    def test_validate_email_format(self, app):
        """Test email format validation."""
        from app.modules.forms import FormValidator
        from app.models import FormDefinition
        
        with app.app_context():
            form = FormDefinition(
                name='Test',
                slug='test-email',
                fields_schema=[
                    {'name': 'email', 'type': 'email', 'label': 'Email', 'required': True}
                ],
                is_active=True
            )
            db.session.add(form)
            db.session.commit()
            
            validator = FormValidator(form)
            
            # Invalid email
            is_valid, errors = validator.validate({'email': 'not-an-email'})
            assert not is_valid
            assert 'email' in errors
            
            # Valid email
            is_valid, errors = validator.validate({'email': 'valid@example.com'})
            assert is_valid


# =============================================================================
# Spam Protection Tests
# =============================================================================

class TestSpamProtection:
    """Tests for spam protection features."""
    
    def test_honeypot_detection(self):
        """Test honeypot spam detection."""
        from app.modules.forms import check_honeypot
        
        # No honeypot filled - not spam
        assert check_honeypot({}) is False
        assert check_honeypot({'hp_field': ''}) is False
        
        # Honeypot filled - is spam
        assert check_honeypot({'hp_field': 'bot text'}) is True
    
    def test_spam_score_calculation(self):
        """Test spam score calculation."""
        from app.modules.forms import calculate_spam_score
        
        # Normal submission
        score = calculate_spam_score({'name': 'John', 'message': 'Hello!'})
        assert score < 50
        
        # Spammy submission with URLs
        score = calculate_spam_score({
            'message': 'Buy now at https://spam.com and https://scam.com'
        })
        assert score > 20
        
        # Submission with spam keywords
        score = calculate_spam_score({
            'message': 'Win the lottery! Free bitcoin!'
        })
        assert score > 30


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
