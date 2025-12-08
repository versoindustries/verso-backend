from cryptography.fernet import Fernet
from flask import current_app
import base64
import hashlib

def get_fernet_key():
    """Derive a valid Fernet key from the app's SECRET_KEY."""
    secret = current_app.config['SECRET_KEY']
    if not secret:
        raise ValueError("SECRET_KEY must be set in config")
    
    # Hash the secret to get 32 bytes
    digest = hashlib.sha256(secret.encode()).digest()
    
    # Base64 encode to make it url-safe for Fernet
    return base64.urlsafe_b64encode(digest)

def encrypt_data(data):
    """Encrypts bytes data."""
    if not isinstance(data, bytes):
        if isinstance(data, str):
            data = data.encode()
        else:
            raise TypeError("Data must be bytes or string")
            
    key = get_fernet_key()
    f = Fernet(key)
    return f.encrypt(data)

def decrypt_data(data):
    """Decrypts bytes data."""
    if not isinstance(data, bytes):
        raise TypeError("Data must be bytes")
        
    key = get_fernet_key()
    f = Fernet(key)
    return f.decrypt(data)
