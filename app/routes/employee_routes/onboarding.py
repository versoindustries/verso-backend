"""
Phase 22: Onboarding Routes
User onboarding wizard with profile completion, preferences, and feature tour
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import OnboardingStep, UserPreference, UserActivity
from app.forms import OnboardingProfileForm, OnboardingPreferencesForm

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')


def get_or_create_step(user_id, step_name):
    """Get or create an onboarding step for a user."""
    step = OnboardingStep.query.filter_by(user_id=user_id, step_name=step_name).first()
    if not step:
        step = OnboardingStep(user_id=user_id, step_name=step_name)
        db.session.add(step)
        db.session.commit()
    return step


def get_onboarding_progress(user_id):
    """Calculate onboarding progress percentage."""
    steps = ['welcome', 'profile', 'preferences', 'tour']
    completed = OnboardingStep.query.filter_by(user_id=user_id, completed=True).count()
    return {
        'completed': completed,
        'total': len(steps),
        'percentage': int((completed / len(steps)) * 100)
    }


@onboarding_bp.route('/welcome')
@login_required
def welcome():
    """Welcome step - introduction to the platform."""
    if current_user.onboarding_completed:
        return redirect(url_for('user.dashboard'))
    
    # Mark welcome step as started
    step = get_or_create_step(current_user.id, 'welcome')
    progress = get_onboarding_progress(current_user.id)
    
    return render_template(
        'onboarding/welcome.html',
        step=step,
        progress=progress,
        hide_estimate_form=True
    )


@onboarding_bp.route('/welcome/complete', methods=['POST'])
@login_required
def complete_welcome():
    """Mark welcome step as complete and proceed to profile."""
    from datetime import datetime
    step = get_or_create_step(current_user.id, 'welcome')
    step.completed = True
    step.completed_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('onboarding.profile'))


@onboarding_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Profile completion step."""
    if current_user.onboarding_completed:
        return redirect(url_for('user.dashboard'))
    
    form = OnboardingProfileForm()
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.first_name.data = current_user.first_name or ''
        form.last_name.data = current_user.last_name or ''
        form.phone.data = current_user.phone or ''
        form.timezone.data = current_user.timezone or ''
        form.bio.data = current_user.bio or ''
    
    if form.validate_on_submit():
        from datetime import datetime
        
        # Update user profile
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data or None
        current_user.timezone = form.timezone.data or None
        current_user.bio = form.bio.data or None
        
        # Mark step complete
        step = get_or_create_step(current_user.id, 'profile')
        step.completed = True
        step.completed_at = datetime.utcnow()
        step.data = {
            'fields_completed': [f for f in ['first_name', 'last_name', 'phone', 'timezone', 'bio'] 
                                 if getattr(form, f).data]
        }
        
        # Update profile completion score
        current_user.calculate_profile_completion_score()
        
        # Log activity
        current_user.log_activity(
            activity_type='profile_updated',
            title='Completed profile setup',
            description='Profile information updated during onboarding',
            icon='fa-user-edit'
        )
        
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('onboarding.preferences'))
    
    progress = get_onboarding_progress(current_user.id)
    return render_template(
        'onboarding/profile.html',
        form=form,
        progress=progress,
        hide_estimate_form=True
    )


@onboarding_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Notification preferences step."""
    if current_user.onboarding_completed:
        return redirect(url_for('user.dashboard'))
    
    form = OnboardingPreferencesForm()
    
    # Get or create user preferences
    user_prefs = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not user_prefs:
        user_prefs = UserPreference(user_id=current_user.id)
        db.session.add(user_prefs)
        db.session.commit()
    
    # Pre-populate form
    if request.method == 'GET':
        form.email_marketing.data = user_prefs.email_marketing
        form.email_order_updates.data = user_prefs.email_order_updates
        form.email_appointment_reminders.data = user_prefs.email_appointment_reminders
        form.email_newsletter.data = user_prefs.email_newsletter
    
    if form.validate_on_submit():
        from datetime import datetime
        
        # Update preferences
        user_prefs.email_marketing = form.email_marketing.data
        user_prefs.email_order_updates = form.email_order_updates.data
        user_prefs.email_appointment_reminders = form.email_appointment_reminders.data
        user_prefs.email_newsletter = form.email_newsletter.data
        
        # Mark step complete
        step = get_or_create_step(current_user.id, 'preferences')
        step.completed = True
        step.completed_at = datetime.utcnow()
        
        db.session.commit()
        flash('Preferences saved!', 'success')
        return redirect(url_for('onboarding.complete'))
    
    progress = get_onboarding_progress(current_user.id)
    return render_template(
        'onboarding/preferences.html',
        form=form,
        progress=progress,
        hide_estimate_form=True
    )


@onboarding_bp.route('/complete', methods=['GET', 'POST'])
@login_required
def complete():
    """Final step - mark onboarding complete and redirect to dashboard with tour."""
    from datetime import datetime
    
    # Mark tour step as complete (will be shown on dashboard)
    step = get_or_create_step(current_user.id, 'tour')
    step.completed = True
    step.completed_at = datetime.utcnow()
    
    # Mark overall onboarding complete
    current_user.onboarding_completed = True
    current_user.onboarding_completed_at = datetime.utcnow()
    
    # Update profile completion score
    current_user.calculate_profile_completion_score()
    
    # Log activity
    current_user.log_activity(
        activity_type='onboarding_completed',
        title='Completed onboarding',
        description='Successfully completed the onboarding wizard',
        icon='fa-check-circle'
    )
    
    db.session.commit()
    
    flash('Welcome! Your account is all set up.', 'success')
    
    # Redirect to dashboard with tour flag
    return redirect(url_for('user.dashboard', tour='1'))


@onboarding_bp.route('/skip', methods=['POST'])
@login_required
def skip():
    """Skip remaining onboarding steps."""
    from datetime import datetime
    
    current_user.onboarding_completed = True
    current_user.onboarding_completed_at = datetime.utcnow()
    db.session.commit()
    
    flash('You can complete your profile later in Settings.', 'info')
    return redirect(url_for('user.dashboard'))


@onboarding_bp.route('/status')
@login_required
def status():
    """Get onboarding status as JSON (for AJAX)."""
    progress = get_onboarding_progress(current_user.id)
    steps = OnboardingStep.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'onboarding_completed': current_user.onboarding_completed,
        'progress': progress,
        'steps': {s.step_name: {'completed': s.completed, 'completed_at': s.completed_at.isoformat() if s.completed_at else None} for s in steps},
        'profile_completion_score': current_user.profile_completion_score
    })
