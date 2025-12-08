"""
Phase 28: MFA (Multi-Factor Authentication) Module

TOTP-based 2FA implementation with backup codes.
"""

import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from io import BytesIO
import base64

from flask import Flask, current_app


class TOTPManager:
    """
    TOTP (Time-based One-Time Password) manager for 2FA.
    
    Compatible with Google Authenticator, Authy, and other TOTP apps.
    """
    
    ISSUER = "Verso"
    DIGITS = 6
    INTERVAL = 30  # seconds
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
        self.ISSUER = app.config.get('MFA_ISSUER', 'Verso')
        self.DIGITS = app.config.get('MFA_DIGITS', 6)
        self.INTERVAL = app.config.get('MFA_INTERVAL', 30)
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret."""
        try:
            import pyotp
            return pyotp.random_base32()
        except ImportError:
            # Fallback if pyotp not installed
            return base64.b32encode(secrets.token_bytes(20)).decode('utf-8')
    
    def get_totp_uri(self, secret: str, email: str) -> str:
        """Get the TOTP provisioning URI for QR code."""
        try:
            import pyotp
            totp = pyotp.TOTP(secret, digits=self.DIGITS, interval=self.INTERVAL)
            return totp.provisioning_uri(name=email, issuer_name=self.ISSUER)
        except ImportError:
            # Manual URI construction
            return f"otpauth://totp/{self.ISSUER}:{email}?secret={secret}&issuer={self.ISSUER}&digits={self.DIGITS}&period={self.INTERVAL}"
    
    def generate_qr_code(self, secret: str, email: str) -> str:
        """
        Generate a QR code image for the TOTP secret.
        
        Returns:
            Base64-encoded PNG image
        """
        try:
            import qrcode
            from PIL import Image
            
            uri = self.get_totp_uri(secret, email)
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except ImportError:
            return ""
    
    def verify_token(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verify a TOTP token.
        
        Args:
            secret: The TOTP secret
            token: The token to verify
            window: Number of time steps to check (for clock drift)
        
        Returns:
            True if token is valid
        """
        try:
            import pyotp
            totp = pyotp.TOTP(secret, digits=self.DIGITS, interval=self.INTERVAL)
            return totp.verify(token, valid_window=window)
        except ImportError:
            # Fallback implementation
            return self._verify_token_fallback(secret, token, window)
    
    def _verify_token_fallback(self, secret: str, token: str, window: int) -> bool:
        """Fallback TOTP verification without pyotp."""
        import hmac
        import struct
        import time
        
        try:
            key = base64.b32decode(secret.upper())
        except Exception:
            return False
        
        current_time = int(time.time())
        
        for offset in range(-window, window + 1):
            counter = (current_time + offset * self.INTERVAL) // self.INTERVAL
            
            # Generate HOTP
            counter_bytes = struct.pack('>Q', counter)
            hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
            
            offset_byte = hmac_hash[-1] & 0x0f
            code = struct.unpack('>I', hmac_hash[offset_byte:offset_byte + 4])[0]
            code = (code & 0x7fffffff) % (10 ** self.DIGITS)
            
            expected = str(code).zfill(self.DIGITS)
            
            if hmac.compare_digest(expected, token):
                return True
        
        return False
    
    def generate_backup_codes(self) -> List[str]:
        """
        Generate a set of backup codes.
        
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(self.BACKUP_CODE_COUNT):
            code = secrets.token_hex(self.BACKUP_CODE_LENGTH // 2)
            # Format as XXXX-XXXX for readability
            formatted = f"{code[:4]}-{code[4:]}"
            codes.append(formatted)
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """Hash a backup code for storage."""
        # Remove formatting
        clean_code = code.replace('-', '').lower()
        return hashlib.sha256(clean_code.encode()).hexdigest()
    
    def verify_backup_code(self, code: str, hashed_codes: List[str]) -> Tuple[bool, Optional[int]]:
        """
        Verify a backup code against the list of hashed codes.
        
        Returns:
            Tuple of (is_valid, index_of_used_code)
        """
        code_hash = self.hash_backup_code(code)
        
        for i, stored_hash in enumerate(hashed_codes):
            if hmac.compare_digest(code_hash, stored_hash):
                return True, i
        
        return False, None


class MFAService:
    """
    High-level MFA service for user enrollment and verification.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.totp = TOTPManager()
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
        self.totp.init_app(app)
    
    def enroll_user(self, user_id: int, mfa_type: str = 'totp') -> dict:
        """
        Start MFA enrollment for a user.
        
        Returns:
            Enrollment data including secret, QR code, and backup codes
        """
        from app.models import UserMFA, User
        from app.database import db
        from app.modules.encryption import encrypt_data
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Generate secret
        secret = self.totp.generate_secret()
        
        # Generate QR code
        qr_code = self.totp.generate_qr_code(secret, user.email)
        
        # Generate backup codes
        backup_codes = self.totp.generate_backup_codes()
        hashed_codes = [self.totp.hash_backup_code(code) for code in backup_codes]
        
        # Encrypt secret for storage (returns bytes, store as base64)
        encrypted_secret = base64.b64encode(encrypt_data(secret)).decode('utf-8')
        encrypted_backup = base64.b64encode(encrypt_data(json.dumps(hashed_codes))).decode('utf-8')
        
        # Create or update MFA record
        mfa = UserMFA.query.filter_by(user_id=user_id, mfa_type=mfa_type).first()
        if not mfa:
            mfa = UserMFA(user_id=user_id, mfa_type=mfa_type)
            db.session.add(mfa)
        
        mfa.secret_encrypted = encrypted_secret
        mfa.backup_codes_encrypted = encrypted_backup
        mfa.is_enabled = False  # Not enabled until verified
        mfa.is_verified = False
        
        db.session.commit()
        
        return {
            'mfa_id': mfa.id,
            'secret': secret,  # Only shown once during enrollment
            'qr_code': qr_code,
            'backup_codes': backup_codes,  # Only shown once
            'uri': self.totp.get_totp_uri(secret, user.email),
        }
    
    def verify_enrollment(self, user_id: int, token: str, 
                         mfa_type: str = 'totp') -> bool:
        """
        Verify MFA enrollment by confirming the user can generate valid tokens.
        
        Returns:
            True if verification successful
        """
        from app.models import UserMFA
        from app.database import db
        from app.modules.encryption import decrypt_data
        
        mfa = UserMFA.query.filter_by(user_id=user_id, mfa_type=mfa_type).first()
        if not mfa or not mfa.secret_encrypted:
            return False
        
        # Decrypt secret (stored as base64-encoded bytes)
        secret = decrypt_data(base64.b64decode(mfa.secret_encrypted)).decode('utf-8')
        
        # Verify token
        if self.totp.verify_token(secret, token):
            mfa.is_enabled = True
            mfa.is_verified = True
            mfa.verified_at = datetime.utcnow()
            db.session.commit()
            return True
        
        return False
    
    def verify_token(self, user_id: int, token: str, 
                    mfa_type: str = 'totp') -> bool:
        """
        Verify a TOTP token for login.
        
        Returns:
            True if token is valid
        """
        from app.models import UserMFA
        from app.database import db
        from app.modules.encryption import decrypt_data
        
        mfa = UserMFA.query.filter_by(
            user_id=user_id, 
            mfa_type=mfa_type,
            is_enabled=True
        ).first()
        
        if not mfa or not mfa.secret_encrypted:
            return False
        
        # Decrypt secret (stored as base64-encoded bytes)
        secret = decrypt_data(base64.b64decode(mfa.secret_encrypted)).decode('utf-8')
        
        # Verify token
        if self.totp.verify_token(secret, token):
            mfa.last_used_at = datetime.utcnow()
            db.session.commit()
            return True
        
        return False
    
    def verify_backup_code(self, user_id: int, code: str,
                          mfa_type: str = 'totp') -> bool:
        """
        Verify and consume a backup code.
        
        Returns:
            True if code is valid (and now consumed)
        """
        from app.models import UserMFA
        from app.database import db
        from app.modules.encryption import decrypt_data, encrypt_data
        
        mfa = UserMFA.query.filter_by(
            user_id=user_id,
            mfa_type=mfa_type,
            is_enabled=True
        ).first()
        
        if not mfa or not mfa.backup_codes_encrypted:
            return False
        
        # Decrypt backup codes (stored as base64-encoded bytes)
        hashed_codes = json.loads(decrypt_data(base64.b64decode(mfa.backup_codes_encrypted)).decode('utf-8'))
        
        # Verify code
        is_valid, index = self.totp.verify_backup_code(code, hashed_codes)
        
        if is_valid and index is not None:
            # Remove used code
            hashed_codes.pop(index)
            mfa.backup_codes_encrypted = base64.b64encode(encrypt_data(json.dumps(hashed_codes))).decode('utf-8')
            mfa.last_used_at = datetime.utcnow()
            db.session.commit()
            return True
        
        return False
    
    def disable_mfa(self, user_id: int, mfa_type: str = 'totp') -> bool:
        """Disable MFA for a user."""
        from app.models import UserMFA
        from app.database import db
        
        mfa = UserMFA.query.filter_by(user_id=user_id, mfa_type=mfa_type).first()
        if mfa:
            db.session.delete(mfa)
            db.session.commit()
            return True
        return False
    
    def is_mfa_enabled(self, user_id: int) -> bool:
        """Check if user has MFA enabled."""
        from app.models import UserMFA
        
        return UserMFA.query.filter_by(
            user_id=user_id,
            is_enabled=True
        ).first() is not None
    
    def get_mfa_status(self, user_id: int) -> dict:
        """Get MFA status for a user."""
        from app.models import UserMFA
        
        mfa_records = UserMFA.query.filter_by(user_id=user_id).all()
        
        return {
            'has_mfa': any(m.is_enabled for m in mfa_records),
            'methods': [{
                'type': m.mfa_type,
                'enabled': m.is_enabled,
                'verified': m.is_verified,
                'verified_at': m.verified_at.isoformat() if m.verified_at else None,
                'last_used': m.last_used_at.isoformat() if m.last_used_at else None,
            } for m in mfa_records]
        }
    
    def create_challenge(self, user_id: int, challenge_type: str = 'totp',
                        expires_minutes: int = 10) -> int:
        """
        Create an MFA challenge for login flow.
        
        Returns:
            Challenge ID
        """
        from app.models import MFAChallenge
        from app.database import db
        from flask import request
        
        challenge = MFAChallenge(
            user_id=user_id,
            challenge_type=challenge_type,
            expires_at=datetime.utcnow() + timedelta(minutes=expires_minutes),
            ip_address=request.remote_addr if request else None,
        )
        db.session.add(challenge)
        db.session.commit()
        
        return challenge.id
    
    def verify_challenge(self, challenge_id: int, token: str) -> Tuple[bool, Optional[int]]:
        """
        Verify an MFA challenge.
        
        Returns:
            Tuple of (success, user_id)
        """
        from app.models import MFAChallenge
        from app.database import db
        
        challenge = MFAChallenge.query.get(challenge_id)
        if not challenge or not challenge.is_valid():
            return False, None
        
        # Increment attempt counter
        challenge.attempts += 1
        db.session.commit()
        
        # Try TOTP verification
        if self.verify_token(challenge.user_id, token, challenge.challenge_type):
            challenge.verified_at = datetime.utcnow()
            db.session.commit()
            return True, challenge.user_id
        
        # Try backup code
        if self.verify_backup_code(challenge.user_id, token, challenge.challenge_type):
            challenge.verified_at = datetime.utcnow()
            db.session.commit()
            return True, challenge.user_id
        
        return False, None


# Global instances
totp_manager = TOTPManager()
mfa_service = MFAService()
