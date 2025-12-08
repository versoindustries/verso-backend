"""
Forms & Data Collection Platform - Admin Routes

Admin interface for managing:
- Dynamic forms (CRUD, submissions, exports)
- Surveys (NPS, CSAT, analytics)
- Product reviews (moderation queue)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import csv
import io
import json
import re

from app.database import db
from app.models import (
    FormDefinition, FormSubmission, FormIntegration,
    Survey, SurveyResponse,
    Review, ReviewVote, Product, User
)
from app.modules.decorators import role_required


forms_admin_bp = Blueprint('forms_admin', __name__, url_prefix='/admin')


# ============================================================================
# Form Management Routes
# ============================================================================

@forms_admin_bp.route('/forms')
@login_required
@role_required('admin')
def list_forms():
    """List all forms with submission counts."""
    forms = FormDefinition.query.order_by(FormDefinition.created_at.desc()).all()
    
    # Calculate stats
    for form in forms:
        form.new_submissions = form.submissions.filter_by(status='new').count()
    
    # Serialize forms for React AdminDataTable component
    forms_json = json.dumps([
        {
            'id': form.id,
            'name': f'<a href="{url_for("forms_admin.edit_form", form_id=form.id)}"><strong>{form.name}</strong></a>',
            'slug': f'<code>{form.slug}</code> <a href="{url_for("forms.view_form", slug=form.slug)}" target="_blank"><i class="bi bi-box-arrow-up-right"></i></a>',
            'fields_count': len(form.fields_schema) if form.fields_schema else 0,
            'submissions_count': form.submissions_count,
            'new_submissions': f'<span class="badge bg-danger">{form.new_submissions}</span>' if form.new_submissions > 0 else '<span class="text-muted">0</span>',
            'status': '<span class="badge bg-success">Active</span>' if form.is_active else '<span class="badge bg-secondary">Inactive</span>',
            'created_at': form.created_at.strftime('%Y-%m-%d') if form.created_at else '-',
            'actions': f'''
                <div class="btn-group btn-group-sm">
                    <a href="{url_for('forms_admin.list_submissions', form_id=form.id)}" class="btn btn-outline-primary" title="View Submissions"><i class="bi bi-inbox"></i></a>
                    <a href="{url_for('forms_admin.edit_form', form_id=form.id)}" class="btn btn-outline-secondary" title="Edit Form"><i class="bi bi-pencil"></i></a>
                </div>
            '''
        }
        for form in forms
    ])
    
    return render_template('admin/forms/index.html', forms=forms, forms_json=forms_json)


@forms_admin_bp.route('/forms/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_form():
    """Create a new form with the form builder."""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            
            # Generate slug from name
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            
            # Ensure unique slug
            base_slug = slug
            counter = 1
            while FormDefinition.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Parse fields schema from JSON
            fields_json = request.form.get('fields_schema', '[]')
            fields_schema = json.loads(fields_json)
            
            # Parse settings
            settings = {
                'submit_text': request.form.get('submit_text', 'Submit'),
                'success_message': request.form.get('success_message', 'Thank you for your submission!'),
                'redirect_url': request.form.get('redirect_url', ''),
                'honeypot': request.form.get('honeypot', 'true') == 'true',
                'rate_limit': int(request.form.get('rate_limit', 5)),
            }
            
            form = FormDefinition(
                name=name,
                slug=slug,
                description=description,
                fields_schema=fields_schema,
                settings=settings,
                is_active=request.form.get('is_active', 'true') == 'true',
                created_by_id=current_user.id
            )
            
            db.session.add(form)
            db.session.commit()
            
            flash(f'Form "{name}" created successfully!', 'success')
            return redirect(url_for('forms_admin.edit_form', form_id=form.id))
        
        except json.JSONDecodeError:
            flash('Invalid fields configuration.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating form: {str(e)}', 'error')
    
    return render_template('admin/forms/create.html')


@forms_admin_bp.route('/forms/<int:form_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_form(form_id):
    """Edit form structure and settings."""
    form = FormDefinition.query.get_or_404(form_id)
    
    if request.method == 'POST':
        try:
            form.name = request.form.get('name', form.name).strip()
            form.description = request.form.get('description', '').strip()
            
            # Parse fields schema
            fields_json = request.form.get('fields_schema', '[]')
            form.fields_schema = json.loads(fields_json)
            
            # Parse conditional logic
            logic_json = request.form.get('conditional_logic', '[]')
            form.conditional_logic = json.loads(logic_json)
            
            # Update settings
            form.settings = {
                'submit_text': request.form.get('submit_text', 'Submit'),
                'success_message': request.form.get('success_message', 'Thank you!'),
                'redirect_url': request.form.get('redirect_url', ''),
                'honeypot': request.form.get('honeypot', 'true') == 'true',
                'rate_limit': int(request.form.get('rate_limit', 5)),
            }
            
            form.is_active = request.form.get('is_active', 'false') == 'true'
            
            db.session.commit()
            flash('Form updated successfully!', 'success')
            
        except json.JSONDecodeError:
            flash('Invalid JSON configuration.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating form: {str(e)}', 'error')
    
    return render_template('admin/forms/edit.html', form=form)


@forms_admin_bp.route('/forms/<int:form_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_form(form_id):
    """Delete a form and all its submissions."""
    form = FormDefinition.query.get_or_404(form_id)
    form_name = form.name
    
    try:
        db.session.delete(form)
        db.session.commit()
        flash(f'Form "{form_name}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting form: {str(e)}', 'error')
    
    return redirect(url_for('forms_admin.list_forms'))


@forms_admin_bp.route('/forms/<int:form_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_form(form_id):
    """Toggle form active status."""
    form = FormDefinition.query.get_or_404(form_id)
    form.is_active = not form.is_active
    db.session.commit()
    
    status = 'activated' if form.is_active else 'deactivated'
    flash(f'Form "{form.name}" {status}.', 'success')
    
    return redirect(url_for('forms_admin.list_forms'))


# ============================================================================
# Form Submissions Routes
# ============================================================================

@forms_admin_bp.route('/forms/<int:form_id>/submissions')
@login_required
@role_required('admin')
def list_submissions(form_id):
    """View all submissions for a form."""
    form = FormDefinition.query.get_or_404(form_id)
    
    # Filtering
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = form.submissions
    
    if status:
        query = query.filter_by(status=status)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(FormSubmission.submitted_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(FormSubmission.submitted_at < to_date)
        except ValueError:
            pass
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    submissions = query.order_by(FormSubmission.submitted_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/forms/submissions.html',
                         form=form,
                         submissions=submissions,
                         status_filter=status,
                         search=search,
                         date_from=date_from,
                         date_to=date_to)


@forms_admin_bp.route('/forms/<int:form_id>/submissions/<int:submission_id>')
@login_required
@role_required('admin')
def view_submission(form_id, submission_id):
    """View a single submission."""
    form = FormDefinition.query.get_or_404(form_id)
    submission = FormSubmission.query.get_or_404(submission_id)
    
    if submission.form_id != form_id:
        flash('Submission not found.', 'error')
        return redirect(url_for('forms_admin.list_submissions', form_id=form_id))
    
    # Mark as read
    if submission.status == 'new':
        submission.status = 'read'
        db.session.commit()
    
    # Build field display data
    field_data = []
    for field_def in (form.fields_schema or []):
        if field_def.get('type') in ('heading', 'paragraph'):
            continue
        field_name = field_def.get('name')
        field_data.append({
            'label': field_def.get('label', field_name),
            'name': field_name,
            'type': field_def.get('type'),
            'value': submission.data.get(field_name),
        })
    
    return render_template('admin/forms/submission_detail.html',
                         form=form,
                         submission=submission,
                         field_data=field_data)


@forms_admin_bp.route('/forms/<int:form_id>/submissions/<int:submission_id>/update-status', methods=['POST'])
@login_required
@role_required('admin')
def update_submission_status(form_id, submission_id):
    """Update submission status."""
    submission = FormSubmission.query.get_or_404(submission_id)
    
    if submission.form_id != form_id:
        return jsonify({'error': 'Invalid submission'}), 400
    
    new_status = request.form.get('status')
    if new_status in ('new', 'read', 'processed', 'archived'):
        submission.status = new_status
        db.session.commit()
        flash(f'Submission marked as {new_status}.', 'success')
    
    return redirect(url_for('forms_admin.view_submission', form_id=form_id, submission_id=submission_id))


@forms_admin_bp.route('/forms/<int:form_id>/submissions/<int:submission_id>/notes', methods=['POST'])
@login_required
@role_required('admin')
def update_submission_notes(form_id, submission_id):
    """Update submission admin notes."""
    submission = FormSubmission.query.get_or_404(submission_id)
    
    if submission.form_id != form_id:
        return jsonify({'error': 'Invalid submission'}), 400
    
    submission.notes = request.form.get('notes', '')
    db.session.commit()
    flash('Notes updated.', 'success')
    
    return redirect(url_for('forms_admin.view_submission', form_id=form_id, submission_id=submission_id))


@forms_admin_bp.route('/forms/<int:form_id>/submissions/<int:submission_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_submission(form_id, submission_id):
    """Delete a submission."""
    submission = FormSubmission.query.get_or_404(submission_id)
    
    if submission.form_id != form_id:
        flash('Invalid submission.', 'error')
        return redirect(url_for('forms_admin.list_submissions', form_id=form_id))
    
    db.session.delete(submission)
    db.session.commit()
    flash('Submission deleted.', 'success')
    
    return redirect(url_for('forms_admin.list_submissions', form_id=form_id))


@forms_admin_bp.route('/forms/<int:form_id>/export')
@login_required
@role_required('admin')
def export_submissions(form_id):
    """Export form submissions as CSV."""
    form = FormDefinition.query.get_or_404(form_id)
    
    # Get all submissions
    submissions = form.submissions.order_by(FormSubmission.submitted_at.desc()).all()
    
    # Build CSV
    output = io.StringIO()
    
    # Get field names from schema
    field_names = []
    field_labels = {}
    for field_def in (form.fields_schema or []):
        if field_def.get('type') in ('heading', 'paragraph'):
            continue
        name = field_def.get('name')
        field_names.append(name)
        field_labels[name] = field_def.get('label', name)
    
    # Header row
    headers = ['Submission ID', 'Submitted At', 'Status', 'IP Address']
    headers.extend(field_labels.get(f, f) for f in field_names)
    
    writer = csv.writer(output)
    writer.writerow(headers)
    
    # Data rows
    for sub in submissions:
        row = [
            sub.id,
            sub.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if sub.submitted_at else '',
            sub.status,
            sub.ip_address or '',
        ]
        for field_name in field_names:
            value = sub.data.get(field_name, '')
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            row.append(value)
        writer.writerow(row)
    
    # Generate response
    output.seek(0)
    filename = f'{form.slug}_submissions_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# ============================================================================
# Form Integrations Routes
# ============================================================================

@forms_admin_bp.route('/forms/<int:form_id>/integrations')
@login_required
@role_required('admin')
def list_integrations(form_id):
    """List integrations for a form."""
    form = FormDefinition.query.get_or_404(form_id)
    integrations = form.integrations.all()
    
    return render_template('admin/forms/integrations.html',
                         form=form,
                         integrations=integrations)


@forms_admin_bp.route('/forms/<int:form_id>/integrations/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_integration(form_id):
    """Create a new integration for a form."""
    form = FormDefinition.query.get_or_404(form_id)
    
    if request.method == 'POST':
        try:
            integration_type = request.form.get('integration_type')
            name = request.form.get('name', '').strip()
            
            # Build config based on type
            config = {}
            if integration_type == 'webhook':
                config = {
                    'url': request.form.get('webhook_url', ''),
                    'method': request.form.get('webhook_method', 'POST'),
                    'headers': json.loads(request.form.get('webhook_headers', '{}')),
                }
            elif integration_type == 'email_notify':
                config = {
                    'recipients': [e.strip() for e in request.form.get('email_recipients', '').split(',')],
                    'subject': request.form.get('email_subject', f'New {form.name} submission'),
                }
            elif integration_type == 'crm_lead':
                config = {
                    'lead_stage': request.form.get('lead_stage', 'new'),
                }
            
            # Parse field mapping
            field_mapping = json.loads(request.form.get('field_mapping', '{}'))
            
            integration = FormIntegration(
                form_id=form.id,
                name=name,
                integration_type=integration_type,
                config=config,
                field_mapping=field_mapping,
                is_active=request.form.get('is_active', 'true') == 'true'
            )
            
            db.session.add(integration)
            db.session.commit()
            
            flash(f'Integration "{name}" created.', 'success')
            return redirect(url_for('forms_admin.list_integrations', form_id=form.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating integration: {str(e)}', 'error')
    
    return render_template('admin/forms/integration_form.html',
                         form=form,
                         integration=None)


@forms_admin_bp.route('/forms/<int:form_id>/integrations/<int:integration_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_integration(form_id, integration_id):
    """Delete an integration."""
    integration = FormIntegration.query.get_or_404(integration_id)
    
    if integration.form_id != form_id:
        flash('Invalid integration.', 'error')
        return redirect(url_for('forms_admin.list_integrations', form_id=form_id))
    
    db.session.delete(integration)
    db.session.commit()
    flash('Integration deleted.', 'success')
    
    return redirect(url_for('forms_admin.list_integrations', form_id=form_id))


# ============================================================================
# Survey Management Routes
# ============================================================================

@forms_admin_bp.route('/surveys')
@login_required
@role_required('admin')
def list_surveys():
    """List all surveys."""
    surveys = Survey.query.order_by(Survey.created_at.desc()).all()
    
    # Calculate NPS for each survey
    for survey in surveys:
        if survey.survey_type == 'nps':
            survey.nps_score = survey.calculate_nps()
    
    # Serialize for AdminDataTable
    surveys_json = json.dumps([{
        'id': survey.id,
        'name': f'<a href="{url_for("forms_admin.view_survey", survey_id=survey.id)}"><strong>{survey.name}</strong></a>',
        'type': '<span class="badge bg-primary">NPS</span>' if survey.survey_type == 'nps' else '<span class="badge bg-success">CSAT</span>' if survey.survey_type == 'csat' else '<span class="badge bg-info">CES</span>' if survey.survey_type == 'ces' else '<span class="badge bg-secondary">Custom</span>',
        'responses': survey.response_count,
        'score': f'<span class="badge {"bg-success" if (survey.nps_score or 0) > 50 else "bg-warning" if (survey.nps_score or 0) > 0 else "bg-danger"}">{survey.nps_score}</span>' if survey.survey_type == 'nps' and survey.nps_score is not None else (f'{round(survey.average_score, 1)}' if survey.average_score else '-'),
        'status': '<span class="badge bg-success">Active</span>' if survey.is_active else '<span class="badge bg-secondary">Inactive</span>',
        'created_at': survey.created_at.strftime('%Y-%m-%d') if survey.created_at else '-',
        'actions': f'''<div class="btn-group btn-group-sm">
            <a href="{url_for('forms_admin.view_survey', survey_id=survey.id)}" class="btn btn-outline-primary" title="Analytics"><i class="bi bi-bar-chart"></i></a>
            <a href="{url_for('forms.view_survey', survey_id=survey.id)}" target="_blank" class="btn btn-outline-secondary" title="Preview"><i class="bi bi-eye"></i></a>
            <form action="{url_for('forms_admin.delete_survey', survey_id=survey.id)}" method="POST" class="d-inline" onsubmit="return confirm('Delete?');"><input type="hidden" name="csrf_token" value=""><button type="submit" class="btn btn-outline-danger" title="Delete"><i class="bi bi-trash"></i></button></form>
        </div>'''
    } for survey in surveys])
    
    return render_template('admin/surveys/index.html', surveys=surveys, surveys_json=surveys_json)


@forms_admin_bp.route('/surveys/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_survey():
    """Create a new survey."""
    if request.method == 'POST':
        try:
            survey_type = request.form.get('survey_type', 'custom')
            name = request.form.get('name', '').strip()
            
            # Parse questions schema
            questions_json = request.form.get('questions_schema', '[]')
            questions_schema = json.loads(questions_json)
            
            # For NPS/CSAT, use standard questions if not provided
            if survey_type == 'nps' and not questions_schema:
                questions_schema = [{
                    'id': 'nps_score',
                    'type': 'rating',
                    'text': 'How likely are you to recommend us to a friend or colleague?',
                    'scale': 10,
                    'required': True,
                }, {
                    'id': 'nps_reason',
                    'type': 'textarea',
                    'text': 'What is the main reason for your score?',
                    'required': False,
                }]
            elif survey_type == 'csat' and not questions_schema:
                questions_schema = [{
                    'id': 'csat_score',
                    'type': 'rating',
                    'text': 'How satisfied are you with your experience?',
                    'scale': 5,
                    'required': True,
                }]
            
            survey = Survey(
                name=name,
                description=request.form.get('description', ''),
                survey_type=survey_type,
                questions_schema=questions_schema,
                trigger_event=request.form.get('trigger_event'),
                trigger_delay_hours=int(request.form.get('trigger_delay_hours', 0)),
                thank_you_message=request.form.get('thank_you_message', 'Thank you for your feedback!'),
                is_active=request.form.get('is_active', 'true') == 'true',
                created_by_id=current_user.id
            )
            
            db.session.add(survey)
            db.session.commit()
            
            flash(f'Survey "{name}" created.', 'success')
            return redirect(url_for('forms_admin.view_survey', survey_id=survey.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating survey: {str(e)}', 'error')
    
    return render_template('admin/surveys/create.html')


@forms_admin_bp.route('/surveys/<int:survey_id>')
@login_required
@role_required('admin')
def view_survey(survey_id):
    """View survey details and analytics."""
    survey = Survey.query.get_or_404(survey_id)
    
    # Calculate analytics
    responses = survey.responses.all()
    total_responses = len(responses)
    
    analytics = {
        'total_responses': total_responses,
        'average_score': None,
        'nps_score': None,
        'score_distribution': {},
    }
    
    if total_responses > 0:
        scores = [r.score for r in responses if r.score is not None]
        if scores:
            analytics['average_score'] = round(sum(scores) / len(scores), 1)
            
            # Score distribution
            for score in scores:
                analytics['score_distribution'][score] = analytics['score_distribution'].get(score, 0) + 1
        
        if survey.survey_type == 'nps':
            analytics['nps_score'] = survey.calculate_nps()
            
            # NPS category breakdown
            promoters = sum(1 for r in responses if r.nps_category == 'promoter')
            passives = sum(1 for r in responses if r.nps_category == 'passive')
            detractors = sum(1 for r in responses if r.nps_category == 'detractor')
            
            analytics['nps_breakdown'] = {
                'promoters': {'count': promoters, 'pct': round(promoters / total_responses * 100, 1)},
                'passives': {'count': passives, 'pct': round(passives / total_responses * 100, 1)},
                'detractors': {'count': detractors, 'pct': round(detractors / total_responses * 100, 1)},
            }
    
    # Recent responses
    recent_responses = survey.responses.order_by(SurveyResponse.completed_at.desc()).limit(20).all()
    
    return render_template('admin/surveys/detail.html',
                         survey=survey,
                         analytics=analytics,
                         recent_responses=recent_responses)


@forms_admin_bp.route('/surveys/<int:survey_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_survey(survey_id):
    """Delete a survey."""
    survey = Survey.query.get_or_404(survey_id)
    name = survey.name
    
    db.session.delete(survey)
    db.session.commit()
    
    flash(f'Survey "{name}" deleted.', 'success')
    return redirect(url_for('forms_admin.list_surveys'))


# ============================================================================
# Review Moderation Routes
# ============================================================================

@forms_admin_bp.route('/reviews')
@login_required
@role_required('admin')
def list_reviews():
    """List reviews for moderation."""
    status = request.args.get('status', 'pending')
    rating = request.args.get('rating', '')
    product_id = request.args.get('product_id', '')
    
    query = Review.query
    
    if status:
        query = query.filter_by(status=status)
    
    if rating:
        query = query.filter_by(rating=int(rating))
    
    if product_id:
        query = query.filter_by(product_id=int(product_id))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    reviews = query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    
    # Get products for filter dropdown
    products = Product.query.order_by(Product.name).all()
    
    # Stats
    pending_count = Review.query.filter_by(status='pending').count()
    
    return render_template('admin/reviews/index.html',
                         reviews=reviews,
                         status_filter=status,
                         rating_filter=rating,
                         product_id_filter=product_id,
                         products=products,
                         pending_count=pending_count)


@forms_admin_bp.route('/reviews/<int:review_id>')
@login_required
@role_required('admin')
def view_review(review_id):
    """View a single review."""
    review = Review.query.get_or_404(review_id)
    return render_template('admin/reviews/detail.html', review=review)


@forms_admin_bp.route('/reviews/<int:review_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_review(review_id):
    """Approve a review."""
    review = Review.query.get_or_404(review_id)
    review.approve(current_user.id)
    db.session.commit()
    
    flash('Review approved.', 'success')
    
    # Return to list or next pending
    next_pending = Review.query.filter_by(status='pending').first()
    if next_pending:
        return redirect(url_for('forms_admin.view_review', review_id=next_pending.id))
    
    return redirect(url_for('forms_admin.list_reviews'))


@forms_admin_bp.route('/reviews/<int:review_id>/reject', methods=['POST'])
@login_required
@role_required('admin')
def reject_review(review_id):
    """Reject a review."""
    review = Review.query.get_or_404(review_id)
    reason = request.form.get('reason', '')
    review.reject(current_user.id, reason)
    db.session.commit()
    
    flash('Review rejected.', 'success')
    
    # Return to list or next pending
    next_pending = Review.query.filter_by(status='pending').first()
    if next_pending:
        return redirect(url_for('forms_admin.view_review', review_id=next_pending.id))
    
    return redirect(url_for('forms_admin.list_reviews'))


@forms_admin_bp.route('/reviews/<int:review_id>/respond', methods=['POST'])
@login_required
@role_required('admin')
def respond_to_review(review_id):
    """Add owner response to a review."""
    review = Review.query.get_or_404(review_id)
    response_text = request.form.get('response', '').strip()
    
    if response_text:
        review.add_response(current_user.id, response_text)
        db.session.commit()
        flash('Response added.', 'success')
    else:
        flash('Response cannot be empty.', 'error')
    
    return redirect(url_for('forms_admin.view_review', review_id=review_id))


@forms_admin_bp.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_review(review_id):
    """Delete a review."""
    review = Review.query.get_or_404(review_id)
    
    db.session.delete(review)
    db.session.commit()
    
    flash('Review deleted.', 'success')
    return redirect(url_for('forms_admin.list_reviews'))


# ============================================================================
# API Endpoints for Form Builder
# ============================================================================

@forms_admin_bp.route('/api/forms/<int:form_id>/preview', methods=['POST'])
@login_required
@role_required('admin')
def preview_form(form_id):
    """Generate form preview HTML."""
    from app.modules.forms import generate_form_html
    
    form = FormDefinition.query.get_or_404(form_id)
    
    # Get fields from request (for preview before save)
    fields_schema = request.json.get('fields_schema', form.fields_schema)
    
    # Temporarily update form for preview
    preview_form = FormDefinition(
        name=form.name,
        slug=form.slug,
        fields_schema=fields_schema,
        settings=form.settings
    )
    
    html = generate_form_html(preview_form, include_wrapper=False)
    
    return jsonify({'html': html})


@forms_admin_bp.route('/api/field-types')
@login_required
@role_required('admin')
def get_field_types():
    """Get available field types for the builder."""
    from app.modules.forms import FIELD_TYPES
    
    return jsonify(FIELD_TYPES)
