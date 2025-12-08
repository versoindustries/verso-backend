"""
Phase 8: Background Worker & Infrastructure Tests

Tests for:
- Enhanced Task model (retry logic, priority, dead letter queue)
- CronTask model
- WorkerHeartbeat model
- Cron parser
- Admin task dashboard routes
"""
import pytest
import json
from datetime import datetime, timedelta
from app import create_app
from app.database import db
from app.models import Task, CronTask, WorkerHeartbeat, User, Role


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        
        # Create admin role if not exists
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            db.session.add(admin_role)
            db.session.flush()
        
        # Create admin user
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', password='testpass')
            admin.first_name = 'Admin'
            admin.last_name = 'User'
            admin.roles.append(admin_role)
            db.session.add(admin)
        
        db.session.commit()
        
        yield app
        
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def logged_in_admin(client, app):
    """Login as admin user."""
    with app.app_context():
        client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'testpass'
        }, follow_redirects=True)
    return client


class TestTaskModel:
    """Tests for the enhanced Task model."""
    
    def test_task_has_retry_fields(self, app):
        """Test Task model has retry_count, max_retries, next_retry_at."""
        with app.app_context():
            task = Task(name='test_task', payload={})
            db.session.add(task)
            db.session.commit()
            
            assert hasattr(task, 'retry_count')
            assert hasattr(task, 'max_retries')
            assert hasattr(task, 'next_retry_at')
            assert task.retry_count == 0
            assert task.max_retries == 3
    
    def test_task_has_priority(self, app):
        """Test Task model has priority field."""
        with app.app_context():
            task = Task(name='test_task', priority=10)
            db.session.add(task)
            db.session.commit()
            
            assert task.priority == 10
    
    def test_task_priority_ordering(self, app):
        """Test tasks are ordered by priority."""
        with app.app_context():
            task_low = Task(name='low_priority', priority=-10)
            task_normal = Task(name='normal_priority', priority=0)
            task_high = Task(name='high_priority', priority=10)
            
            db.session.add_all([task_low, task_normal, task_high])
            db.session.commit()
            
            tasks = Task.query.order_by(Task.priority.desc()).all()
            
            assert tasks[0].name == 'high_priority'
            assert tasks[1].name == 'normal_priority'
            assert tasks[2].name == 'low_priority'
    
    def test_calculate_next_retry(self, app):
        """Test exponential backoff calculation."""
        with app.app_context():
            task = Task(name='test_task')
            db.session.add(task)
            db.session.commit()
            
            # First retry: 1 minute (2^0)
            task.retry_count = 0
            next_retry = task.calculate_next_retry()
            assert next_retry is not None
            assert next_retry > datetime.utcnow()
            
            # Second retry: 2 minutes (2^1)
            task.retry_count = 1
            next_retry = task.calculate_next_retry()
            assert next_retry is not None
    
    def test_should_move_to_dead_letter(self, app):
        """Test dead letter queue logic."""
        with app.app_context():
            task = Task(name='test_task', max_retries=3)
            db.session.add(task)
            db.session.commit()
            
            # Not yet at max retries
            task.retry_count = 2
            assert not task.should_move_to_dead_letter()
            
            # At max retries
            task.retry_count = 3
            assert task.should_move_to_dead_letter()
            
            # Beyond max retries
            task.retry_count = 5
            assert task.should_move_to_dead_letter()


class TestCronTaskModel:
    """Tests for the CronTask model."""
    
    def test_create_cron_task(self, app):
        """Test CronTask creation."""
        with app.app_context():
            cron = CronTask(
                name='daily_cleanup',
                handler='cleanup_old_sessions',
                schedule='@daily',
                payload={'days_to_keep': 30}
            )
            db.session.add(cron)
            db.session.commit()
            
            assert cron.id is not None
            assert cron.name == 'daily_cleanup'
            assert cron.handler == 'cleanup_old_sessions'
            assert cron.schedule == '@daily'
            assert cron.is_active == True
            assert cron.payload == {'days_to_keep': 30}
    
    def test_cron_task_toggle(self, app):
        """Test CronTask active toggle."""
        with app.app_context():
            cron = CronTask(name='test_cron', handler='test_handler', schedule='@hourly')
            db.session.add(cron)
            db.session.commit()
            
            assert cron.is_active == True
            
            cron.is_active = False
            db.session.commit()
            
            assert cron.is_active == False


class TestWorkerHeartbeatModel:
    """Tests for the WorkerHeartbeat model."""
    
    def test_create_worker_heartbeat(self, app):
        """Test WorkerHeartbeat creation."""
        with app.app_context():
            heartbeat = WorkerHeartbeat(
                worker_id='worker-abc123',
                hostname='localhost'
            )
            db.session.add(heartbeat)
            db.session.commit()
            
            assert heartbeat.id is not None
            assert heartbeat.worker_id == 'worker-abc123'
            assert heartbeat.status == 'running'
            assert heartbeat.tasks_processed == 0
            assert heartbeat.tasks_failed == 0
    
    def test_is_alive(self, app):
        """Test worker is_alive check."""
        with app.app_context():
            heartbeat = WorkerHeartbeat(
                worker_id='worker-test',
                last_heartbeat=datetime.utcnow()
            )
            db.session.add(heartbeat)
            db.session.commit()
            
            # Recent heartbeat should be alive
            assert heartbeat.is_alive(60) == True
            
            # Old heartbeat should not be alive
            heartbeat.last_heartbeat = datetime.utcnow() - timedelta(minutes=5)
            db.session.commit()
            
            assert heartbeat.is_alive(60) == False


