"""
Phase 29: Data Retention Module

Automated data retention policy management and cleanup.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from flask import Flask, current_app


class RetentionPolicyManager:
    """
    Manage data retention policies and execute cleanup jobs.
    """
    
    # Default retention policies
    DEFAULT_POLICIES = [
        {
            'name': 'login_attempts',
            'data_type': 'security',
            'table_name': 'login_attempt',
            'retention_days': 90,
            'action': 'delete',
            'description': 'Login attempt records older than 90 days',
        },
        {
            'name': 'session_data',
            'data_type': 'operational',
            'table_name': 'session',
            'retention_days': 30,
            'action': 'delete',
            'description': 'Session records older than 30 days',
        },
        {
            'name': 'analytics_pageviews',
            'data_type': 'analytics',
            'table_name': 'page_view',
            'retention_days': 365,
            'action': 'delete',
            'description': 'Page view records older than 1 year',
        },
        {
            'name': 'mfa_challenges',
            'data_type': 'security',
            'table_name': 'mfa_challenge',
            'retention_days': 7,
            'action': 'delete',
            'description': 'MFA challenges older than 7 days',
        },
        {
            'name': 'webhook_deliveries',
            'data_type': 'operational',
            'table_name': 'webhook_delivery',
            'retention_days': 30,
            'action': 'delete',
            'description': 'Webhook delivery logs older than 30 days',
        },
        {
            'name': 'audit_logs',
            'data_type': 'compliance',
            'table_name': 'audit_log',
            'retention_days': 2555,  # ~7 years for compliance
            'action': 'archive',
            'description': 'Audit logs - kept for 7 years for compliance',
        },
    ]
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
    
    def seed_default_policies(self) -> int:
        """Create default retention policies if they don't exist."""
        from app.models import RetentionPolicy
        from app.database import db
        
        created = 0
        for policy_data in self.DEFAULT_POLICIES:
            existing = RetentionPolicy.query.filter_by(name=policy_data['name']).first()
            if not existing:
                policy = RetentionPolicy(**policy_data)
                db.session.add(policy)
                created += 1
        
        db.session.commit()
        return created
    
    def get_policies(self, active_only: bool = True) -> List[Dict]:
        """Get all retention policies."""
        from app.models import RetentionPolicy
        
        query = RetentionPolicy.query
        if active_only:
            query = query.filter_by(is_active=True)
        
        policies = query.order_by(RetentionPolicy.name).all()
        
        return [{
            'id': p.id,
            'name': p.name,
            'data_type': p.data_type,
            'table_name': p.table_name,
            'retention_days': p.retention_days,
            'action': p.action,
            'is_active': p.is_active,
            'last_executed': p.last_executed_at.isoformat() if p.last_executed_at else None,
            'description': p.description,
        } for p in policies]
    
    def execute_policy(self, policy_id: int) -> Dict[str, Any]:
        """
        Execute a single retention policy.
        
        Returns:
            Execution results
        """
        from app.models import RetentionPolicy, DataRetentionLog
        from app.database import db
        
        policy = RetentionPolicy.query.get(policy_id)
        if not policy:
            raise ValueError("Policy not found")
        
        start_time = time.time()
        results = {
            'records_processed': 0,
            'records_deleted': 0,
            'records_anonymized': 0,
            'records_archived': 0,
            'status': 'success',
            'error_message': None,
        }
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
            
            # Execute based on action type
            if policy.action == 'delete':
                results = self._delete_old_records(policy.table_name, cutoff_date)
            elif policy.action == 'anonymize':
                results = self._anonymize_old_records(policy.table_name, cutoff_date)
            elif policy.action == 'archive':
                results = self._archive_old_records(policy.table_name, cutoff_date)
            
            results['status'] = 'success'
            
        except Exception as e:
            results['status'] = 'failed'
            results['error_message'] = str(e)
        
        # Log execution
        duration = time.time() - start_time
        log = DataRetentionLog(
            policy_id=policy_id,
            records_processed=results.get('records_processed', 0),
            records_deleted=results.get('records_deleted', 0),
            records_anonymized=results.get('records_anonymized', 0),
            records_archived=results.get('records_archived', 0),
            status=results['status'],
            error_message=results.get('error_message'),
            duration_seconds=duration,
        )
        db.session.add(log)
        
        # Update policy last executed
        policy.last_executed_at = datetime.utcnow()
        db.session.commit()
        
        return results
    
    def _delete_old_records(self, table_name: str, cutoff_date: datetime) -> Dict:
        """Delete records older than cutoff date."""
        from app.database import db
        
        # Map table names to model classes
        model_map = self._get_model_map()
        
        model = model_map.get(table_name)
        if not model:
            return {'records_processed': 0, 'records_deleted': 0}
        
        # Find the date column
        date_column = self._get_date_column(model)
        if not date_column:
            return {'records_processed': 0, 'records_deleted': 0}
        
        # Count and delete
        query = model.query.filter(date_column < cutoff_date)
        count = query.count()
        query.delete(synchronize_session=False)
        db.session.commit()
        
        return {
            'records_processed': count,
            'records_deleted': count,
            'records_anonymized': 0,
            'records_archived': 0,
        }
    
    def _anonymize_old_records(self, table_name: str, cutoff_date: datetime) -> Dict:
        """Anonymize records older than cutoff date."""
        from app.database import db
        
        model_map = self._get_model_map()
        model = model_map.get(table_name)
        if not model:
            return {'records_processed': 0, 'records_anonymized': 0}
        
        date_column = self._get_date_column(model)
        if not date_column:
            return {'records_processed': 0, 'records_anonymized': 0}
        
        records = model.query.filter(date_column < cutoff_date).all()
        count = 0
        
        for record in records:
            self._anonymize_record(record)
            count += 1
        
        db.session.commit()
        
        return {
            'records_processed': count,
            'records_deleted': 0,
            'records_anonymized': count,
            'records_archived': 0,
        }
    
    def _archive_old_records(self, table_name: str, cutoff_date: datetime) -> Dict:
        """Archive records older than cutoff date (log and delete or move)."""
        # For now, archiving just logs the records and keeps them
        # In a full implementation, this would move to archive storage
        
        model_map = self._get_model_map()
        model = model_map.get(table_name)
        if not model:
            return {'records_processed': 0, 'records_archived': 0}
        
        date_column = self._get_date_column(model)
        if not date_column:
            return {'records_processed': 0, 'records_archived': 0}
        
        count = model.query.filter(date_column < cutoff_date).count()
        
        # In production, this would export to cold storage
        # For now, we just count the records that would be archived
        
        return {
            'records_processed': count,
            'records_deleted': 0,
            'records_anonymized': 0,
            'records_archived': count,
        }
    
    def _get_model_map(self) -> Dict:
        """Get mapping of table names to model classes."""
        from app import models
        
        return {
            'login_attempt': getattr(models, 'LoginAttempt', None),
            'mfa_challenge': getattr(models, 'MFAChallenge', None),
            'webhook_delivery': getattr(models, 'WebhookDelivery', None),
            'page_view': getattr(models, 'PageView', None),
            'post_view': getattr(models, 'PostView', None),
            'audit_log': getattr(models, 'AuditLog', None),
            'consent_record': getattr(models, 'ConsentRecord', None),
        }
    
    def _get_date_column(self, model):
        """Get the date column for a model."""
        for col_name in ['created_at', 'executed_at', 'viewed_at', 'logged_at', 'timestamp']:
            if hasattr(model, col_name):
                return getattr(model, col_name)
        return None
    
    def _anonymize_record(self, record) -> None:
        """Anonymize PII fields in a record."""
        pii_fields = ['email', 'ip_address', 'user_agent', 'first_name', 'last_name', 'phone']
        
        for field in pii_fields:
            if hasattr(record, field):
                setattr(record, field, '[REDACTED]')
    
    def run_all_due_policies(self) -> Dict[str, Any]:
        """
        Run all retention policies that are due.
        
        Returns:
            Summary of execution results
        """
        from app.models import RetentionPolicy
        
        results = {
            'policies_executed': 0,
            'total_records_deleted': 0,
            'total_records_anonymized': 0,
            'total_records_archived': 0,
            'errors': [],
        }
        
        policies = RetentionPolicy.query.filter_by(is_active=True).all()
        
        for policy in policies:
            # Check if policy is due
            if policy.last_executed_at:
                next_run = policy.last_executed_at + timedelta(hours=policy.execution_interval_hours)
                if datetime.utcnow() < next_run:
                    continue
            
            try:
                result = self.execute_policy(policy.id)
                results['policies_executed'] += 1
                results['total_records_deleted'] += result.get('records_deleted', 0)
                results['total_records_anonymized'] += result.get('records_anonymized', 0)
                results['total_records_archived'] += result.get('records_archived', 0)
                
                if result['status'] == 'failed':
                    results['errors'].append({
                        'policy': policy.name,
                        'error': result.get('error_message'),
                    })
            
            except Exception as e:
                results['errors'].append({
                    'policy': policy.name,
                    'error': str(e),
                })
        
        return results
    
    def get_execution_history(self, policy_id: int = None, limit: int = 50) -> List[Dict]:
        """Get execution history for policies."""
        from app.models import DataRetentionLog
        
        query = DataRetentionLog.query.order_by(DataRetentionLog.executed_at.desc())
        
        if policy_id:
            query = query.filter_by(policy_id=policy_id)
        
        logs = query.limit(limit).all()
        
        return [{
            'id': log.id,
            'policy_id': log.policy_id,
            'policy_name': log.policy.name if log.policy else None,
            'records_processed': log.records_processed,
            'records_deleted': log.records_deleted,
            'records_anonymized': log.records_anonymized,
            'records_archived': log.records_archived,
            'status': log.status,
            'error_message': log.error_message,
            'executed_at': log.executed_at.isoformat() if log.executed_at else None,
            'duration_seconds': log.duration_seconds,
        } for log in logs]


# Global instance
retention_manager = RetentionPolicyManager()
