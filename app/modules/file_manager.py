import hashlib
from app.models import Media
from app.database import db
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'md'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_media(file_storage, user_id=None):
    """
    Saves a FileStorage object to the database.
    Returns the created Media object.
    """
    if not file_storage or not allowed_file(file_storage.filename):
        return None

    filename = secure_filename(file_storage.filename)
    data = file_storage.read()
    size = len(data)
    checksum = hashlib.sha256(data).hexdigest()
    mimetype = file_storage.mimetype

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