"""
Phase 6: Enhanced Messaging routes.

Provides channel-based messaging with:
- Direct messages (1:1 channels)
- Private channels with member management
- Channel archiving
- @mentions with notifications
- Message reactions
- Read receipts
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import (
    Channel, Message, User, Media, ChannelMember, 
    MessageReaction
)
from app.database import db
from datetime import datetime
import re
from markupsafe import Markup, escape

messaging_bp = Blueprint('messaging', __name__, url_prefix='/messaging')


# ============================================================================
# Helper Functions
# ============================================================================

def render_message_content(message):
    """Escape user content and wrap @mentions in spans."""
    content = escape(message.content or '')
    for mention in message.get_mentions():
        mention_text = f'@{mention}'
        content = content.replace(
            mention_text,
            Markup(f'<span class="mention">@{escape(mention)}</span>')
        )
    return Markup(content)


def user_can_access_channel(channel):
    """Return True if current_user can access the channel."""
    if channel.type in ('private', 'direct') and current_user not in channel.members:
        return False
    return True


def get_or_create_dm_channel(user1_id, user2_id):
    """Get or create a direct message channel between two users."""
    # Sort IDs to ensure consistent channel lookup
    ids = sorted([user1_id, user2_id])
    
    # Check for existing DM channel
    for channel in Channel.query.filter_by(is_direct=True, type='direct').all():
        member_ids = [m.id for m in channel.members]
        if sorted(member_ids) == ids:
            return channel
    
    # Create new DM channel
    user1 = User.query.get(user1_id)
    user2 = User.query.get(user2_id)
    
    channel = Channel(
        name=f"DM: {user1.username} & {user2.username}",
        type='direct',
        is_direct=True,
        created_by_id=user1_id
    )
    channel.members.append(user1)
    channel.members.append(user2)
    db.session.add(channel)
    db.session.commit()
    
    # Create membership records for read tracking
    for user_id in ids:
        membership = ChannelMember(channel_id=channel.id, user_id=user_id)
        db.session.add(membership)
    db.session.commit()
    
    return channel


def process_mentions(message):
    """
    Parse @mentions in message content and create notifications.
    Returns list of mentioned user IDs.
    """
    mentions = message.get_mentions()
    mentioned_user_ids = []
    
    for username in mentions:
        user = User.query.filter_by(username=username).first()
        if user and user.id != message.user_id:  # Don't notify self
            mentioned_user_ids.append(user.id)
            
            # Create notification
            from app.routes.notifications import create_notification
            create_notification(
                user_id=user.id,
                notification_type='mention',
                title=f"@{message.user.username} mentioned you",
                body=(message.content or '')[:100] + ('...' if len(message.content or '') > 100 else ''),
                link=url_for('messaging.channel', channel_id=message.channel_id),
                related_type='message',
                related_id=message.id
            )
    
    return mentioned_user_ids


def notify_channel_members(message, exclude_user_id=None):
    """
    Notify all channel members about a new message.
    """
    from app.routes.notifications import create_notification
    
    channel = message.channel
    
    # Get all members (for DMs/private) or skip for public channels
    if channel.is_direct or channel.type == 'private':
        for member in channel.members:
            if member.id != exclude_user_id:
                # Check if user has muted this channel
                membership = ChannelMember.query.filter_by(
                    channel_id=channel.id,
                    user_id=member.id
                ).first()
                
                if membership and membership.is_muted:
                    continue
                
                preview = (message.content or '')[:80]
                if message.content and len(message.content) > 80:
                    preview += '...'
                
                create_notification(
                    user_id=member.id,
                    notification_type='message',
                    title=f"New message in {channel.get_display_name(member)}",
                    body=f"{message.user.username}: {preview}",
                    link=url_for('messaging.channel', channel_id=channel.id),
                    related_type='channel',
                    related_id=channel.id
                )


def update_read_receipt(channel_id, user_id, message_id=None):
    """Update read receipt for a user in a channel."""
    membership = ChannelMember.query.filter_by(
        channel_id=channel_id,
        user_id=user_id
    ).first()
    
    if not membership:
        # Create membership record
        membership = ChannelMember(
            channel_id=channel_id,
            user_id=user_id
        )
        db.session.add(membership)
    
    if message_id:
        membership.last_read_message_id = message_id
    membership.last_read_at = datetime.utcnow()
    db.session.commit()


# ============================================================================
# Main Routes
# ============================================================================

@messaging_bp.route('/')
@login_required
def index():
    """List all channels accessible to the user."""
    show_archived = request.args.get('archived', '0') == '1'
    
    # Get public and private channels
    if show_archived:
        public_channels = Channel.query.filter(
            Channel.type == 'public'
        ).order_by(Channel.name).all()
    else:
        public_channels = Channel.query.filter(
            Channel.type == 'public',
            Channel.is_archived == False
        ).order_by(Channel.name).all()
    
    # Get user's private channels
    private_channels = Channel.query.filter(
        Channel.type == 'private',
        Channel.members.any(id=current_user.id)
    ).all()
    if not show_archived:
        private_channels = [c for c in private_channels if not c.is_archived]
    
    # Get user's DM channels
    dm_channels = Channel.query.filter(
        Channel.is_direct == True,
        Channel.members.any(id=current_user.id)
    ).all()
    
    # Get all users for DM creation
    users = User.query.filter(User.id != current_user.id).order_by(User.username).all()
    
    return render_template('messaging/index.html', 
                         public_channels=public_channels,
                         private_channels=private_channels,
                         dm_channels=dm_channels,
                         users=users,
                         show_archived=show_archived)


@messaging_bp.route('/create_channel', methods=['POST'])
@login_required
def create_channel():
    """Create a new channel."""
    name = request.form.get('name')
    channel_type = request.form.get('type', 'public')
    description = request.form.get('description', '')
    
    if not name:
        flash('Channel name is required.', 'error')
        return redirect(url_for('messaging.index'))
    
    channel = Channel(
        name=name, 
        type=channel_type,
        description=description,
        created_by_id=current_user.id
    )
    
    # For private channels, add creator as a member
    if channel_type == 'private':
        channel.members.append(current_user)
    
    db.session.add(channel)
    db.session.commit()
    
    # Create membership record
    if channel_type == 'private':
        membership = ChannelMember(channel_id=channel.id, user_id=current_user.id)
        db.session.add(membership)
        db.session.commit()
    
    flash('Channel created successfully.', 'success')
    return redirect(url_for('messaging.channel', channel_id=channel.id))


@messaging_bp.route('/dm/<int:user_id>')
@login_required
def direct_message(user_id):
    """Get or create a DM channel with another user."""
    if user_id == current_user.id:
        flash("You can't message yourself.", 'error')
        return redirect(url_for('messaging.index'))
    
    other_user = User.query.get_or_404(user_id)
    channel = get_or_create_dm_channel(current_user.id, user_id)
    
    return redirect(url_for('messaging.channel', channel_id=channel.id))


@messaging_bp.route('/channel/<int:channel_id>')
@login_required
def channel(channel_id):
    """View a channel and its messages."""
    channel = Channel.query.get_or_404(channel_id)
    
    # Check access for private/DM channels
    if not user_can_access_channel(channel):
        flash("You don't have access to this channel.", 'error')
        return redirect(url_for('messaging.index'))
    
    messages = Message.query.filter_by(channel_id=channel_id)\
        .order_by(Message.created_at.asc()).all()
    for msg in messages:
        msg.rendered_content = render_message_content(msg)
    
    # Update read receipt
    last_message = messages[-1] if messages else None
    if last_message:
        update_read_receipt(channel_id, current_user.id, last_message.id)
    else:
        # Ensure membership exists even if no messages yet
        update_read_receipt(channel_id, current_user.id)
    
    # Get read receipts for display
    read_receipts = {}
    memberships = ChannelMember.query.filter_by(channel_id=channel_id).all()
    for m in memberships:
        if m.last_read_message_id:
            read_receipts[m.user_id] = m.last_read_message_id
    seen_users = []
    if messages:
        last_id = messages[-1].id
        seen_users = [
            m.user for m in memberships 
            if m.user_id != current_user.id and m.last_read_message_id and m.last_read_message_id >= last_id
        ]
    
    membership = ChannelMember.query.filter_by(
        channel_id=channel_id,
        user_id=current_user.id
    ).first()
    is_muted = membership.is_muted if membership else False
    
    # Load channel lists for sidebar
    public_channels = Channel.query.filter(
        Channel.type == 'public',
        Channel.is_archived == False
    ).order_by(Channel.name).all()
    private_channels = Channel.query.filter(
        Channel.type == 'private',
        Channel.members.any(id=current_user.id)
    ).order_by(Channel.name).all()
    dm_channels = Channel.query.filter(
        Channel.is_direct == True,
        Channel.members.any(id=current_user.id)
    ).all()
    
    # Serialize data for React component
    import json
    
    channel_json = json.dumps({
        'id': channel.id,
        'name': channel.name,
        'type': channel.type,
        'is_archived': channel.is_archived,
        'is_direct': channel.is_direct,
        'display_name': channel.get_display_name(current_user)
    })
    
    def serialize_message(msg):
        attachment_info = None
        if msg.attachment_id and msg.attachment:
            attachment_info = {
                'url': url_for('media.serve_media', media_id=msg.attachment_id),
                'name': msg.attachment.filename,
                'is_image': msg.attachment.mimetype.startswith('image/') if msg.attachment.mimetype else False
            }
        
        # Get reactions
        reactions = {}
        for reaction in msg.reactions:
            if reaction.emoji not in reactions:
                reactions[reaction.emoji] = {'count': 0, 'user_reacted': False}
            reactions[reaction.emoji]['count'] += 1
            if reaction.user_id == current_user.id:
                reactions[reaction.emoji]['user_reacted'] = True
        
        return {
            'id': msg.id,
            'user': msg.user.username,
            'user_id': msg.user_id,
            'content': str(render_message_content(msg)),
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'attachment': attachment_info,
            'reactions': reactions
        }
    
    messages_json = json.dumps([serialize_message(msg) for msg in messages])
    
    seen_users_json = json.dumps([
        {'id': u.id, 'username': u.username}
        for u in seen_users
    ])
    
    return render_template(
        'messaging/channel.html', 
        current_channel=channel,
        channel_json=channel_json,
        messages_json=messages_json,
        seen_users_json=seen_users_json,
        channels=public_channels,
        dm_channels=dm_channels,
        private_channels=private_channels,
        messages=messages,
        read_receipts=read_receipts,
        seen_users=seen_users,
        is_muted=is_muted
    )


@messaging_bp.route('/channel/<int:channel_id>/send', methods=['POST'])
@login_required
def send_message(channel_id):
    """Send a message to a channel."""
    channel = Channel.query.get_or_404(channel_id)
    
    # Check access
    if channel.type in ('private', 'direct') and current_user not in channel.members:
        flash("You don't have access to this channel.", 'error')
        return redirect(url_for('messaging.index'))
    if channel.is_archived:
        flash('This channel is archived and read-only.', 'error')
        return redirect(url_for('messaging.channel', channel_id=channel_id))
    
    content = request.form.get('content', '').strip()
    file = request.files.get('file')
    
    if not content and not (file and file.filename):
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('messaging.channel', channel_id=channel_id))
    
    attachment_id = None
    if file and file.filename:
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        data = file.read()
        media = Media(
            filename=filename, 
            mimetype=file.mimetype, 
            data=data, 
            size=len(data), 
            uploaded_by_id=current_user.id
        )
        db.session.add(media)
        db.session.flush()
        attachment_id = media.id
    
    message = Message(
        channel_id=channel_id, 
        user_id=current_user.id, 
        content=content,
        attachment_id=attachment_id
    )
    db.session.add(message)
    db.session.commit()
    
    # Process @mentions
    process_mentions(message)
    
    # Notify channel members (for DMs and private channels)
    notify_channel_members(message, exclude_user_id=current_user.id)
    
    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message_id': message.id})
    
    return redirect(url_for('messaging.channel', channel_id=channel_id))


@messaging_bp.route('/channel/<int:channel_id>/poll')
@login_required
def poll_messages(channel_id):
    """Poll for new messages (AJAX endpoint)."""
    channel = Channel.query.get_or_404(channel_id)
    if not user_can_access_channel(channel):
        return jsonify({'error': 'Access denied'}), 403
    
    last_id = request.args.get('last_id', 0, type=int)
    
    messages = Message.query.filter(
        Message.channel_id == channel_id, 
        Message.id > last_id
    ).order_by(Message.created_at.asc()).all()
    
    # Update read receipt
    if messages:
        update_read_receipt(channel_id, current_user.id, messages[-1].id)
    
    results = []
    for msg in messages:
        attachment_info = None
        if msg.attachment_id and msg.attachment:
            attachment_info = {
                'url': url_for('media.serve_media', media_id=msg.attachment_id),
                'name': msg.attachment.filename,
                'is_image': msg.attachment.mimetype.startswith('image/') if msg.attachment.mimetype else False
            }
        
        # Get reactions
        reactions = {}
        for reaction in msg.reactions:
            if reaction.emoji not in reactions:
                reactions[reaction.emoji] = {'count': 0, 'users': [], 'user_reacted': False}
            reactions[reaction.emoji]['count'] += 1
            reactions[reaction.emoji]['users'].append(reaction.user.username)
            if reaction.user_id == current_user.id:
                reactions[reaction.emoji]['user_reacted'] = True
        
        results.append({
            'id': msg.id,
            'user': msg.user.username,
            'user_id': msg.user_id,
            'content': str(render_message_content(msg)),
            'raw_content': msg.content,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_me': msg.user_id == current_user.id,
            'attachment': attachment_info,
            'reactions': reactions
        })
    
    return jsonify(results)


# ============================================================================
# Channel Management Routes
# ============================================================================

@messaging_bp.route('/channel/<int:channel_id>/archive', methods=['POST'])
@login_required
def archive_channel(channel_id):
    """Archive a channel."""
    channel = Channel.query.get_or_404(channel_id)
    
    # Only creator or admin can archive
    if channel.created_by_id != current_user.id and not current_user.has_role('admin'):
        flash("You don't have permission to archive this channel.", 'error')
        return redirect(url_for('messaging.channel', channel_id=channel_id))
    
    channel.is_archived = True
    db.session.commit()
    
    flash(f'Channel "{channel.name}" has been archived.', 'success')
    return redirect(url_for('messaging.index'))


@messaging_bp.route('/channel/<int:channel_id>/unarchive', methods=['POST'])
@login_required
def unarchive_channel(channel_id):
    """Unarchive a channel."""
    channel = Channel.query.get_or_404(channel_id)
    
    if channel.created_by_id != current_user.id and not current_user.has_role('admin'):
        flash("You don't have permission to unarchive this channel.", 'error')
        return redirect(url_for('messaging.index'))
    
    channel.is_archived = False
    db.session.commit()
    
    flash(f'Channel "{channel.name}" has been unarchived.', 'success')
    return redirect(url_for('messaging.channel', channel_id=channel_id))


@messaging_bp.route('/channel/<int:channel_id>/members', methods=['GET', 'POST'])
@login_required
def manage_members(channel_id):
    """Manage members of a private channel."""
    channel = Channel.query.get_or_404(channel_id)
    
    if channel.type != 'private':
        flash("Only private channels have member management.", 'error')
        return redirect(url_for('messaging.channel', channel_id=channel_id))
    
    if channel.created_by_id != current_user.id and not current_user.has_role('admin'):
        flash("You don't have permission to manage members.", 'error')
        return redirect(url_for('messaging.channel', channel_id=channel_id))
    
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id', type=int)
        
        if action == 'add' and user_id:
            user = User.query.get(user_id)
            if user and user not in channel.members:
                channel.members.append(user)
                membership = ChannelMember(channel_id=channel.id, user_id=user.id)
                db.session.add(membership)
                db.session.commit()
                flash(f'{user.username} added to channel.', 'success')
        
        elif action == 'remove' and user_id:
            user = User.query.get(user_id)
            if user and user in channel.members and user.id != channel.created_by_id:
                channel.members.remove(user)
                ChannelMember.query.filter_by(
                    channel_id=channel.id, 
                    user_id=user.id
                ).delete()
                db.session.commit()
                flash(f'{user.username} removed from channel.', 'success')
        
        return redirect(url_for('messaging.manage_members', channel_id=channel_id))
    
    # Get available users to add
    current_member_ids = [m.id for m in channel.members]
    available_users = User.query.filter(
        ~User.id.in_(current_member_ids)
    ).order_by(User.username).all()
    
    return render_template('messaging/members.html',
                         channel=channel,
                         available_users=available_users)


@messaging_bp.route('/channel/<int:channel_id>/mute', methods=['POST'])
@login_required
def toggle_mute(channel_id):
    """Toggle mute status for channel notifications."""
    channel = Channel.query.get_or_404(channel_id)
    if not user_can_access_channel(channel):
        flash("You don't have access to this channel.", 'error')
        return redirect(url_for('messaging.index'))
    
    membership = ChannelMember.query.filter_by(
        channel_id=channel_id,
        user_id=current_user.id
    ).first()
    
    if not membership:
        membership = ChannelMember(
            channel_id=channel_id,
            user_id=current_user.id,
            is_muted=True
        )
        db.session.add(membership)
    else:
        membership.is_muted = not membership.is_muted
    
    db.session.commit()
    
    status = 'muted' if membership.is_muted else 'unmuted'
    flash(f'Channel {status}.', 'success')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'muted': membership.is_muted})
    
    return redirect(url_for('messaging.channel', channel_id=channel_id))


# ============================================================================
# Reaction Routes
# ============================================================================

@messaging_bp.route('/message/<int:message_id>/react', methods=['POST'])
@login_required
def add_reaction(message_id):
    """Add a reaction to a message."""
    message = Message.query.get_or_404(message_id)
    if not user_can_access_channel(message.channel):
        return jsonify({'error': 'Access denied'}), 403
    emoji = request.form.get('emoji') or request.json.get('emoji')
    
    if not emoji:
        return jsonify({'error': 'Emoji required'}), 400
    
    # Check if reaction already exists
    existing = MessageReaction.query.filter_by(
        message_id=message_id,
        user_id=current_user.id,
        emoji=emoji
    ).first()
    
    if existing:
        # Remove reaction (toggle)
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed'})
    
    # Add reaction
    reaction = MessageReaction(
        message_id=message_id,
        user_id=current_user.id,
        emoji=emoji
    )
    db.session.add(reaction)
    db.session.commit()
    
    return jsonify({'success': True, 'action': 'added'})


@messaging_bp.route('/message/<int:message_id>/reactions')
@login_required
def get_reactions(message_id):
    """Get all reactions for a message."""
    message = Message.query.get_or_404(message_id)
    if not user_can_access_channel(message.channel):
        return jsonify({'error': 'Access denied'}), 403
    
    reactions = {}
    for reaction in message.reactions:
        if reaction.emoji not in reactions:
            reactions[reaction.emoji] = {'count': 0, 'users': [], 'user_reacted': False}
        reactions[reaction.emoji]['count'] += 1
        reactions[reaction.emoji]['users'].append(reaction.user.username)
        if reaction.user_id == current_user.id:
            reactions[reaction.emoji]['user_reacted'] = True
    
    return jsonify(reactions)
