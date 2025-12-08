import unittest
from app import create_app, db
from app.models import User, Role, ContactFormSubmission, Appointment, Task, Newsletter, UnsubscribedEmail
from datetime import datetime
import json

class TestPhase4(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['WTF_CSRF_CHECK_DEFAULT'] = False
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create admin role and user
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(name='admin')
                db.session.add(admin_role)
            
            admin = User(username='admin', email='admin@example.com', password='password')
            admin.tos_accepted = True
            admin.roles.append(admin_role)
            db.session.add(admin)
            
            # Create sample leads
            c1 = ContactFormSubmission(
                first_name='John', last_name='Doe', email='john@example.com', 
                phone='1234567890', message='Hello'
            )
            c2 = ContactFormSubmission(
                first_name='Jane', last_name='Smith', email='jane@example.com', 
                phone='0987654321', message='Hi'
            )
            # Duplicate contact
            c3 = ContactFormSubmission(
                first_name='John', last_name='Doe', email='john@example.com', 
                phone='1234567890', message='Duplicate'
            )
            
            db.session.add_all([c1, c2, c3])
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, email, password):
        return self.client.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def test_crm_board(self):
        self.login('admin@example.com', 'password')
        response = self.client.get('/admin/crm/board')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Lead Management', response.data)
        self.assertIn(b'John Doe', response.data)

    def test_update_status(self):
        self.login('admin@example.com', 'password')
        
        with self.app.app_context():
            lead = ContactFormSubmission.query.filter_by(email='john@example.com').first()
            lead_id = lead.id
            
        response = self.client.post('/admin/crm/update_status', json={
            'id': lead_id,
            'type': 'contact',
            'status': 'Contacted'
        })
        self.assertEqual(response.status_code, 200)
        
        with self.app.app_context():
            lead = ContactFormSubmission.query.get(lead_id)
            self.assertEqual(lead.status, 'Contacted')

    def test_duplicates(self):
        self.login('admin@example.com', 'password')
        response = self.client.get('/admin/crm/duplicates')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'john@example.com', response.data)
        self.assertIn(b'Contact Duplicates', response.data)

    def test_web_to_lead(self):
        # 1. Normal submission (no honeypot)
        response = self.client.post('/contact', data={
            'first_name': 'Web',
            'last_name': 'Lead',
            'email': 'web@lead.com',
            'phone': '555-0199',
            'message': 'Interested in services',
            'hp_field': '' # Empty honeypot
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Thank you', response.data) # Assuming confirmation page says Thank you (let's check template later if fail)
        
        with self.app.app_context():
            submission = ContactFormSubmission.query.filter_by(email='web@lead.com').first()
            self.assertIsNotNone(submission)
            
            # Check for task
            task = Task.query.filter_by(name='new_lead_notification').order_by(Task.id.desc()).first()
            self.assertIsNotNone(task)
            self.assertEqual(task.payload['submission_id'], submission.id)

        # 2. Spam submission (honeypot filled)
        response = self.client.post('/contact', data={
            'first_name': 'Spam',
            'last_name': 'Bot',
            'email': 'spam@bot.com',
            'phone': '555-6666',
            'message': 'Spam message',
            'hp_field': 'I am a bot' 
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Should act like success
        
        with self.app.app_context():
            # Should NOT exist
            submission = ContactFormSubmission.query.filter_by(email='spam@bot.com').first()
            self.assertIsNone(submission)

    def test_newsletter_system(self):
        self.login('admin@example.com', 'password')
        
        # 1. Create Draft
        response = self.client.post('/admin/newsletter/create', data={
            'subject': 'Monthly Updates',
            'content': 'Hello World',
            'tags': 'leads, customers'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Monthly Updates', response.data)
        
        with self.app.app_context():
            # Check DB
            nl = Newsletter.query.order_by(Newsletter.id.desc()).first()
            self.assertIsNotNone(nl)
            self.assertEqual(nl.subject, 'Monthly Updates')
            self.assertEqual(nl.status, 'draft')
            self.assertEqual(nl.recipient_tags, ['leads', 'customers'])
            newsletter_id = nl.id
            
        # 2. Send Broadcast
        response = self.client.post(f'/admin/newsletter/{newsletter_id}/send', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        with self.app.app_context():
            nl = Newsletter.query.get(newsletter_id)
            self.assertEqual(nl.status, 'queued')
            
            # Check Task
            task = Task.query.filter_by(name='send_newsletter_broadcast').order_by(Task.id.desc()).first()
            self.assertIsNotNone(task)
            self.assertEqual(task.payload['newsletter_id'], newsletter_id)

    def test_unsubscribe(self):
        email = 'unsub@me.com'
        response = self.client.get(f'/unsubscribe?email={email}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'successfully unsubscribed', response.data)
        
        with self.app.app_context():
            unsub = UnsubscribedEmail.query.filter_by(email=email).first()
            self.assertIsNotNone(unsub)
            
        # Repeat should be idempotent (no error)
        response = self.client.get(f'/unsubscribe?email={email}')
        self.assertEqual(response.status_code, 200)

    def test_analytics(self):
        # 1. Trigger page view
        self.client.get('/services')
        
        with self.app.app_context():
            from app.models import PageView
            view = PageView.query.filter_by(url='/services').first()
            self.assertIsNotNone(view)
            self.assertIsNotNone(view.ip_hash)
            
        # 2. Check Dashboard (as admin)
        self.login('admin@example.com', 'password')
        response = self.client.get('/admin/analytics/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Analytics Dashboard', response.data)
        
        # 3. Check API
        response = self.client.get('/admin/analytics/api/daily_traffic')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('labels', data)
