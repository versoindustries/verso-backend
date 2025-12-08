import sys
import os
import unittest
from flask import Flask
from app import create_app, db
from app.models import User, Location, Appointment, Service, Estimator

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestPhase7(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create Locations
        self.loc_ny = Location(name='New York', address='123 Wall St')
        self.loc_ldn = Location(name='London', address='456 High St')
        db.session.add_all([self.loc_ny, self.loc_ldn])
        db.session.commit()
        
        # Create Users
        self.admin_ny = User(username='admin_ny', email='ny@test.com', password='password')
        self.admin_ny.location_id = self.loc_ny.id
        
        self.admin_ldn = User(username='admin_ldn', email='ldn@test.com', password='password')
        self.admin_ldn.location_id = self.loc_ldn.id
        
        self.super_admin = User(username='super', email='super@test.com', password='password')
        # No location_id means super admin / HQ
        
        db.session.add_all([self.admin_ny, self.admin_ldn, self.super_admin])
        db.session.commit()

        # Create Dependencies
        self.estimator = Estimator(name="Bob")
        db.session.add(self.estimator)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_data_scoping(self):
        """Test that data is scoped by location."""
        print("\nTesting Data Scoping...")
        
        # Create Appointments
        appt_ny = Appointment(
            first_name='Client NY', last_name='Doe', phone='123', email='c@ny.com',
            preferred_date_time=Appointment.to_utc(datetime.utcnow()), estimator_id=self.estimator.id,
            location_id=self.loc_ny.id
        )
        appt_ldn = Appointment(
            first_name='Client LDN', last_name='Doe', phone='456', email='c@ldn.com',
            preferred_date_time=Appointment.to_utc(datetime.utcnow()), estimator_id=self.estimator.id,
            location_id=self.loc_ldn.id
        )
        db.session.add_all([appt_ny, appt_ldn])
        db.session.commit()
        
        # Verify filtering logic (mimicking the admin route logic)
        
        # NY Admin should see NY appt only
        ny_appts = Appointment.query.filter_by(location_id=self.admin_ny.location_id).all()
        self.assertEqual(len(ny_appts), 1)
        self.assertEqual(ny_appts[0].first_name, 'Client NY')
        
        # LDN Admin should see LDN appt only
        ldn_appts = Appointment.query.filter_by(location_id=self.admin_ldn.location_id).all()
        self.assertEqual(len(ldn_appts), 1)
        self.assertEqual(ldn_appts[0].first_name, 'Client LDN')
        
        # Super Admin should see all (if we don't filter)
        all_appts = Appointment.query.all()
        self.assertEqual(len(all_appts), 2)
        
        print("Data Scoping Verified.")

    def test_location_creation(self):
        """Verify location creation."""
        print("\nTesting Location Creation...")
        loc = Location.query.filter_by(name='New York').first()
        self.assertIsNotNone(loc)
        self.assertEqual(loc.address, '123 Wall St')
        print("Location Creation Verified.")
        
from datetime import datetime
if __name__ == '__main__':
    unittest.main()
