
import unittest
from datetime import datetime, date, time, timedelta
from app.database import db
from app.models import AppointmentType, Resource, ResourceBooking, Appointment, User, Role, Estimator, Availability, BusinessConfig
from app.modules.scheduling_service import get_appointment_type_slots, book_with_resources
from app import create_app
from app import create_app
from app.config import Config
import os
import uuid

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_phase17.db'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost.localdomain'

def create_test_app():
    return create_app(TestConfig)

class Phase17TestCase(unittest.TestCase):
    def setUp(self):
        # Ensure clean state
        if os.path.exists('test_phase17.db'):
            os.remove('test_phase17.db')

        self.app = create_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create roles (check if exists first just in case)
        if not Role.query.filter_by(name='admin').first():
            role = Role(name='admin')
            db.session.add(role)
        
        # Create user/estimator with unique data to avoid persist conflicts
        uid = str(uuid.uuid4())[:8]
        self.est_user = User(username=f'est_{uid}', email=f'est_{uid}@example.com', password='password')
        self.est_user.first_name = 'Est'
        self.est_user.last_name = 'Staff'
        db.session.add(self.est_user)
        db.session.commit()
        
        self.estimator = Estimator(name='Est Staff', user=self.est_user)
        db.session.add(self.estimator)
        db.session.commit()
        
        # Create availability (9-5)
        for d in range(5):
            av = Availability(estimator_id=self.estimator.id, day_of_week=d, start_time=time(9,0), end_time=time(17,0))
            db.session.add(av)
            
        # Create config
        conf = BusinessConfig(setting_name='buffer_time_minutes', setting_value='0')
        db.session.add(conf)
        
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()
        if os.path.exists('test_phase17.db'):
            os.remove('test_phase17.db')

    def test_appointment_type_crud(self):
        """Test creating and retrieving appointment types."""
        at = AppointmentType(
            name="Consultation", 
            slug="consult", 
            duration_minutes=60,
            price=100.00
        )
        db.session.add(at)
        db.session.commit()
        
        fetched = AppointmentType.query.filter_by(slug="consult").first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Consultation")
        self.assertEqual(fetched.get_total_duration(), 60 + 15) # 60 + 0 buffer before + 15 default after

    def test_resource_creation(self):
        """Test creating resources."""
        res = Resource(name="Room A", resource_type="room", capacity=5)
        db.session.add(res)
        db.session.commit()
        
        self.assertEqual(Resource.query.count(), 1)
        self.assertEqual(Resource.query.first().resource_type, "room")

    def test_slot_generation(self):
        """Test generating slots for an appointment type."""
        at = AppointmentType(name="Short", slug="short", duration_minutes=30, buffer_after=0)
        db.session.add(at)
        db.session.commit()
        
        # Get slots for a Monday
        # Assumes test runs on day where Monday exists in future?
        # Construct a specific future Monday
        today = date.today()
        # Find next monday
        target_date = today + timedelta(days=(7 - today.weekday()))
        
        slots = get_appointment_type_slots(at.id, target_date)
        
        self.assertTrue(len(slots) > 0)
        # 9:00, 9:15, 9:30... (15 min interval gen)
        # Estimator available 9-17.
        # Duration 30.
        # First slot 9:00.
        self.assertIn(datetime.combine(target_date, time(9,0)), slots)

    def test_booking_with_resource(self):
        """Test booking flow checking resource availability."""
        # Setup
        at = AppointmentType(name="Scan", slug="scan", duration_minutes=60, required_resource_type="equipment")
        db.session.add(at)
        
        res = Resource(name="Scanner 1", resource_type="equipment")
        db.session.add(res)
        db.session.commit()
        
        # Book for specific time
        start = datetime.combine(date.today() + timedelta(days=1), time(10, 0))
        
        data = {
            'first_name': 'Client',
            'last_name': 'One',
            'phone': '123',
            'email': 'c1@example.com',
            'preferred_date_time': start,
            'estimator_id': self.estimator.id,
            'appointment_type_id': at.id
        }
        
        # 1. Successful booking
        appt, err = book_with_resources(data, ['equipment'])
        self.assertIsNone(err)
        self.assertIsNotNone(appt)
        
        # Verify resource booking created
        rb = ResourceBooking.query.filter_by(appointment_id=appt.id).first()
        self.assertIsNotNone(rb)
        self.assertEqual(rb.resource_id, res.id)
        
        # 2. Conflict booking (same time)
        appt2, err2 = book_with_resources(data, ['equipment'])
        self.assertIsNotNone(err2) # Should fail due to resource busy
        self.assertIn("No available equipment", err2)

if __name__ == '__main__':
    unittest.main()
