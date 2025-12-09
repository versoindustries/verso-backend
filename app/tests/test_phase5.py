import unittest
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.models import User, Role, Product, Order, OrderItem
from datetime import datetime
import json

from app.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    WTF_CSRF_CHECK_DEFAULT = False
    STRIPE_SECRET_KEY = 'sk_test_mock'
    STRIPE_WEBHOOK_SECRET = 'whsec_test_mock'
    SERVER_NAME = 'localhost'

class TestPhase5(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create Admin Role & User (get-or-create pattern)
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            db.session.commit()
        
        admin = User(username='admin', email='admin@example.com', password='password')
        admin.roles.append(admin_role)
        admin.tos_accepted = True
        admin.confirmed = True
        db.session.add(admin)
        db.session.commit()
        
        # Create Product
        product = Product(name='Test Product', price=1000, inventory_count=10) # $10.00
        db.session.add(product)
        db.session.commit()
        self.product_id = product.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def test_shop_admin(self):
        self.login('admin@example.com', 'password')
        
        # Create Product
        response = self.client.post('/admin/shop/products/create', data={
            'name': 'New Shoes',
            'description': 'Comfortable',
            'price': '49.99',
            'inventory': '50'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Shoes', response.data)
        
        with self.app.app_context():
            p = Product.query.filter_by(name='New Shoes').first()
            self.assertIsNotNone(p)
            self.assertEqual(p.price, 4999)
            self.assertEqual(p.inventory_count, 50)

    def test_public_shop(self):
        response = self.client.get('/shop/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Product', response.data)
        
        response = self.client.get(f'/shop/{self.product_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Buy Now', response.data)

    @patch('app.routes.shop.stripe.checkout.Session.create')
    def test_checkout_session(self, mock_checkout):
        # Mock stripe response
        mock_checkout.return_value = MagicMock(url='http://stripe.com/checkout')
        
        self.login('admin@example.com', 'password') # Login as user
        
        response = self.client.post(f'/shop/checkout-session/{self.product_id}', follow_redirects=False)
        # Should redirect to stripe
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.location, 'http://stripe.com/checkout')
        
        # Check order created
        with self.app.app_context():
            order = Order.query.filter_by(total_amount=1000).order_by(Order.id.desc()).first()
            self.assertIsNotNone(order)
            self.assertEqual(order.status, 'pending')

    @patch('app.routes.webhooks.stripe.Webhook.construct_event')
    def test_stripe_webhook(self, mock_construct_event):
        # Create an order to pay
        order = Order(total_amount=1000, status='pending')
        db.session.add(order)
        item = OrderItem(order=order, product_id=self.product_id, quantity=1, price_at_purchase=1000)
        db.session.add(item)
        db.session.commit()
        
        # Mock payload
        payload = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'client_reference_id': str(order.id),
                    'payment_intent': 'pi_mock_123'
                }
            }
        }
        
        mock_construct_event.return_value = payload
        
        headers = {'Stripe-Signature': 'mock_sig'}
        response = self.client.post('/webhooks/stripe', data=json.dumps(payload), headers=headers)
        
        self.assertEqual(response.status_code, 200)
        
        with self.app.app_context():
            updated_order = Order.query.get(order.id)
            self.assertEqual(updated_order.status, 'paid')
            self.assertEqual(updated_order.stripe_payment_intent_id, 'pi_mock_123')
            
            # Inventory -1
            prod = Product.query.get(self.product_id)
            self.assertEqual(prod.inventory_count, 9)
