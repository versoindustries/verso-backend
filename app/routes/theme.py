"""
Phase 7: Theme Editor Blueprint
Provides visual sovereignty through live theme editing with preview.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.modules.auth_manager import admin_required
from app.models import BusinessConfig, Media
from app.forms import CSRFTokenForm
from app.database import db
from app.modules.audit import log_audit_event
from werkzeug.utils import secure_filename
import os

theme_bp = Blueprint('theme', __name__, template_folder='templates')


@theme_bp.route('/admin/theme', methods=['GET', 'POST'])
@login_required
@admin_required
def theme_editor():
    """Theme editor with live preview."""
    form = CSRFTokenForm()
    
    # Load current theme settings
    configs = {c.setting_name: c.setting_value for c in BusinessConfig.query.all()}
    
    current_theme = {
        'primary_color': configs.get('primary_color', '#4169e1'),
        'secondary_color': configs.get('secondary_color', '#6c757d'),
        'accent_color': configs.get('accent_color', '#28a745'),
        'font_family': configs.get('font_family', 'Roboto, sans-serif'),
        'border_radius': configs.get('border_radius', '8'),
        'logo_media_id': configs.get('logo_media_id', ''),
        'ga4_tracking_id': configs.get('ga4_tracking_id', '')
    }
    
    # Get logo info if exists
    logo = None
    if current_theme['logo_media_id']:
        logo = Media.query.get(current_theme['logo_media_id'])
    
    if request.method == 'POST':
        try:
            # Update theme settings
            settings = {
                'primary_color': request.form.get('primary_color', '#4169e1'),
                'secondary_color': request.form.get('secondary_color', '#6c757d'),
                'accent_color': request.form.get('accent_color', '#28a745'),
                'font_family': request.form.get('font_family', 'Roboto, sans-serif'),
                'border_radius': request.form.get('border_radius', '8'),
                'ga4_tracking_id': request.form.get('ga4_tracking_id', '').strip()
            }
            
            for name, value in settings.items():
                config = BusinessConfig.query.filter_by(setting_name=name).first()
                if config:
                    config.setting_value = value
                else:
                    config = BusinessConfig(setting_name=name, setting_value=value)
                    db.session.add(config)
            
            db.session.commit()
            log_audit_event(current_user.id, 'update_theme', 'BusinessConfig', None, settings, request.remote_addr)
            flash('Theme updated successfully!', 'success')
            return redirect(url_for('theme.theme_editor'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Theme update error: {e}')
            flash('Error updating theme.', 'error')
    
    # Font choices
    font_choices = [
        ('Roboto, sans-serif', 'Roboto'),
        ('Open Sans, sans-serif', 'Open Sans'),
        ('Lato, sans-serif', 'Lato'),
        ('Montserrat, sans-serif', 'Montserrat'),
        ('Poppins, sans-serif', 'Poppins'),
        ('Inter, sans-serif', 'Inter'),
        ('Neon-Regular, sans-serif', 'Neon (Default)'),
        ('Arial, sans-serif', 'Arial'),
        ('Georgia, serif', 'Georgia'),
    ]
    
    # Convert font choices to JSON format for React component
    import json
    font_choices_json = json.dumps([{'value': v, 'label': l} for v, l in font_choices])
    
    return render_template(
        'admin/theme_editor.html',
        form=form,
        current_theme=current_theme,
        font_choices=font_choices,
        font_choices_json=font_choices_json,
        logo=logo
    )


@theme_bp.route('/admin/theme/logo', methods=['POST'])
@login_required
@admin_required
def upload_logo():
    """Handle logo upload."""
    if 'logo' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('theme.theme_editor'))
    
    file = request.files['logo']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('theme.theme_editor'))
    
    if file:
        try:
            filename = secure_filename(file.filename)
            
            # Store in Media model
            media = Media(
                filename=filename,
                content_type=file.content_type,
                data=file.read()
            )
            db.session.add(media)
            db.session.flush()  # Get the ID
            
            # Update BusinessConfig with logo_media_id
            config = BusinessConfig.query.filter_by(setting_name='logo_media_id').first()
            if config:
                config.setting_value = str(media.id)
            else:
                config = BusinessConfig(setting_name='logo_media_id', setting_value=str(media.id))
                db.session.add(config)
            
            db.session.commit()
            log_audit_event(current_user.id, 'upload_logo', 'Media', media.id, {'filename': filename}, request.remote_addr)
            flash('Logo uploaded successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Logo upload error: {e}')
            flash('Error uploading logo.', 'error')
    
    return redirect(url_for('theme.theme_editor'))


@theme_bp.route('/admin/theme/logo/remove', methods=['POST'])
@login_required
@admin_required
def remove_logo():
    """Remove custom logo."""
    config = BusinessConfig.query.filter_by(setting_name='logo_media_id').first()
    if config:
        config.setting_value = ''
        db.session.commit()
        log_audit_event(current_user.id, 'remove_logo', 'BusinessConfig', None, {}, request.remote_addr)
        flash('Logo removed.', 'success')
    return redirect(url_for('theme.theme_editor'))


@theme_bp.route('/admin/theme/preview')
@login_required
@admin_required  
def theme_preview():
    """Render preview page with temporary theme settings from query params."""
    # Get preview settings from query params
    preview_theme = {
        'primary_color': request.args.get('primary_color', '#4169e1'),
        'secondary_color': request.args.get('secondary_color', '#6c757d'),
        'accent_color': request.args.get('accent_color', '#28a745'),
        'font_family': request.args.get('font_family', 'Roboto, sans-serif'),
        'border_radius': request.args.get('border_radius', '8')
    }
    
    return render_template('admin/theme_preview.html', preview_theme=preview_theme)
