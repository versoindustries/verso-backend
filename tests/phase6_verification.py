import sys
import os
import unittest
from flask import Flask
from app import create_app, db
from app.models import User, Role, AuditLog
from app.modules.audit import log_audit_event
from app.modules.data_manager import create_backup_zip, restore_from_zip
import io
import zipfile

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestPhase6(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a test user
        self.user = User(username='testadmin', email='admin@test.com', password='password')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_audit_log_creation(self):
        """Test that audit logs are created correctly."""
        print("\nTesting Audit Log Creation...")
        log_audit_event(self.user.id, 'test_action', 'User', self.user.id, {'foo': 'bar'}, '127.0.0.1')
        
        log = AuditLog.query.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action, 'test_action')
        self.assertEqual(log.user_id, self.user.id)
        self.assertEqual(log.details['foo'], 'bar')
        print("Audit Log Creation Verified.")

    def test_backup_zip_creation(self):
        """Test that backup zip is created and contains files."""
        print("\nTesting Backup ZIP Creation...")
        # Create some data
        log_audit_event(self.user.id, 'backup_test', 'User', self.user.id, {}, '127.0.0.1')
        
        zip_buffer = create_backup_zip()
        self.assertIsNotNone(zip_buffer)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            files = zf.namelist()
            print(f"Files in backup: {files}")
            self.assertIn('user.json', files)
            self.assertIn('audit_log.json', files)
            
            # Verify content
            user_data = zf.read('user.json')
            self.assertIn(b'testadmin', user_data)
            
        print("Backup ZIP Creation Verified.")

    def test_restore_from_zip(self):
        """Test restoring data from zip."""
        print("\nTesting Restore from ZIP...")
        # Create backup of current state
        zip_buffer = create_backup_zip()
        
        # Clear DB (simulate fresh state or data loss)
        db.drop_all()
        db.create_all()
        self.assertEqual(User.query.count(), 0)
        
        # Restore
        success, msg = restore_from_zip(zip_buffer)
        self.assertTrue(success, msg)
        
        # Verify
        self.assertEqual(User.query.count(), 1)
        user = User.query.first()
        self.assertEqual(user.username, 'testadmin')
        print(f"Restore Verified. User count: {User.query.count()}")

if __name__ == '__main__':
    unittest.main()
