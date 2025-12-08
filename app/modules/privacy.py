"""
Phase 29: Privacy & Compliance Module

GDPR/CCPA compliance tools including cookie consent, data export, and anonymization.
"""

import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from zipfile import ZipFile
from io import BytesIO

from flask import Flask, request, session, current_app


class CookieConsentManager:
    """
    Manage cookie consent for GDPR/CCPA compliance.
    """
    
    CONSENT_TYPES = ['necessary', 'functional', 'analytics', 'marketing']
    COOKIE_NAME = 'cookie_consent'
    COOKIE_MAX_AGE = 365 * 24 * 60 * 60  # 1 year in seconds
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
        self.COOKIE_NAME = app.config.get('CONSENT_COOKIE_NAME', 'cookie_consent')
    
    def get_consent(self, consent_type: str = None) -> Dict[str, bool]:
        """
        Get current consent status.
        
        Returns:
            Dict of consent type -> granted status
        """
        consent_cookie = request.cookies.get(self.COOKIE_NAME)
        
        if not consent_cookie:
            # No consent given yet - only necessary cookies allowed
            return {t: (t == 'necessary') for t in self.CONSENT_TYPES}
        
        try:
            consent = json.loads(consent_cookie)
            if consent_type:
                return consent.get(consent_type, False)
            return consent
        except (json.JSONDecodeError, TypeError):
            return {t: (t == 'necessary') for t in self.CONSENT_TYPES}
    
    def has_consent(self, consent_type: str) -> bool:
        """Check if user has granted consent for a specific type."""
        # Necessary cookies are always allowed
        if consent_type == 'necessary':
            return True
        
        consent = self.get_consent()
        return consent.get(consent_type, False)
    
    def save_consent(self, consent: Dict[str, bool], response, 
                    user_id: int = None) -> None:
        """
        Save consent preferences.
        
        Args:
            consent: Dict of consent type -> granted status
            response: Flask response object to set cookie
            user_id: Optional user ID for logged-in users
        """
        from app.models import ConsentRecord
        from app.database import db
        
        # Ensure necessary is always True
        consent['necessary'] = True
        
        # Set cookie
        response.set_cookie(
            self.COOKIE_NAME,
            json.dumps(consent),
            max_age=self.COOKIE_MAX_AGE,
            httponly=True,
            samesite='Lax',
            secure=current_app.config.get('ENV') == 'production',
        )
        
        # Log consent records
        for consent_type, granted in consent.items():
            record = ConsentRecord(
                user_id=user_id,
                session_id=session.get('_id'),
                consent_type=consent_type,
                granted=granted,
                ip_address=self._get_hashed_ip(),
                user_agent=request.headers.get('User-Agent', '')[:255],
                consent_source='cookie_banner',
                policy_version=current_app.config.get('PRIVACY_POLICY_VERSION', '1.0'),
            )
            db.session.add(record)
        
        db.session.commit()
    
    def withdraw_consent(self, consent_types: List[str] = None,
                        user_id: int = None) -> None:
        """Withdraw consent for specified types (or all non-necessary)."""
        from app.models import ConsentRecord
        from app.database import db
        
        types_to_withdraw = consent_types or ['functional', 'analytics', 'marketing']
        
        for consent_type in types_to_withdraw:
            if consent_type == 'necessary':
                continue
            
            record = ConsentRecord(
                user_id=user_id,
                session_id=session.get('_id'),
                consent_type=consent_type,
                granted=False,
                ip_address=self._get_hashed_ip(),
                user_agent=request.headers.get('User-Agent', '')[:255],
                consent_source='settings',
            )
            db.session.add(record)
        
        db.session.commit()
    
    def get_consent_history(self, user_id: int) -> List[Dict]:
        """Get consent history for a user."""
        from app.models import ConsentRecord
        
        records = ConsentRecord.query.filter_by(
            user_id=user_id
        ).order_by(ConsentRecord.created_at.desc()).limit(100).all()
        
        return [{
            'type': r.consent_type,
            'granted': r.granted,
            'source': r.consent_source,
            'created_at': r.created_at.isoformat(),
        } for r in records]
    
    def _get_hashed_ip(self) -> str:
        """Get hashed IP address for privacy."""
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip:
            ip = ip.split(',')[0].strip()
        return hashlib.sha256((ip or '').encode()).hexdigest()[:32]


