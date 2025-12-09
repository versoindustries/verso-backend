import unittest
from unittest.mock import patch
import os
from app import create_app, db
from app.models import User, Channel, Message, LeaveRequest, EncryptedDocument, Task, Appointment, Estimator, Service, Role
from app.modules.encryption import encrypt_data, decrypt_data
from datetime import datetime, date, timedelta
import json
from io import BytesIO

class TestPhase3(unittest.TestCase):
    def setUp(self):
        # Patch environment variables to ensure we use memory DB
        self.env_patcher = patch.dict(os.environ, {
            'DATABASE_URL': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-key'
        })
        self.env_patcher.start()
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['WTF_CSRF_CHECK_DEFAULT'] = False
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create user and admin
            self.user = User(username='testuser', email='test@example.com', password='password')
            self.user.tos_accepted = True
            self.user.confirmed = True
            db.session.add(self.user)
            self.admin = User(username='admin', email='admin@example.com', password='password')
            self.admin.tos_accepted = True
            self.admin.confirmed = True
            admin_role = Role(name='admin')
            self.admin.roles.append(admin_role)
            db.session.add(admin_role)
            db.session.add(self.admin)
            
            # Create basics for appointments
            self.service = Service(name='Test Service')
            self.estimator = Estimator(name='Test Estimator')
            db.session.add(self.service)
            db.session.add(self.estimator)
            
            db.session.commit()
            
            # Store IDs for use in tests to avoid DetachedInstanceError
            self.user_id = self.user.id
            self.admin_id = self.admin.id
            self.service_id = self.service.id
            self.estimator_id = self.estimator.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.env_patcher.stop()

    def login(self, email, password):
        return self.client.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def test_messaging_models(self):
        with self.app.app_context():
            channel = Channel(name='General')
            db.session.add(channel)
            db.session.commit()
            
            # Re-query user to attach to session or just use ID
            # Better to use ID for new Message
            # self.user is detached, but self.user.id is an int
            msg = Message(channel_id=channel.id, user_id=self.user_id, content='Hello')
            db.session.add(msg)
            db.session.commit()
            
            self.assertEqual(Message.query.count(), 1)
            self.assertEqual(Message.query.first().content, 'Hello')

    def test_encryption(self):
        with self.app.app_context():
            original = b"Secret Data"
            encrypted = encrypt_data(original)
            decrypted = decrypt_data(encrypted)
            self.assertEqual(original, decrypted)
            self.assertNotEqual(original, encrypted)

    def test_messaging_api(self):
        self.login('test@example.com', 'password')
        
        # Create channel
        self.client.post('/messaging/create_channel', data={'name': 'Random'})
        
        with self.app.app_context():
            channel = Channel.query.filter_by(name='Random').first()
            channel_id = channel.id
            
        # Send message
        self.client.post(f'/messaging/channel/{channel_id}/send', data={'content': 'Test Message'})
        
        # Poll
        response = self.client.get(f'/messaging/channel/{channel_id}/poll?last_id=0')
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['content'], 'Test Message')

    def test_messaging_with_attachment(self):
        self.login('test@example.com', 'password')
        
        # Create channel
        self.client.post('/messaging/create_channel', data={'name': 'Files'})
        
        with self.app.app_context():
            channel = Channel.query.filter_by(name='Files').first()
            channel_id = channel.id
            
        # Send message with file
        data = {
            'file': (BytesIO(b'file content'), 'test.txt'),
            'content': 'Check this file'
        }
        self.client.post(f'/messaging/channel/{channel_id}/send', data=data, content_type='multipart/form-data')
        
        # Poll
        response = self.client.get(f'/messaging/channel/{channel_id}/poll?last_id=0')
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['content'], 'Check this file')
        self.assertIsNotNone(data[0]['attachment'])
        self.assertEqual(data[0]['attachment']['name'], 'test.txt')

    def test_employee_leave(self):
        self.login('test@example.com', 'password')
        response = self.client.post('/employee/leave/request', data={
            'leave_type': 'vacation',
            'start_date': '2025-01-01',
            'end_date': '2025-01-05',
            'reason': 'Vacation'
        }, follow_redirects=True)
        # Verify the request succeeded (status code 200 after redirect)
        self.assertEqual(response.status_code, 200)
        
        with self.app.app_context():
            leave = LeaveRequest.query.first()
            self.assertIsNotNone(leave, "Leave request should be created in database")
            self.assertEqual(leave.reason, 'Vacation')
            self.assertEqual(leave.start_date, date(2025, 1, 1))

    def test_background_worker_task(self):
        with self.app.app_context():
            task = Task(name='test_task', payload={'foo': 'bar'})
            db.session.add(task)
            db.session.commit()
            
            # Simulate worker run (import inside test to avoid early app creation issues)
            from app.worker import run_worker, register_task_handler, TASK_HANDLERS
            # We can't run the infinite loop, but we can call the logic or just verify the model works
            # Let's verify the model
            t = Task.query.get(1)
            self.assertEqual(t.status, 'pending')

    def test_calendar_api(self):
        self.login('admin@example.com', 'password')
        
        # Create appointment directly in DB
        with self.app.app_context():
            appt = Appointment(
                first_name='John', last_name='Doe', email='j@d.com', phone='123',
                estimator_id=self.estimator.id, service_id=self.service.id,
                preferred_date_time=datetime(2025, 6, 1, 12, 0, 0)
            )
            db.session.add(appt)
            db.session.commit()
            appt_id = appt.id
            
        response = self.client.get('/calendar/api/events')
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], appt_id)
        
        # Update event
        new_time = '2025-06-02T14:00:00Z'
        response = self.client.post(f'/calendar/api/event/{appt_id}/update', data={'start': new_time})
        self.assertEqual(response.status_code, 200)
        
        with self.app.app_context():
            appt = Appointment.query.get(appt_id)
            # Check if updated (ignoring tzinfo matching logic for assertEqual if needed)
            # Models store naive UTC.
            expected = datetime(2025, 6, 2, 14, 0, 0)
            self.assertEqual(appt.preferred_date_time, expected)

if __name__ == '__main__':
    unittest.main()
