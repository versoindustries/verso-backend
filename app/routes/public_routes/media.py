from flask import Blueprint, send_file, abort, Response
from app.models import Media
from io import BytesIO

media_bp = Blueprint('media', __name__)

@media_bp.route('/media/<int:media_id>')
def serve_media(media_id):
    media = Media.query.get_or_404(media_id)
    
    return send_file(
        BytesIO(media.data),
        mimetype=media.mimetype,
        as_attachment=False,
        download_name=media.filename,
        etag=media.checksum
    )
