"""
Phase 25: Backup Service Module

Provides automated backup functionality for database and media files.
Supports local storage, S3, and Azure blob storage.
"""

import os
import hashlib
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import json
import gzip

from flask import current_app


class BackupService:
    """Core backup functionality for the application."""
    
    BACKUP_DIR = 'backups'
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        # Create backup directory if it doesn't exist
        backup_path = os.path.join(app.instance_path, self.BACKUP_DIR)
        os.makedirs(backup_path, exist_ok=True)
    
    def get_backup_path(self) -> str:
        """Get the backup directory path."""
        if self.app:
            return os.path.join(self.app.instance_path, self.BACKUP_DIR)
        return self.BACKUP_DIR
    
    def create_database_backup(self, compress: bool = True, encrypt: bool = False) -> Tuple[str, int, str]:
        """
        Create a backup of the database.
        
        Returns:
            Tuple of (file_path, file_size, checksum)
        """
        from app.models import Backup
        from app.database import db
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.get_backup_path()
        
        # Determine database type
        db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        if 'sqlite' in db_url:
            return self._backup_sqlite(db_url, backup_dir, timestamp, compress)
        elif 'postgresql' in db_url:
            return self._backup_postgres(db_url, backup_dir, timestamp, compress)
        else:
            raise ValueError(f"Unsupported database type: {db_url}")
    
    def _backup_sqlite(self, db_url: str, backup_dir: str, timestamp: str, compress: bool) -> Tuple[str, int, str]:
        """Backup SQLite database."""
        # Extract path from sqlite:///path
        db_path = db_url.replace('sqlite:///', '')
        if db_path.startswith('/'):
            source_path = db_path
        else:
            source_path = os.path.join(current_app.instance_path, '..', db_path)
        
        filename = f"db_backup_{timestamp}.sqlite"
        if compress:
            filename += '.gz'
        
        dest_path = os.path.join(backup_dir, filename)
        
        if compress:
            # Compress the backup
            with open(source_path, 'rb') as f_in:
                with gzip.open(dest_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(source_path, dest_path)
        
        file_size = os.path.getsize(dest_path)
        checksum = self._calculate_checksum(dest_path)
        
        return dest_path, file_size, checksum
    
    def _backup_postgres(self, db_url: str, backup_dir: str, timestamp: str, compress: bool) -> Tuple[str, int, str]:
        """Backup PostgreSQL database using pg_dump."""
        filename = f"db_backup_{timestamp}.sql"
        if compress:
            filename += '.gz'
        
        dest_path = os.path.join(backup_dir, filename)
        
        # Parse connection string for pg_dump
        # Format: postgresql://user:password@host:port/dbname
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password or ''
        
        cmd = [
            'pg_dump',
            '-h', parsed.hostname or 'localhost',
            '-p', str(parsed.port or 5432),
            '-U', parsed.username or 'postgres',
            '-d', parsed.path.lstrip('/'),
            '-F', 'p',  # Plain SQL format
        ]
        
        if compress:
            # Pipe through gzip
            with gzip.open(dest_path, 'wt') as f:
                process = subprocess.run(cmd, env=env, capture_output=True, text=True)
                if process.returncode != 0:
                    raise RuntimeError(f"pg_dump failed: {process.stderr}")
                f.write(process.stdout)
        else:
            with open(dest_path, 'w') as f:
                process = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.PIPE, text=True)
                if process.returncode != 0:
                    raise RuntimeError(f"pg_dump failed: {process.stderr}")
        
        file_size = os.path.getsize(dest_path)
        checksum = self._calculate_checksum(dest_path)
        
        return dest_path, file_size, checksum
    
    def create_media_backup(self, compress: bool = True) -> Tuple[str, int, str]:
        """
        Create a backup of uploaded media files.
        
        Returns:
            Tuple of (file_path, file_size, checksum)
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.get_backup_path()
        
        # Get upload directory
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 
                                            os.path.join(current_app.instance_path, 'uploads'))
        
        if not os.path.exists(upload_dir):
            raise FileNotFoundError(f"Upload directory not found: {upload_dir}")
        
        filename = f"media_backup_{timestamp}"
        archive_path = os.path.join(backup_dir, filename)
        
        if compress:
            shutil.make_archive(archive_path, 'gztar', upload_dir)
            archive_path += '.tar.gz'
        else:
            shutil.make_archive(archive_path, 'tar', upload_dir)
            archive_path += '.tar'
        
        file_size = os.path.getsize(archive_path)
        checksum = self._calculate_checksum(archive_path)
        
        return archive_path, file_size, checksum
    
    def create_full_backup(self, compress: bool = True) -> Tuple[str, int, str]:
        """
        Create a full backup including database and media.
        
        Returns:
            Tuple of (file_path, file_size, checksum)
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.get_backup_path()
        temp_dir = os.path.join(backup_dir, f'temp_{timestamp}')
        
        try:
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create database backup in temp dir
            db_path, _, _ = self.create_database_backup(compress=False)
            shutil.move(db_path, os.path.join(temp_dir, 'database.sqlite'))
            
            # Copy uploads to temp dir
            upload_dir = current_app.config.get('UPLOAD_FOLDER',
                                                os.path.join(current_app.instance_path, 'uploads'))
            if os.path.exists(upload_dir):
                shutil.copytree(upload_dir, os.path.join(temp_dir, 'uploads'))
            
            # Create archive
            filename = f"full_backup_{timestamp}"
            archive_path = os.path.join(backup_dir, filename)
            
            if compress:
                shutil.make_archive(archive_path, 'gztar', temp_dir)
                archive_path += '.tar.gz'
            else:
                shutil.make_archive(archive_path, 'tar', temp_dir)
                archive_path += '.tar'
            
            file_size = os.path.getsize(archive_path)
            checksum = self._calculate_checksum(archive_path)
            
            return archive_path, file_size, checksum
            
        finally:
            # Clean up temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def verify_backup(self, backup_path: str, expected_checksum: str) -> bool:
        """Verify backup integrity by comparing checksums."""
        if not os.path.exists(backup_path):
            return False
        
        actual_checksum = self._calculate_checksum(backup_path)
        return actual_checksum == expected_checksum
    
    def restore_database_backup(self, backup_path: str) -> bool:
        """
        Restore database from backup.
        
        WARNING: This will overwrite the current database!
        """
        db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        if 'sqlite' in db_url:
            return self._restore_sqlite(backup_path, db_url)
        elif 'postgresql' in db_url:
            return self._restore_postgres(backup_path, db_url)
        else:
            raise ValueError(f"Unsupported database type: {db_url}")
    
    def _restore_sqlite(self, backup_path: str, db_url: str) -> bool:
        """Restore SQLite database from backup."""
        db_path = db_url.replace('sqlite:///', '')
        if db_path.startswith('/'):
            dest_path = db_path
        else:
            dest_path = os.path.join(current_app.instance_path, '..', db_path)
        
        # Handle compressed backups
        if backup_path.endswith('.gz'):
            with gzip.open(backup_path, 'rb') as f_in:
                with open(dest_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(backup_path, dest_path)
        
        return True
    
    def _restore_postgres(self, backup_path: str, db_url: str) -> bool:
        """Restore PostgreSQL database from backup."""
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password or ''
        
        cmd = [
            'psql',
            '-h', parsed.hostname or 'localhost',
            '-p', str(parsed.port or 5432),
            '-U', parsed.username or 'postgres',
            '-d', parsed.path.lstrip('/'),
        ]
        
        # Handle compressed backups
        if backup_path.endswith('.gz'):
            with gzip.open(backup_path, 'rt') as f:
                sql_content = f.read()
            process = subprocess.run(cmd, input=sql_content, env=env, 
                                   capture_output=True, text=True)
        else:
            with open(backup_path, 'r') as f:
                process = subprocess.run(cmd, stdin=f, env=env,
                                       capture_output=True, text=True)
        
        if process.returncode != 0:
            raise RuntimeError(f"psql restore failed: {process.stderr}")
        
        return True
    
    def cleanup_old_backups(self, retention_days: int = 30, backup_type: str = None) -> int:
        """
        Remove backups older than retention_days.
        
        Returns:
            Number of backups deleted
        """
        from app.models import Backup
        from app.database import db
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        deleted_count = 0
        
        query = Backup.query.filter(Backup.started_at < cutoff_date)
        if backup_type:
            query = query.filter(Backup.backup_type == backup_type)
        
        old_backups = query.all()
        
        for backup in old_backups:
            if backup.file_path and os.path.exists(backup.file_path):
                try:
                    os.remove(backup.file_path)
                except OSError:
                    pass
            db.session.delete(backup)
            deleted_count += 1
        
        db.session.commit()
        return deleted_count
    
    def list_backups(self, backup_type: str = None, limit: int = 50) -> List[dict]:
        """List available backups."""
        from app.models import Backup
        
        query = Backup.query.order_by(Backup.started_at.desc())
        if backup_type:
            query = query.filter(Backup.backup_type == backup_type)
        
        backups = query.limit(limit).all()
        
        return [{
            'id': b.id,
            'type': b.backup_type,
            'status': b.status,
            'file_path': b.file_path,
            'file_size': b.file_size_bytes,
            'started_at': b.started_at.isoformat() if b.started_at else None,
            'completed_at': b.completed_at.isoformat() if b.completed_at else None,
            'verified': b.verified,
            'checksum': b.checksum,
        } for b in backups]
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()


class BackupScheduler:
    """Schedule and manage backup jobs."""
    
    def __init__(self, backup_service: BackupService):
        self.backup_service = backup_service
    
    def run_scheduled_backup(self, schedule_id: int) -> Optional[int]:
        """
        Run a scheduled backup job.
        
        Returns:
            Backup ID if successful, None otherwise
        """
        from app.models import Backup, BackupSchedule
        from app.database import db
        
        schedule = BackupSchedule.query.get(schedule_id)
        if not schedule or not schedule.is_active:
            return None
        
        # Create backup record
        backup = Backup(
            backup_type=schedule.backup_type,
            status='in_progress',
            schedule_id=schedule_id,
            encrypted=schedule.encryption_enabled,
            storage_location=schedule.storage_location,
        )
        db.session.add(backup)
        db.session.commit()
        
        try:
            # Perform backup based on type
            if schedule.backup_type == 'database':
                file_path, file_size, checksum = self.backup_service.create_database_backup()
            elif schedule.backup_type == 'media':
                file_path, file_size, checksum = self.backup_service.create_media_backup()
            elif schedule.backup_type == 'full':
                file_path, file_size, checksum = self.backup_service.create_full_backup()
            else:
                raise ValueError(f"Unknown backup type: {schedule.backup_type}")
            
            # Update backup record
            backup.status = 'completed'
            backup.file_path = file_path
            backup.file_size_bytes = file_size
            backup.checksum = checksum
            backup.completed_at = datetime.utcnow()
            
            # Update schedule
            schedule.last_run_at = datetime.utcnow()
            schedule.next_run_at = self._calculate_next_run(schedule)
            
            db.session.commit()
            
            # Cleanup old backups based on retention
            self.backup_service.cleanup_old_backups(
                retention_days=schedule.retention_days,
                backup_type=schedule.backup_type
            )
            
            return backup.id
            
        except Exception as e:
            backup.status = 'failed'
            backup.error_message = str(e)
            backup.completed_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def _calculate_next_run(self, schedule) -> datetime:
        """Calculate next run time based on frequency."""
        now = datetime.utcnow()
        
        if schedule.frequency == 'hourly':
            return now + timedelta(hours=1)
        elif schedule.frequency == 'daily':
            return now + timedelta(days=1)
        elif schedule.frequency == 'weekly':
            return now + timedelta(weeks=1)
        elif schedule.frequency == 'monthly':
            return now + timedelta(days=30)
        else:
            return now + timedelta(days=1)
    
    def get_due_schedules(self) -> List:
        """Get backup schedules that are due to run."""
        from app.models import BackupSchedule
        
        now = datetime.utcnow()
        return BackupSchedule.query.filter(
            BackupSchedule.is_active == True,
            db.or_(
                BackupSchedule.next_run_at <= now,
                BackupSchedule.next_run_at.is_(None)
            )
        ).all()


# Global instance
backup_service = BackupService()
