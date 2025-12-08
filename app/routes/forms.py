"""
Forms & Data Collection Platform - Public Routes

Public-facing routes for:
- Dynamic form rendering and submission
- Survey responses
- Product reviews
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime
import json

from app.database import db
from app.models import (
    FormDefinition, FormSubmission, FormIntegration,
    Survey, SurveyResponse,
    Review, ReviewVote, Product, Order
)
from app.modules.forms import (
    FormValidator, sanitize_submission, check_honeypot, check_rate_limit,
    calculate_spam_score, extract_utm_params, get_client_ip, process_integrations
)


forms_bp = Blueprint('forms', __name__)


# ============================================================================
# Dynamic Form Routes
# ============================================================================

@forms_bp.route('/forms/<slug>')
def view_form(slug):
    """Render a dynamic form by slug."""
    form = FormDefinition.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Extract prefill values from query params
    prefill_data = {}
    for field_def in (form.fields_schema or []):
        field_name = field_def.get('name')
        if field_name and request.args.get(field_name):
            prefill_data[field_name] = request.args.get(field_name)
    
    return render_template('forms/form.html', form=form, prefill_data=prefill_data)


@forms_bp.route('/forms/<slug>/submit', methods=['POST'])
def submit_form(slug):
    """Handle form submission."""
    form = FormDefinition.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Get client info
    ip_address = get_client_ip()
    user_agent = request.headers.get('User-Agent', '')[:500]
    referrer = request.headers.get('Referer', '')[:500]
    
    # Spam protection: honeypot check
    settings = form.settings or {}
    if settings.get('honeypot', True) and check_honeypot(request.form):
        # Silently accept but mark as spam
        submission = FormSubmission(
            form_id=form.id,
            data={},
            submitted_by_id=current_user.id if current_user.is_authenticated else None,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            is_spam=True,
            spam_score=100,
        )
        db.session.add(submission)
        db.session.commit()
        
        # Show success anyway to not tip off bots
        return _handle_success_redirect(form)
    
    # Spam protection: rate limiting
    rate_limit = settings.get('rate_limit', 5)
    if check_rate_limit(ip_address, form.id, max_submissions=rate_limit):
        flash('Too many submissions. Please try again later.', 'error')
        return redirect(url_for('forms.view_form', slug=slug))
    
    # Extract form data (exclude CSRF token and honeypot)
    raw_data = {}
    for key, value in request.form.items():
        if key not in ('csrf_token', 'hp_field'):
            # Handle multi-value fields
            values = request.form.getlist(key)
            raw_data[key] = values if len(values) > 1 else value
    
    # Handle file uploads
    files_data = {}
    for key, file in request.files.items():
        if file and file.filename:
            # Save file (simplified - in production use secure storage)
            from werkzeug.utils import secure_filename
            import os
            
            filename = secure_filename(file.filename)
            upload_dir = os.path.join('app', 'static', 'uploads', 'forms', str(form.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            filepath = os.path.join(upload_dir, f'{datetime.utcnow().timestamp()}_{filename}')
            file.save(filepath)
            
            files_data[key] = {
                'filename': filename,
                'path': filepath,
                'content_type': file.content_type,
            }
    
    # Merge file references into data
    raw_data.update({k: v['filename'] for k, v in files_data.items()})
    
    # Sanitize submission data
    sanitized_data = sanitize_submission(raw_data, form.fields_schema)
    
    # Validate
    validator = FormValidator(form)
    is_valid, errors = validator.validate(sanitized_data)
    
    if not is_valid:
        # Re-render form with errors
        return render_template('forms/form.html', 
                             form=form, 
                             prefill_data=sanitized_data, 
                             errors=errors)
    
    # Calculate spam score
    spam_score = calculate_spam_score(sanitized_data, ip_address)
    is_spam = spam_score >= 70  # Threshold
    
    # Extract UTM params
    utm_params = extract_utm_params(request.args)
    
    # Create submission
    submission = FormSubmission(
        form_id=form.id,
        data=sanitized_data,
        submitted_by_id=current_user.id if current_user.is_authenticated else None,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer,
        utm_params=utm_params,
        is_spam=is_spam,
        spam_score=spam_score,
        attachments=[v for v in files_data.values()],
    )
    
    db.session.add(submission)
    form.increment_submissions()
    db.session.commit()
    
    # Process integrations (in background in production)
    if not is_spam:
        try:
            process_integrations(form, submission)
        except Exception as e:
            # Log but don't fail the submission
            from flask import current_app
            current_app.logger.error(f'Integration processing failed: {e}')
    
    return _handle_success_redirect(form)


def _handle_success_redirect(form):
    """Handle redirect after successful form submission."""
    settings = form.settings or {}
    
    # Custom redirect URL
    redirect_url = settings.get('redirect_url')
    if redirect_url:
        return redirect(redirect_url)
    
    # Default thank you page
    success_message = settings.get('success_message', 'Thank you for your submission!')
    return render_template('forms/thank_you.html', 
                         form=form, 
                         success_message=success_message)


# ============================================================================
# Survey Routes
# ============================================================================

@forms_bp.route('/surveys/<int:survey_id>')
def view_survey(survey_id):
    """Render a survey."""
    survey = Survey.query.filter_by(id=survey_id, is_active=True).first_or_404()
    
    # Check if user already responded (optional, based on context)
    already_responded = False
    if current_user.is_authenticated:
        existing = SurveyResponse.query.filter_by(
            survey_id=survey_id, 
            user_id=current_user.id
        ).first()
        already_responded = existing is not None
    
    return render_template('surveys/survey.html', 
                         survey=survey, 
                         already_responded=already_responded)


@forms_bp.route('/surveys/<int:survey_id>/submit', methods=['POST'])
def submit_survey(survey_id):
    """Submit a survey response."""
    survey = Survey.query.filter_by(id=survey_id, is_active=True).first_or_404()
    
    # Check for duplicate response
    if current_user.is_authenticated:
        existing = SurveyResponse.query.filter_by(
            survey_id=survey_id, 
            user_id=current_user.id
        ).first()
        if existing:
            flash('You have already submitted a response to this survey.', 'info')
            return redirect(url_for('forms.survey_thank_you', survey_id=survey_id))
    
    # Collect responses
    responses_data = {}
    primary_score = None
    
    for question in (survey.questions_schema or []):
        q_id = question.get('id')
        q_type = question.get('type')
        
        value = request.form.get(q_id)
        
        # Handle multi-value questions
        if q_type in ('checkbox_group', 'multi_select'):
            value = request.form.getlist(q_id)
        
        # Convert rating scores to int
        if q_type == 'rating' and value:
            try:
                value = int(value)
                # Use first rating question as primary score
                if primary_score is None:
                    primary_score = value
            except ValueError:
                pass
        
        responses_data[q_id] = value
    
    # Create response
    response = SurveyResponse(
        survey_id=survey.id,
        user_id=current_user.id if current_user.is_authenticated else None,
        responses=responses_data,
        score=primary_score,
        ip_address=get_client_ip(),
        user_agent=request.headers.get('User-Agent', '')[:500],
    )
    
    # Classify NPS if applicable
    if survey.survey_type == 'nps' and primary_score is not None:
        response.classify_nps()
    
    # Extract context from query params
    context_type = request.args.get('context_type')
    context_id = request.args.get('context_id')
    if context_type:
        response.context_type = context_type
    if context_id:
        try:
            response.context_id = int(context_id)
        except ValueError:
            pass
    
    db.session.add(response)
    
    # Update survey stats
    survey.response_count += 1
    if primary_score is not None:
        # Recalculate average
        all_scores = [r.score for r in survey.responses.all() if r.score is not None]
        all_scores.append(primary_score)
        survey.average_score = sum(all_scores) / len(all_scores)
    
    db.session.commit()
    
    return redirect(url_for('forms.survey_thank_you', survey_id=survey_id))


@forms_bp.route('/surveys/<int:survey_id>/thank-you')
def survey_thank_you(survey_id):
    """Survey completion page."""
    survey = Survey.query.get_or_404(survey_id)
    
    thank_you_message = survey.thank_you_message or 'Thank you for your feedback!'
    
    # Check for redirect
    if survey.redirect_url:
        return redirect(survey.redirect_url)
    
    return render_template('surveys/thank_you.html', 
                         survey=survey, 
                         thank_you_message=thank_you_message)


# ============================================================================
# Product Review Routes
# ============================================================================

@forms_bp.route('/products/<int:product_id>/reviews')
def product_reviews(product_id):
    """View all approved reviews for a product."""
    product = Product.query.get_or_404(product_id)
    
    # Filtering and sorting
    sort = request.args.get('sort', 'newest')
    rating = request.args.get('rating')
    
    query = Review.query.filter_by(product_id=product_id, status='approved')
    
    if rating:
        query = query.filter_by(rating=int(rating))
    
    if sort == 'newest':
        query = query.order_by(Review.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Review.created_at.asc())
    elif sort == 'highest':
        query = query.order_by(Review.rating.desc())
    elif sort == 'lowest':
        query = query.order_by(Review.rating.asc())
    elif sort == 'helpful':
        query = query.order_by(Review.helpful_count.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    reviews = query.paginate(page=page, per_page=10, error_out=False)
    
    # Calculate rating distribution
    rating_counts = {}
    for r in range(1, 6):
        rating_counts[r] = Review.query.filter_by(
            product_id=product_id, status='approved', rating=r
        ).count()
    
    total_reviews = sum(rating_counts.values())
    avg_rating = 0
    if total_reviews > 0:
        avg_rating = sum(r * count for r, count in rating_counts.items()) / total_reviews
    
    return render_template('shop/reviews.html',
                         product=product,
                         reviews=reviews,
                         rating_counts=rating_counts,
                         total_reviews=total_reviews,
                         avg_rating=round(avg_rating, 1),
                         sort=sort,
                         rating_filter=rating)


@forms_bp.route('/products/<int:product_id>/reviews/new', methods=['GET', 'POST'])
@login_required
def create_review(product_id):
    """Create a new product review."""
    product = Product.query.get_or_404(product_id)
    
    # Check if user already reviewed this product
    existing_review = Review.query.filter_by(
        product_id=product_id, 
        user_id=current_user.id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this product.', 'info')
        return redirect(url_for('forms.product_reviews', product_id=product_id))
    
    # Check for verified purchase
    verified_order = Order.query.filter(
        Order.user_id == current_user.id,
        Order.status.in_(['completed', 'delivered'])
    ).join(Order.items).filter_by(product_id=product_id).first()
    
    if request.method == 'POST':
        rating = request.form.get('rating')
        title = request.form.get('title', '').strip()[:200]
        body = request.form.get('body', '').strip()
        
        # Validate rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            flash('Please select a rating from 1 to 5.', 'error')
            return render_template('shop/review_form.html', product=product)
        
        review = Review(
            product_id=product_id,
            user_id=current_user.id,
            order_id=verified_order.id if verified_order else None,
            rating=rating,
            title=title,
            body=body,
            verified_purchase=verified_order is not None,
            status='pending',  # Requires moderation
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Thank you for your review! It will be visible after moderation.', 'success')
        return redirect(url_for('forms.product_reviews', product_id=product_id))
    
    return render_template('shop/review_form.html', 
                         product=product,
                         is_verified_purchase=verified_order is not None)


@forms_bp.route('/reviews/<int:review_id>/vote', methods=['POST'])
@login_required
def vote_review(review_id):
    """Vote on a review's helpfulness."""
    review = Review.query.get_or_404(review_id)
    
    if review.status != 'approved':
        return jsonify({'error': 'Review not found'}), 404
    
    # Check for existing vote
    existing_vote = ReviewVote.query.filter_by(
        review_id=review_id,
        user_id=current_user.id
    ).first()
    
    is_helpful = request.form.get('helpful', 'true') == 'true'
    
    if existing_vote:
        # Update existing vote
        if existing_vote.is_helpful != is_helpful:
            # Switching vote
            if existing_vote.is_helpful:
                review.helpful_count -= 1
                review.not_helpful_count += 1
            else:
                review.not_helpful_count -= 1
                review.helpful_count += 1
            existing_vote.is_helpful = is_helpful
    else:
        # Create new vote
        vote = ReviewVote(
            review_id=review_id,
            user_id=current_user.id,
            is_helpful=is_helpful
        )
        db.session.add(vote)
        
        if is_helpful:
            review.helpful_count += 1
        else:
            review.not_helpful_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'helpful_count': review.helpful_count,
        'not_helpful_count': review.not_helpful_count
    })


# ============================================================================
# Embed/Widget Routes
# ============================================================================

@forms_bp.route('/embed/form/<slug>')
def embed_form(slug):
    """Render embeddable form widget."""
    form = FormDefinition.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Render without full base template
    return render_template('forms/embed.html', form=form)


@forms_bp.route('/embed/survey/<int:survey_id>')
def embed_survey(survey_id):
    """Render embeddable survey widget."""
    survey = Survey.query.filter_by(id=survey_id, is_active=True).first_or_404()
    
    return render_template('surveys/embed.html', survey=survey)


# ============================================================================
# AJAX/API Endpoints
# ============================================================================

@forms_bp.route('/api/forms/<slug>/validate', methods=['POST'])
def validate_form_field(slug):
    """Real-time field validation via AJAX."""
    form = FormDefinition.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    field_name = request.json.get('field')
    value = request.json.get('value')
    
    # Find field definition
    field_def = form.get_field(field_name)
    if not field_def:
        return jsonify({'valid': True})
    
    # Validate single field
    validator = FormValidator(form)
    temp_data = {field_name: value}
    is_valid, errors = validator.validate(temp_data)
    
    return jsonify({
        'valid': field_name not in errors,
        'error': errors.get(field_name)
    })