class DataExporter:
    """
    Export user data for GDPR data portability requests.
    """
    
    EXPORT_EXPIRY_DAYS = 7
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
        self.EXPORT_EXPIRY_DAYS = app.config.get('DATA_EXPORT_EXPIRY_DAYS', 7)
    
    def request_export(self, user_id: int, file_format: str = 'json') -> int:
        """
        Create a data export request.
        
        Returns:
            Export request ID
        """
        from app.models import DataExportRequest
        from app.database import db
        
        # Check for existing pending/processing requests
        existing = DataExportRequest.query.filter(
            DataExportRequest.user_id == user_id,
            DataExportRequest.status.in_(['pending', 'processing'])
        ).first()
        
        if existing:
            return existing.id
        
        export_request = DataExportRequest(
            user_id=user_id,
            status='pending',
            file_format=file_format,
        )
        db.session.add(export_request)
        db.session.commit()
        
        return export_request.id
    
    def process_export(self, request_id: int) -> str:
        """
        Process a data export request and generate the export file.
        
        Returns:
            Path to the generated export file
        """
        from app.models import DataExportRequest, User
        from app.database import db
        
        export_request = DataExportRequest.query.get(request_id)
        if not export_request:
            raise ValueError("Export request not found")
        
        export_request.status = 'processing'
        export_request.processing_started_at = datetime.utcnow()
        db.session.commit()
        
        try:
            user = User.query.get(export_request.user_id)
            if not user:
                raise ValueError("User not found")
            
            # Collect user data
            data = self._collect_user_data(user)
            
            # Generate export file
            export_dir = os.path.join(
                current_app.instance_path, 
                'exports'
            )
            os.makedirs(export_dir, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"user_data_{user.id}_{timestamp}"
            
            if export_request.file_format == 'json':
                file_path = os.path.join(export_dir, f"{filename}.json")
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                # Create ZIP with CSV files
                file_path = os.path.join(export_dir, f"{filename}.zip")
                self._create_csv_export(data, file_path)
            
            # Update request
            export_request.status = 'ready'
            export_request.file_path = file_path
            export_request.file_size_bytes = os.path.getsize(file_path)
            export_request.completed_at = datetime.utcnow()
            export_request.expires_at = datetime.utcnow() + timedelta(days=self.EXPORT_EXPIRY_DAYS)
            db.session.commit()
            
            return file_path
            
        except Exception as e:
            export_request.status = 'failed'
            export_request.error_message = str(e)
            export_request.completed_at = datetime.utcnow()
            db.session.commit()
            raise
    
    def _collect_user_data(self, user) -> Dict[str, Any]:
        """Collect all user data for export."""
        from app.models import (
            Order, OrderItem, Appointment, ContactFormSubmission,
            Post, Comment, Message, ConsentRecord
        )
        
        data = {
            'export_date': datetime.utcnow().isoformat(),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'bio': user.bio,
                'timezone': user.timezone,
                'created_at': user.date.isoformat() if user.date else None,
            },
            'orders': [],
            'appointments': [],
            'leads': [],
            'posts': [],
            'comments': [],
            'messages': [],
            'consent_records': [],
        }
        
        # Orders
        orders = Order.query.filter_by(user_id=user.id).all()
        for order in orders:
            order_data = {
                'id': order.id,
                'total': float(order.total_cents) / 100 if hasattr(order, 'total_cents') else None,
                'status': order.status,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'items': []
            }
            for item in order.items:
                order_data['items'].append({
                    'product': item.product.name if item.product else 'Unknown',
                    'quantity': item.quantity,
                    'price': float(item.price_at_purchase) if item.price_at_purchase else None,
                })
            data['orders'].append(order_data)
        
        # Appointments
        appointments = Appointment.query.filter_by(email=user.email).all()
        for appt in appointments:
            data['appointments'].append({
                'id': appt.id,
                'date': appt.preferred_date_time.isoformat() if appt.preferred_date_time else None,
                'service': appt.service.name if appt.service else None,
                'status': appt.status,
            })
        
        # Contact form submissions (leads)
        leads = ContactFormSubmission.query.filter_by(email=user.email).all()
        for lead in leads:
            data['leads'].append({
                'id': lead.id,
                'message': lead.message,
                'submitted_at': lead.submitted_at.isoformat() if lead.submitted_at else None,
            })
        
        # Posts (if author)
        posts = Post.query.filter_by(author_id=user.id).all()
        for post in posts:
            data['posts'].append({
                'id': post.id,
                'title': post.title,
                'created_at': post.created_at.isoformat() if post.created_at else None,
            })
        
        # Comments
        comments = Comment.query.filter_by(user_id=user.id).all()
        for comment in comments:
            data['comments'].append({
                'id': comment.id,
                'content': comment.content,
                'post_id': comment.post_id,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
            })
        
        # Messages
        messages = Message.query.filter_by(user_id=user.id).all()
        for msg in messages:
            data['messages'].append({
                'id': msg.id,
                'channel_id': msg.channel_id,
                'content': msg.content,
                'created_at': msg.created_at.isoformat() if msg.created_at else None,
            })
        
        # Consent records
        consents = ConsentRecord.query.filter_by(user_id=user.id).all()
        for consent in consents:
            data['consent_records'].append({
                'type': consent.consent_type,
                'granted': consent.granted,
                'created_at': consent.created_at.isoformat() if consent.created_at else None,
            })
        
        return data
    
    def _create_csv_export(self, data: Dict, zip_path: str) -> None:
        """Create a ZIP file with CSV exports."""
        import csv
        
        with ZipFile(zip_path, 'w') as zipf:
            # User info
            user_csv = BytesIO()
            writer = csv.writer(user_csv)
            user = data['user']
            writer.writerow(['Field', 'Value'])
            for key, value in user.items():
                writer.writerow([key, value])
            zipf.writestr('user.csv', user_csv.getvalue())
            
            # Orders
            if data['orders']:
                orders_csv = BytesIO()
                writer = csv.writer(orders_csv)
                writer.writerow(['Order ID', 'Total', 'Status', 'Created At'])
                for order in data['orders']:
                    writer.writerow([order['id'], order['total'], order['status'], order['created_at']])
                zipf.writestr('orders.csv', orders_csv.getvalue())
            
            # Add more tables as needed
    
    def download_export(self, request_id: int, user_id: int) -> Optional[str]:
        """
        Get export file for download.
        
        Returns:
            File path if available
        """
        from app.models import DataExportRequest
        from app.database import db
        
        export_request = DataExportRequest.query.filter_by(
            id=request_id,
            user_id=user_id,
            status='ready'
        ).first()
        
        if not export_request:
            return None
        
        if export_request.expires_at and datetime.utcnow() > export_request.expires_at:
            export_request.status = 'expired'
            db.session.commit()
            return None
        
        export_request.downloaded_at = datetime.utcnow()
        export_request.download_count += 1
        db.session.commit()
        
        return export_request.file_path
    
    def cleanup_expired_exports(self) -> int:
        """Clean up expired export files."""
        from app.models import DataExportRequest
        from app.database import db
        
        expired = DataExportRequest.query.filter(
            DataExportRequest.expires_at < datetime.utcnow(),
            DataExportRequest.status == 'ready'
        ).all()
        
        count = 0
        for export in expired:
            if export.file_path and os.path.exists(export.file_path):
                try:
                    os.remove(export.file_path)
                except OSError:
                    pass
            export.status = 'expired'
            count += 1
        
        db.session.commit()
        return count


