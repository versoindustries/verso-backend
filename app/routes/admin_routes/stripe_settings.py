"""
Stripe Settings Admin Routes

Manage Stripe payment configuration for the admin.
"""
import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required
from app.modules.decorators import role_required

stripe_settings_bp = Blueprint('stripe_settings', __name__, url_prefix='/admin')


@stripe_settings_bp.route('/stripe-settings')
@login_required
@role_required('Admin')
def stripe_settings():
    """Display Stripe settings page."""
    # Get current config values (masked for display)
    stripe_publishable = current_app.config.get('STRIPE_PUBLISHABLE_KEY', '')
    stripe_secret = current_app.config.get('STRIPE_SECRET_KEY', '')
    stripe_webhook = current_app.config.get('STRIPE_WEBHOOK_SECRET', '')
    
    # Mask keys for display
    def mask_key(key):
        if not key:
            return 'Not configured'
        if len(key) < 12:
            return '***'
        return key[:8] + '...' + key[-4:]
    
    settings = {
        'publishable_key': mask_key(stripe_publishable),
        'secret_key': mask_key(stripe_secret),
        'webhook_secret': mask_key(stripe_webhook),
        'is_configured': bool(stripe_publishable and stripe_secret),
        'is_test_mode': stripe_publishable.startswith('pk_test') if stripe_publishable else True
    }
    
    return render_template('admin/stripe_settings.html', settings=settings)


@stripe_settings_bp.route('/api/stripe-settings/test', methods=['POST'])
@login_required
@role_required('Admin')
def test_stripe_connection():
    """Test Stripe API connection."""
    try:
        import stripe
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        
        if not stripe.api_key:
            return jsonify({'success': False, 'error': 'Stripe secret key not configured'})
        
        # Test the connection by fetching account info
        account = stripe.Account.retrieve()
        
        return jsonify({
            'success': True,
            'account_id': account.id,
            'business_name': account.get('business_profile', {}).get('name', 'Unknown'),
            'country': account.country,
            'default_currency': account.default_currency
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
