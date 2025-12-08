"""
Phase 15: Email Tracking Routes

Public endpoints for email tracking:
- Open tracking pixel
- Click tracking redirect
- Unsubscribe handling
- Email preference center
"""

from flask import Blueprint, request, redirect, render_template, flash, abort, make_response
from flask_login import login_required, current_user
from datetime import datetime
import base64
import hashlib

from app.database import db
from app.models import EmailSend, EmailClickTrack, EmailSuppressionList, User

email_tracking_bp = Blueprint('email_tracking', __name__, url_prefix='/t')


# 1x1 transparent GIF
TRACKING_PIXEL = base64.b64decode(
    'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
)


@email_tracking_bp.route('/o/<token>')
def track_open(token):
    """Track email open via tracking pixel.
    
    Returns a 1x1 transparent GIF.
    """
    try:
        email_send = EmailSend.query.filter_by(tracking_token=token).first()
        
        if email_send:
            email_send.record_open()
            db.session.commit()
    except Exception as e:
        # Don't let tracking errors affect user experience
        pass
    
    # Return 1x1 transparent GIF
    response = make_response(TRACKING_PIXEL)
    response.headers['Content-Type'] = 'image/gif'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response


@email_tracking_bp.route('/c/<token>/<int:idx>')
def track_click(token, idx):
    """Track email click and redirect to original URL.
    
    Args:
        token: Email send tracking token
        idx: Link index (for analytics)
    """
    # Get original URL from query param
    encoded_url = request.args.get('url', '')
    
    if not encoded_url:
        abort(400, "Missing URL parameter")
    
    try:
        original_url = base64.urlsafe_b64decode(encoded_url).decode()
    except Exception:
        abort(400, "Invalid URL encoding")
    
    try:
        email_send = EmailSend.query.filter_by(tracking_token=token).first()
        
        if email_send:
            email_send.record_click()
            
            # Record detailed click
            ip_hash = hashlib.sha256(
                request.remote_addr.encode('utf-8')
            ).hexdigest() if request.remote_addr else None
            
            click_track = EmailClickTrack(
                email_send_id=email_send.id,
                original_url=original_url,
                user_agent=request.user_agent.string[:500] if request.user_agent else None,
                ip_hash=ip_hash
            )
            db.session.add(click_track)
            db.session.commit()
    except Exception as e:
        # Don't let tracking errors affect user experience
        pass
    
    return redirect(original_url)


@email_tracking_bp.route('/u/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    """One-click unsubscribe from emails.
    
    GET: Show confirmation page
    POST: Process unsubscribe
    """
    email_send = EmailSend.query.filter_by(tracking_token=token).first()
    
    if not email_send:
        flash('Invalid unsubscribe link.', 'error')
        return redirect('/')
    
    email = email_send.recipient_email
    
    if request.method == 'POST':
        # Process unsubscribe
        email_send.unsubscribed = True
        email_send.unsubscribed_at = datetime.utcnow()
        
        # Add to suppression list
        existing = EmailSuppressionList.query.filter_by(email=email.lower()).first()
        if not existing:
            suppression = EmailSuppressionList(
                email=email.lower(),
                reason='unsubscribe',
                source=f'campaign_{email_send.campaign_id}' if email_send.campaign_id else 'transactional'
            )
            db.session.add(suppression)
        
        db.session.commit()
        
        flash('You have been unsubscribed successfully.', 'success')
        return render_template('email/unsubscribe_success.html', email=email)
    
    # GET - show confirmation page
    return render_template('email/unsubscribe_confirm.html', 
                          email=email, 
                          token=token,
                          campaign=email_send.campaign)


@email_tracking_bp.route('/preferences/<token>', methods=['GET', 'POST'])
def email_preferences(token):
    """Email preference center.
    
    Allows users to manage their email preferences.
    """
    email_send = EmailSend.query.filter_by(tracking_token=token).first()
    
    if not email_send:
        flash('Invalid link.', 'error')
        return redirect('/')
    
    user = email_send.recipient
    email = email_send.recipient_email
    
    # Check if on suppression list
    is_unsubscribed = EmailSuppressionList.query.filter_by(
        email=email.lower()
    ).first() is not None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'unsubscribe_all':
            # Full unsubscribe
            if not is_unsubscribed:
                suppression = EmailSuppressionList(
                    email=email.lower(),
                    reason='unsubscribe',
                    source='preference_center'
                )
                db.session.add(suppression)
                db.session.commit()
            
            flash('You have been unsubscribed from all marketing emails.', 'success')
            
        elif action == 'resubscribe':
            # Remove from suppression list
            EmailSuppressionList.query.filter_by(email=email.lower()).delete()
            db.session.commit()
            flash('You have been resubscribed to marketing emails.', 'success')
        
        # Refresh status
        is_unsubscribed = EmailSuppressionList.query.filter_by(
            email=email.lower()
        ).first() is not None
    
    return render_template('email/preferences.html',
                          email=email,
                          user=user,
                          token=token,
                          is_unsubscribed=is_unsubscribed)


# ============================================================================
# List-Unsubscribe Header Support (RFC 8058)
# ============================================================================

@email_tracking_bp.route('/list-unsubscribe/<token>', methods=['POST'])
def list_unsubscribe(token):
    """Handle List-Unsubscribe-Post header requests.
    
    This endpoint handles one-click unsubscribe from email clients
    that support RFC 8058.
    """
    email_send = EmailSend.query.filter_by(tracking_token=token).first()
    
    if not email_send:
        return '', 404
    
    email = email_send.recipient_email
    
    # Process unsubscribe
    email_send.unsubscribed = True
    email_send.unsubscribed_at = datetime.utcnow()
    
    # Add to suppression list
    existing = EmailSuppressionList.query.filter_by(email=email.lower()).first()
    if not existing:
        suppression = EmailSuppressionList(
            email=email.lower(),
            reason='unsubscribe',
            source='list_unsubscribe'
        )
        db.session.add(suppression)
    
    db.session.commit()
    
    return '', 200