class DataAnonymizer:
    """
    Anonymize user data for right to erasure (GDPR Article 17).
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
    
    def anonymize_user(self, user_id: int, hard_delete: bool = False) -> Dict[str, int]:
        """
        Anonymize or delete user data.
        
        Args:
            user_id: User ID to anonymize
            hard_delete: If True, delete data instead of anonymizing
        
        Returns:
            Dict of table -> records affected
        """
        from app.models import (
            User, Order, Appointment, ContactFormSubmission,
            Comment, Message, ConsentRecord, LoginAttempt
        )
        from app.database import db
        
        results = {}
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        # Generate anonymous identifier
        anon_id = f"DELETED_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Anonymize/delete messages
        messages = Message.query.filter_by(user_id=user_id).all()
        for msg in messages:
            if hard_delete:
                db.session.delete(msg)
            else:
                msg.content = '[DELETED]'
        results['messages'] = len(messages)
        
        # Anonymize/delete comments
        comments = Comment.query.filter_by(user_id=user_id).all()
        for comment in comments:
            if hard_delete:
                db.session.delete(comment)
            else:
                comment.content = '[DELETED]'
                comment.author_name = 'Anonymous'
                comment.author_email = None
        results['comments'] = len(comments)
        
        # Anonymize orders (keep for financial records, but anonymize PII)
        orders = Order.query.filter_by(user_id=user_id).all()
        for order in orders:
            if hasattr(order, 'email'):
                order.email = anon_id
            if hasattr(order, 'shipping_address'):
                order.shipping_address = None
        results['orders'] = len(orders)
        
        # Anonymize appointments
        appointments = Appointment.query.filter_by(email=user.email).all()
        for appt in appointments:
            appt.first_name = 'Anonymous'
            appt.last_name = 'User'
            appt.email = f"{anon_id}@deleted.local"
            appt.phone = None
            appt.notes = None
        results['appointments'] = len(appointments)
        
        # Anonymize contact submissions
        leads = ContactFormSubmission.query.filter_by(email=user.email).all()
        for lead in leads:
            lead.first_name = 'Anonymous'
            lead.last_name = 'User'
            lead.email = f"{anon_id}@deleted.local"
            lead.phone = None
            lead.message = '[DELETED]'
        results['leads'] = len(leads)
        
        # Delete login attempts
        LoginAttempt.query.filter_by(user_id=user_id).delete()
        LoginAttempt.query.filter_by(email=user.email).delete()
        results['login_attempts'] = 1
        
        # Delete consent records (or anonymize)
        if hard_delete:
            ConsentRecord.query.filter_by(user_id=user_id).delete()
        results['consent_records'] = 1
        
        # Anonymize/delete user account
        if hard_delete:
            db.session.delete(user)
        else:
            user.username = anon_id
            user.email = f"{anon_id}@deleted.local"
            user.password_hash = ''
            user.first_name = None
            user.last_name = None
            user.phone = None
            user.bio = None
            user.confirmed = False
            # Keep created_at for audit purposes
        
        results['user'] = 1
        
        db.session.commit()
        
        return results
    
    def get_deletion_preview(self, user_id: int) -> Dict[str, int]:
        """
        Preview what data would be affected by deletion.
        """
        from app.models import (
            User, Order, Appointment, ContactFormSubmission,
            Comment, Message
        )
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        return {
            'orders': Order.query.filter_by(user_id=user_id).count(),
            'appointments': Appointment.query.filter_by(email=user.email).count(),
            'leads': ContactFormSubmission.query.filter_by(email=user.email).count(),
            'comments': Comment.query.filter_by(user_id=user_id).count(),
            'messages': Message.query.filter_by(user_id=user_id).count(),
        }


# Global instances
cookie_consent = CookieConsentManager()
data_exporter = DataExporter()
data_anonymizer = DataAnonymizer()
