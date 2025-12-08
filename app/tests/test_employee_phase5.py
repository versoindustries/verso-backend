"""
Phase 5: Employee Portal & HR Tests
Tests for leave management, document sharing, employee directory, and time tracking.
"""
import pytest
from datetime import datetime, date, timedelta
from app import create_app
from app.database import db
from app.models import (User, Role, LeaveRequest, LeaveBalance, LeaveType,
                        EncryptedDocument, DocumentShare, TimeEntry)


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        
        # Create test role
        role = Role(name='employee')
        db.session.add(role)
        
        # Create test user
        user = User(username='testuser', email='test@example.com', password='testpass')
        user.first_name = 'Test'
        user.last_name = 'User'
        user.job_title = 'Engineer'
        user.department = 'Engineering'
        user.skills = 'Python, Flask, SQL'
        user.roles.append(role)
        db.session.add(user)
        
        # Create admin user
        admin_role = Role(name='admin')
        db.session.add(admin_role)
        admin = User(username='admin', email='admin@example.com', password='adminpass')
        admin.roles.append(admin_role)
        db.session.add(admin)
        
        db.session.commit()
        
        yield app
        
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client fixture."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Authenticated test client."""
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
    return client


class TestLeaveManagement:
    """Tests for leave request and balance management."""
    
    def test_leave_request_model(self, app):
        """Test LeaveRequest model with enhanced fields."""
        with app.app_context():
            user = User.query.first()
            
            leave = LeaveRequest(
                user_id=user.id,
                leave_type='vacation',
                start_date=date(2025, 12, 20),
                end_date=date(2025, 12, 25),
                reason='Holiday vacation'
            )
            db.session.add(leave)
            db.session.commit()
            
            assert leave.id is not None
            assert leave.status == 'pending'
            assert leave.leave_type == 'vacation'
            assert leave.days_requested() == 6
    
    def test_leave_balance_model(self, app):
        """Test LeaveBalance model."""
        with app.app_context():
            user = User.query.first()
            
            balance = LeaveBalance(
                user_id=user.id,
                leave_type='vacation',
                year=2025,
                balance_days=15.0,
                used_days=3.0,
                carryover_days=2.0
            )
            db.session.add(balance)
            db.session.commit()
            
            assert balance.remaining_days() == 14.0  # 15 + 2 - 3
    
    def test_leave_balance_unique_constraint(self, app):
        """Test that duplicate balances are prevented."""
        with app.app_context():
            user = User.query.first()
            
            balance1 = LeaveBalance(
                user_id=user.id,
                leave_type='vacation',
                year=2025,
                balance_days=15.0
            )
            db.session.add(balance1)
            db.session.commit()
            
            # Attempt duplicate should fail
            balance2 = LeaveBalance(
                user_id=user.id,
                leave_type='vacation',
                year=2025,
                balance_days=20.0
            )
            db.session.add(balance2)
            with pytest.raises(Exception):
                db.session.commit()


class TestDocumentManagement:
    """Tests for encrypted document sharing."""
    
    def test_document_share_model(self, app):
        """Test DocumentShare model."""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            admin = User.query.filter_by(username='admin').first()
            
            # Create document
            doc = EncryptedDocument(
                user_id=user.id,
                title='Test Document',
                blob_data=b'encrypted content',
                category='contracts',
                requires_signature=True
            )
            db.session.add(doc)
            db.session.commit()
            
            # Share document
            share = DocumentShare(
                document_id=doc.id,
                shared_with_user_id=admin.id,
                shared_by_id=user.id,
                permissions='download'
            )
            db.session.add(share)
            db.session.commit()
            
            assert share.id is not None
            assert share.document.title == 'Test Document'
            assert share.shared_with_user.username == 'admin'
    
    def test_document_signature(self, app):
        """Test document e-signature functionality."""
        with app.app_context():
            user = User.query.first()
            
            doc = EncryptedDocument(
                user_id=user.id,
                title='Contract',
                blob_data=b'contract content',
                requires_signature=True
            )
            db.session.add(doc)
            db.session.commit()
            
            assert doc.signed_by_id is None
            
            # Sign document
            doc.signed_by_id = user.id
            doc.signed_at = datetime.utcnow()
            db.session.commit()
            
            assert doc.signed_by_id == user.id
            assert doc.signed_at is not None


class TestTimeTracking:
    """Tests for clock in/out functionality."""
    
    def test_time_entry_model(self, app):
        """Test TimeEntry model."""
        with app.app_context():
            user = User.query.first()
            now = datetime.utcnow()
            
            entry = TimeEntry(
                user_id=user.id,
                clock_in=now,
                date=now.date()
            )
            db.session.add(entry)
            db.session.commit()
            
            assert entry.id is not None
            assert entry.clock_out is None
            
            # Clock out
            entry.clock_out = now + timedelta(hours=8)
            entry.duration_minutes = entry.calculate_duration()
            db.session.commit()
            
            assert entry.duration_minutes == 480  # 8 hours
    
    def test_calculate_duration(self, app):
        """Test duration calculation."""
        with app.app_context():
            user = User.query.first()
            now = datetime.utcnow()
            
            entry = TimeEntry(
                user_id=user.id,
                clock_in=now,
                clock_out=now + timedelta(hours=4, minutes=30),
                date=now.date()
            )
            
            assert entry.calculate_duration() == 270  # 4.5 hours


class TestEmployeeDirectory:
    """Tests for employee directory and org chart."""
    
    def test_user_reports_to(self, app):
        """Test reports_to relationship for org chart."""
        with app.app_context():
            manager = User.query.filter_by(username='admin').first()
            employee = User.query.filter_by(username='testuser').first()
            
            employee.reports_to_id = manager.id
            db.session.commit()
            
            assert employee.reports_to.id == manager.id
            assert employee in manager.direct_reports.all()
    
    def test_skills_field(self, app):
        """Test skills field for directory search."""
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            assert 'Python' in user.skills
            assert 'Flask' in user.skills


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
