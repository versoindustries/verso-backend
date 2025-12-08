import unittest
from flask import url_for
from app import create_app, db
from app.models import User, Role

from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost.localdomain'

class TestPhase19Accessibility(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_viewport_meta_tag(self):
        """Test that viewport meta tag allows zooming (no user-scalable=no)."""
        response = self.client.get(url_for('main_routes.index'))
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        # Check for presence of viewport tag
        self.assertIn('<meta name="viewport"', content)
        # Check that user-scalable=no is NOT present or tag is correct
        self.assertNotIn('user-scalable=no', content)
        self.assertIn('content="width=device-width, initial-scale=1.0"', content)

    def test_accessibility_route(self):
        """Test the accessibility statement page."""
        response = self.client.get('/accessibility')
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertIn('Accessibility Statement', content)
        self.assertIn('WCAG 2.1 level AA', content)

    def test_login_form_aria_attributes(self):
        """Test that login form has proper ARIA attributes."""
        response = self.client.get(url_for('auth.login'))
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        
        # Check for aria-required
        self.assertIn('aria-required="true"', content) # Jinja renders it as is if passed as kwarg or attr
        # Wait, in the macro or direct call, it might render roughly as aria-required="true"
        # However, checking strictly:
        # We manually added aria_required="true" in login.html calls which renders as aria-required="true" in HTML.
        
        # Let's check for aria-describedby being conditionally present (might not be there if no errors)
        # We need to trigger an error to see aria-describedby
        
        # Submit empty form to trigger errors
        response = self.client.post(url_for('auth.login'), data={}, follow_redirects=True)
        content = response.get_data(as_text=True)
        
        # Now errors should exist, so aria-describedby should be present
        self.assertIn('aria-describedby="email-error"', content)
        self.assertIn('id="email-error"', content)
        self.assertIn('aria-describedby="password-error"', content)
        self.assertIn('id="password-error"', content)

if __name__ == '__main__':
    unittest.main()
