import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, ApiKey, ContactFormSubmission, Order, Product
from app.modules.compliance import collect_user_data
import unittest
import json

class Phase8Test(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Setup Data
        self.user = User(username='testadmin', email='admin@example.com', password='password')
        db.session.add(self.user)
        
        self.lead = ContactFormSubmission(
            first_name='John', last_name='Doe', email='john@example.com', 
            phone='123', message='Hello'
        )
        db.session.add(self.lead)
        
        self.product = Product(name='Test Product', price=1000)
        db.session.add(self.product)
        
        self.order = Order(total_amount=1000) # Simple order
        db.session.add(self.order)
        
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_api_key_lifecycle(self):
        # Create Key
        key = ApiKey(name='Test Key', user_id=self.user.id, scopes=['read:leads', 'read:orders'])
        raw_key = 'sk_live_1234567890'
        key.set_key(raw_key)
        db.session.add(key)
        db.session.commit()
        
        # Test Access with Valid Key
        headers = {'Authorization': f'Bearer {raw_key}'}
        res = self.client.get('/api/v1/leads', headers=headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['email'], 'john@example.com')
        
        # Test Access with Invalid Key
        res_invalid = self.client.get('/api/v1/leads', headers={'Authorization': 'Bearer wrong'})
        self.assertEqual(res_invalid.status_code, 401)
        
        # Test Scope Failure
        # This key has read:leads, let's try products (not in scope)
        res_scope = self.client.get('/api/v1/products', headers=headers)
        self.assertEqual(res_scope.status_code, 403)
        
    def test_compliance_export(self):
        # Add data linked to email
        lead = ContactFormSubmission(
            first_name='Jane', last_name='Doe', email='jane@example.com', 
            phone='123', message='My Data'
        )
        db.session.add(lead)
        db.session.commit()
        
        data = collect_user_data(email='jane@example.com')
        self.assertTrue('contact_submissions' in data)
        self.assertEqual(data['contact_submissions'][0]['message'], 'My Data')

if __name__ == '__main__':
    unittest.main()