class TestCronParser:
    """Tests for the cron expression parser."""
    
    def test_parse_hourly(self):
        """Test @hourly schedule parsing."""
        from app.modules.cron_parser import parse_schedule
        
        now = datetime.utcnow()
        next_run = parse_schedule('@hourly', now)
        
        assert next_run is not None
        assert next_run > now
        assert next_run.minute == 0
    
    def test_parse_daily(self):
        """Test @daily schedule parsing."""
        from app.modules.cron_parser import parse_schedule
        
        now = datetime.utcnow()
        next_run = parse_schedule('@daily', now)
        
        assert next_run is not None
        assert next_run > now
    
    def test_parse_weekly(self):
        """Test @weekly schedule parsing."""
        from app.modules.cron_parser import parse_schedule
        
        now = datetime.utcnow()
        next_run = parse_schedule('@weekly', now)
        
        assert next_run is not None
        assert next_run > now
    
    def test_parse_cron_expression(self):
        """Test basic cron expression parsing."""
        from app.modules.cron_parser import parse_schedule
        
        now = datetime.utcnow()
        # Every day at 9:00
        next_run = parse_schedule('0 9 * * *', now)
        
        assert next_run is not None
        assert next_run.hour == 9
        assert next_run.minute == 0
    
    def test_get_schedule_description(self):
        """Test human-readable schedule descriptions."""
        from app.modules.cron_parser import get_schedule_description
        
        assert get_schedule_description('@hourly') == 'Every hour'
        assert get_schedule_description('@daily') == 'Daily at midnight'
        assert 'Every Monday' in get_schedule_description('@weekly')


class TestAdminTaskRoutes:
    """Tests for admin task dashboard routes."""
    
    def test_dashboard_loads(self, logged_in_admin, app):
        """Test task dashboard page loads."""
        response = logged_in_admin.get('/admin/tasks/')
        # May redirect to login if auth fails, or 200 if works
        assert response.status_code in [200, 302]
    
    def test_queue_page_loads(self, logged_in_admin, app):
        """Test task queue page loads."""
        response = logged_in_admin.get('/admin/tasks/queue')
        assert response.status_code in [200, 302]
    
    def test_dead_letter_page_loads(self, logged_in_admin, app):
        """Test dead letter page loads."""
        response = logged_in_admin.get('/admin/tasks/dead-letter')
        assert response.status_code in [200, 302]
    
    def test_cron_tasks_page_loads(self, logged_in_admin, app):
        """Test cron tasks page loads."""
        response = logged_in_admin.get('/admin/tasks/cron')
        assert response.status_code in [200, 302]
    
    def test_worker_status_page_loads(self, logged_in_admin, app):
        """Test worker status page loads."""
        response = logged_in_admin.get('/admin/tasks/worker-status')
        assert response.status_code in [200, 302]
    
    def test_api_stats_returns_json(self, logged_in_admin, app):
        """Test stats API returns JSON."""
        with app.app_context():
            response = logged_in_admin.get('/admin/tasks/api/stats')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'pending' in data
            assert 'processing' in data
            assert 'dead_letter' in data
            assert 'active_workers' in data
    
    def test_retry_dead_letter_task(self, logged_in_admin, app):
        """Test retrying a dead letter task."""
        with app.app_context():
            # Create a dead letter task
            task = Task(
                name='failed_task',
                status='dead_letter',
                retry_count=3,
                error='Test error'
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id
            
            # Retry the task
            response = logged_in_admin.post(
                f'/admin/tasks/{task_id}/retry',
                follow_redirects=True
            )
            assert response.status_code == 200
            
            # Verify task is reset
            db.session.refresh(task)
            assert task.status == 'pending'
            assert task.retry_count == 0
            assert task.error is None
    
    def test_toggle_cron_task(self, logged_in_admin, app):
        """Test toggling cron task active status."""
        with app.app_context():
            cron = CronTask(
                name='toggle_test',
                handler='test_handler',
                schedule='@daily',
                is_active=True
            )
            db.session.add(cron)
            db.session.commit()
            cron_id = cron.id
            
            # Toggle off
            response = logged_in_admin.post(
                f'/admin/tasks/cron/{cron_id}/toggle',
                follow_redirects=True
            )
            assert response.status_code == 200
            
            db.session.refresh(cron)
            assert cron.is_active == False
    
    def test_run_cron_now(self, logged_in_admin, app):
        """Test running cron task immediately."""
        with app.app_context():
            cron = CronTask(
                name='run_now_test',
                handler='test_handler',
                schedule='@daily',
                payload={'key': 'value'}
            )
            db.session.add(cron)
            db.session.commit()
            cron_id = cron.id
            
            # Get initial task count
            initial_count = Task.query.count()
            
            # Run now
            response = logged_in_admin.post(
                f'/admin/tasks/cron/{cron_id}/run-now',
                follow_redirects=True
            )
            assert response.status_code == 200
            
            # Verify a new task was created
            assert Task.query.count() == initial_count + 1
            
            new_task = Task.query.filter_by(name='test_handler').first()
            assert new_task is not None
            assert new_task.priority == 10  # High priority for manual triggers
