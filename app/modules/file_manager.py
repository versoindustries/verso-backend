"""
File Manager Module

Handles file uploads, storage, and image processing.
"""

import hashlib
from io import BytesIO
from app.models import Media
from app.database import db
from werkzeug.utils import secure_filename

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'txt', 'md', 'doc', 'docx', 'xls', 'xlsx'}
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Auto-compress images larger than this (1MB)
AUTO_COMPRESS_THRESHOLD = 1024 * 1024


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_image(filename):
    """Check if file is an image based on extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS


def compress_image(data, quality=85, max_dimension=2048):
    """
    Compress an image using Pillow.
    
    Args:
        data: Raw image bytes
        quality: JPEG quality (1-100)
        max_dimension: Max width/height, larger images are resized
    
    Returns:
        Compressed image bytes
    """
    try:
        from PIL import Image
        
        img = Image.open(BytesIO(data))
        
        # Convert RGBA to RGB for JPEG
        if img.mode in ('RGBA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background
        
        # Resize if too large
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save compressed
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
        
    except ImportError:
        # Pillow not installed, return original
        return data
    except Exception:
        # Any error, return original
        return data


def save_media(file_storage, user_id=None, compress=True):
    """
    Saves a FileStorage object to the database.
    
    Args:
        file_storage: Werkzeug FileStorage object
        user_id: Optional user ID for tracking
        compress: Auto-compress large images
    
    Returns:
        Created Media object or None if invalid
    """
    if not file_storage or not allowed_file(file_storage.filename):
        return None

    filename = secure_filename(file_storage.filename)
    data = file_storage.read()
    size = len(data)
    mimetype = file_storage.mimetype
    
    # Auto-compress large images
    if compress and is_image(filename) and size > AUTO_COMPRESS_THRESHOLD:
        compressed_data = compress_image(data)
        if len(compressed_data) < size:
            data = compressed_data
            size = len(data)
            # Update mimetype for JPEG conversion
            if mimetype not in ('image/jpeg', 'image/jpg'):
                mimetype = 'image/jpeg'
                # Update filename extension
                name_parts = filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    filename = f"{name_parts[0]}.jpg"
    
    checksum = hashlib.sha256(data).hexdigest()

    media = Media(
        filename=filename,
        data=data,
        mimetype=mimetype,
        size=size,
        checksum=checksum,
        uploaded_by_id=user_id
    )
    
    db.session.add(media)
    db.session.commit()
    
    return media


def delete_media(media_id):
    """
    Delete a media item by ID.
    
    Returns:
        True if deleted, False if not found
    """
    media = Media.query.get(media_id)
    if media:
        db.session.delete(media)
        db.session.commit()
        return True
    return False


def get_media_by_checksum(checksum):
    """
    Find existing media by checksum (deduplication).
    
    Returns:
        Media object or None
    """
    return Media.query.filter_by(checksum=checksum).first()