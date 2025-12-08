"""
Phase 2: Calendar & Scheduling Overhaul - Tests

Tests for availability management, booking flow, staff self-service features.
"""
import unittest
from datetime import datetime, date, time, timedelta
from unittest.mock import patch, MagicMock
from app import create_app
from app.database import db
from app.models import (
    User, Role, Estimator, Service, Appointment,
    Availability, AvailabilityException, RescheduleRequest
)


class TestPhase2Models(unittest.TestCase):
    """Test Phase 2 database models."""
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()
    
    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        cls.app_context.pop()
    
    def setUp(self):
        # Create test estimator
        self.estimator = Estimator(name='Test Estimator')
        db.session.add(self.estimator)
        db.session.commit()
    
    def tearDown(self):
        db.session.rollback()
        # Clean up
        Availability.query.delete()
        AvailabilityException.query.delete()
        RescheduleRequest.query.delete()
        Appointment.query.delete()
        Estimator.query.delete()
        db.session.commit()
    
    def test_availability_model(self):
        """Test Availability model creation."""
        availability = Availability(
            estimator_id=self.estimator.id,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        db.session.add(availability)
        db.session.commit()
        
        self.assertIsNotNone(availability.id)
        self.assertEqual(availability.day_of_week, 0)
        self.assertEqual(availability.start_time, time(9, 0))
        self.assertEqual(availability.end_time, time(17, 0))
    
    def test_availability_exception_blocked(self):
        """Test AvailabilityException for blocked day."""
        exception = AvailabilityException(
            estimator_id=self.estimator.id,
            date=date(2024, 12, 25),
            is_blocked=True,
            reason='Christmas'
        )
        db.session.add(exception)
        db.session.commit()
        
        self.assertIsNotNone(exception.id)
        self.assertTrue(exception.is_blocked)
        self.assertEqual(exception.reason, 'Christmas')
    
    def test_availability_exception_custom_hours(self):
        """Test AvailabilityException with custom hours."""
        exception = AvailabilityException(
            estimator_id=self.estimator.id,
            date=date(2024, 12, 24),
            is_blocked=False,
            custom_start_time=time(9, 0),
            custom_end_time=time(12, 0),
            reason='Christmas Eve - half day'
        )
        db.session.add(exception)
        db.session.commit()
        
        self.assertFalse(exception.is_blocked)
        self.assertEqual(exception.custom_start_time, time(9, 0))
        self.assertEqual(exception.custom_end_time, time(12, 0))
    
    def test_service_duration(self):
        """Test Service model with duration field."""
        service = Service(
            name='Full Inspection',
            description='Complete home inspection',
            duration_minutes=90
        )
        db.session.add(service)
        db.session.commit()
        
        self.assertEqual(service.duration_minutes, 90)
    
    def test_appointment_staff_fields(self):
        """Test Appointment model with new staff fields."""
        service = Service(name='Test Service', duration_minutes=60)
        db.session.add(service)
        db.session.commit()
        
        appointment = Appointment(
            first_name='John',
            last_name='Doe',
            phone='555-1234',
            email='john@example.com',
            preferred_date_time=datetime.utcnow(),
            estimator_id=self.estimator.id,
            service_id=service.id,
            staff_notes='Customer prefers morning calls'
        )
        db.session.add(appointment)
        db.session.commit()
        
        self.assertIsNone(appointment.checked_in_at)
        self.assertIsNone(appointment.checked_out_at)
        self.assertEqual(appointment.staff_notes, 'Customer prefers morning calls')
    
    def test_appointment_checkin_checkout(self):
        """Test check-in/check-out functionality."""
        appointment = Appointment(
            first_name='Jane',
            last_name='Smith',
            phone='555-5678',
            email='jane@example.com',
            preferred_date_time=datetime.utcnow(),
            estimator_id=self.estimator.id
        )
        db.session.add(appointment)
        db.session.commit()
        
        # Check in
        appointment.checked_in_at = datetime.utcnow()
        db.session.commit()
        self.assertIsNotNone(appointment.checked_in_at)
        
        # Check out
        appointment.checked_out_at = datetime.utcnow()
        db.session.commit()
        self.assertIsNotNone(appointment.checked_out_at)
        
        # Calculate duration
        duration = (appointment.checked_out_at - appointment.checked_in_at).seconds // 60
        self.assertGreaterEqual(duration, 0)


class TestAvailabilityService(unittest.TestCase):
    """Test availability service functions."""
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()
    
    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        cls.app_context.pop()
    
    def setUp(self):
        self.estimator = Estimator(name='Test Estimator')
        db.session.add(self.estimator)
        db.session.commit()
    
    def tearDown(self):
        db.session.rollback()
        Availability.query.delete()
        AvailabilityException.query.delete()
        Appointment.query.delete()
        Estimator.query.delete()
        db.session.commit()
    
    def test_get_estimator_availability(self):
        """Test retrieving availability for a date."""
        from app.modules.availability_service import get_estimator_availability
        
        # Add Monday availability
        availability = Availability(
            estimator_id=self.estimator.id,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        db.session.add(availability)
        db.session.commit()
        
        # Test for a Monday
        test_date = date(2024, 12, 2)  # A Monday
        result = get_estimator_availability(self.estimator.id, test_date)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (time(9, 0), time(17, 0)))
    
    def test_availability_blocked_by_exception(self):
        """Test that exception blocks regular availability."""
        from app.modules.availability_service import get_estimator_availability
        
        # Add regular availability
        availability = Availability(
            estimator_id=self.estimator.id,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        db.session.add(availability)
        
        # Add exception that blocks this day
        exception = AvailabilityException(
            estimator_id=self.estimator.id,
            date=date(2024, 12, 2),
            is_blocked=True,
            reason='Holiday'
        )
        db.session.add(exception)
        db.session.commit()
        
        result = get_estimator_availability(self.estimator.id, date(2024, 12, 2))
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
