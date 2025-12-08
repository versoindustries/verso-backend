"""
Phase 27: AI & Business Intelligence Routes

Admin routes for AI-powered insights and analytics.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from app.database import db
from app.models import ContactFormSubmission, Order, User


ai_bp = Blueprint('ai', __name__, url_prefix='/admin/ai')


def admin_required(f):
    """Decorator to require admin role."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('admin'):
            from flask import flash, redirect, url_for
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@ai_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """AI insights dashboard."""
    from app.modules.ai_intelligence import business_intelligence
    
    insights = business_intelligence.get_dashboard_insights()
    
    return render_template('admin/ai/dashboard.html', insights=insights)


@ai_bp.route('/lead-scoring')
@login_required
@admin_required
def lead_scoring():
    """Lead scoring interface."""
    from app.modules.ai_intelligence import lead_scorer
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get leads
    leads_query = ContactFormSubmission.query.order_by(
        ContactFormSubmission.submitted_at.desc()
    )
    leads = leads_query.paginate(page=page, per_page=per_page)
    
    # Score each lead
    scored_leads = []
    for lead in leads.items:
        lead_data = {
            'email': lead.email,
            'phone': lead.phone,
            'message': lead.message or '',
            'first_name': lead.first_name,
            'last_name': lead.last_name,
        }
        score_result = lead_scorer.score_lead(lead_data)
        scored_leads.append({
            'lead': lead,
            'score': score_result,
        })
    
    return render_template('admin/ai/lead_scoring.html',
                          scored_leads=scored_leads,
                          pagination=leads)


@ai_bp.route('/lead-scoring/score', methods=['POST'])
@login_required
@admin_required
def score_single_lead():
    """Score a single lead via API."""
    from app.modules.ai_intelligence import lead_scorer
    
    data = request.get_json()
    result = lead_scorer.score_lead(data)
    
    return jsonify(result)


@ai_bp.route('/churn-analysis')
@login_required
@admin_required
def churn_analysis():
    """Customer churn analysis."""
    from app.modules.ai_intelligence import churn_predictor
    
    # Get customers with order history
    customers_at_risk = []
    
    # Query customers with their last order date
    customers = User.query.filter(
        User.roles.any(name='customer')
    ).all()
    
    for customer in customers[:50]:  # Limit for performance
        # Get customer behavior data
        last_order = Order.query.filter_by(user_id=customer.id).order_by(
            Order.created_at.desc()
        ).first()
        
        customer_data = {
            'days_since_last_order': (datetime.utcnow() - last_order.created_at).days if last_order else 365,
            'days_since_login': (datetime.utcnow() - customer.last_seen).days if customer.last_seen else 90,
        }
        
        prediction = churn_predictor.predict_churn(customer_data)
        
        if prediction['risk_level'] in ['high', 'medium']:
            customers_at_risk.append({
                'customer': customer,
                'prediction': prediction,
            })
    
    # Sort by churn probability
    customers_at_risk.sort(key=lambda x: x['prediction']['churn_probability'], reverse=True)
    
    return render_template('admin/ai/churn_analysis.html',
                          customers_at_risk=customers_at_risk)


@ai_bp.route('/revenue-forecast')
@login_required
@admin_required
def revenue_forecast():
    """Revenue forecasting view."""
    from app.modules.ai_intelligence import revenue_forecaster
    
    # Get historical revenue data
    months_back = request.args.get('months', 12, type=int)
    forecast_periods = request.args.get('forecast', 6, type=int)
    
    # Aggregate monthly revenue
    historical_data = []
    current_date = datetime.utcnow()
    
    for i in range(months_back, 0, -1):
        month_start = current_date.replace(day=1) - timedelta(days=i * 30)
        month_end = month_start + timedelta(days=30)
        
        month_revenue = db.session.query(
            db.func.sum(Order.total_cents)
        ).filter(
            Order.created_at >= month_start,
            Order.created_at < month_end,
            Order.status == 'completed'
        ).scalar() or 0
        
        historical_data.append({
            'date': month_start.isoformat()[:10],
            'revenue': month_revenue / 100,  # Convert cents to dollars
        })
    
    # Generate forecast
    if len(historical_data) >= 3:
        forecast = revenue_forecaster.forecast_revenue(historical_data, periods=forecast_periods)
    else:
        forecast = {'error': 'Insufficient data for forecasting'}
    
    return render_template('admin/ai/revenue_forecast.html',
                          historical_data=historical_data,
                          forecast=forecast)


@ai_bp.route('/anomalies')
@login_required
@admin_required
def anomaly_detection():
    """Anomaly detection dashboard."""
    from app.modules.ai_intelligence import anomaly_detector
    
    # Check various metrics for anomalies
    anomalies = {}
    
    # Daily orders
    order_data = []
    for i in range(30, 0, -1):
        day = datetime.utcnow() - timedelta(days=i)
        count = Order.query.filter(
            db.func.date(Order.created_at) == day.date()
        ).count()
        order_data.append({
            'date': day.isoformat()[:10],
            'value': count,
        })
    
    order_anomalies = anomaly_detector.detect_anomalies(order_data)
    if order_anomalies:
        anomalies['daily_orders'] = order_anomalies
    
    # Daily leads
    lead_data = []
    for i in range(30, 0, -1):
        day = datetime.utcnow() - timedelta(days=i)
        count = ContactFormSubmission.query.filter(
            db.func.date(ContactFormSubmission.submitted_at) == day.date()
        ).count()
        lead_data.append({
            'date': day.isoformat()[:10],
            'value': count,
        })
    
    lead_anomalies = anomaly_detector.detect_anomalies(lead_data)
    if lead_anomalies:
        anomalies['daily_leads'] = lead_anomalies
    
    # Daily revenue
    revenue_data = []
    for i in range(30, 0, -1):
        day = datetime.utcnow() - timedelta(days=i)
        revenue = db.session.query(
            db.func.sum(Order.total_cents)
        ).filter(
            db.func.date(Order.created_at) == day.date(),
            Order.status == 'completed'
        ).scalar() or 0
        revenue_data.append({
            'date': day.isoformat()[:10],
            'value': revenue / 100,
        })
    
    revenue_anomalies = anomaly_detector.detect_anomalies(revenue_data)
    if revenue_anomalies:
        anomalies['daily_revenue'] = revenue_anomalies
    
    return render_template('admin/ai/anomalies.html', anomalies=anomalies)


@ai_bp.route('/insights')
@login_required
@admin_required
def business_insights():
    """Overall business intelligence insights."""
    from app.modules.ai_intelligence import (
        lead_scorer, churn_predictor, revenue_forecaster
    )
    
    insights = {
        'summary': {},
        'recommendations': [],
    }
    
    # Lead summary
    recent_leads = ContactFormSubmission.query.filter(
        ContactFormSubmission.submitted_at >= datetime.utcnow() - timedelta(days=7)
    ).all()
    
    if recent_leads:
        scores = [lead_scorer.score_lead({
            'email': l.email,
            'phone': l.phone,
            'message': l.message or '',
        }) for l in recent_leads]
        
        insights['summary']['leads'] = {
            'total_this_week': len(recent_leads),
            'average_score': round(sum(s['score'] for s in scores) / len(scores), 1),
            'hot_leads': len([s for s in scores if s['grade'] == 'A']),
        }
        
        if insights['summary']['leads']['hot_leads'] > 0:
            insights['recommendations'].append({
                'priority': 'high',
                'title': f"{insights['summary']['leads']['hot_leads']} hot leads require immediate attention",
                'action': 'Review lead scoring dashboard and prioritize outreach',
            })
    
    # Revenue trend
    last_month_revenue = db.session.query(
        db.func.sum(Order.total_cents)
    ).filter(
        Order.created_at >= datetime.utcnow() - timedelta(days=30),
        Order.status == 'completed'
    ).scalar() or 0
    
    previous_month_revenue = db.session.query(
        db.func.sum(Order.total_cents)
    ).filter(
        Order.created_at >= datetime.utcnow() - timedelta(days=60),
        Order.created_at < datetime.utcnow() - timedelta(days=30),
        Order.status == 'completed'
    ).scalar() or 0
    
    if previous_month_revenue > 0:
        revenue_change = ((last_month_revenue - previous_month_revenue) / previous_month_revenue) * 100
        insights['summary']['revenue'] = {
            'last_30_days': last_month_revenue / 100,
            'change_percent': round(revenue_change, 1),
        }
        
        if revenue_change < -10:
            insights['recommendations'].append({
                'priority': 'high',
                'title': f'Revenue declined {abs(round(revenue_change, 1))}% vs previous month',
                'action': 'Review pricing, marketing campaigns, and customer retention',
            })
    
    return render_template('admin/ai/insights.html', insights=insights)


# API Endpoints

@ai_bp.route('/api/lead-scores')
@login_required
@admin_required
def api_lead_scores():
    """API endpoint for lead scores."""
    from app.modules.ai_intelligence import lead_scorer
    
    limit = request.args.get('limit', 10, type=int)
    
    leads = ContactFormSubmission.query.order_by(
        ContactFormSubmission.submitted_at.desc()
    ).limit(limit).all()
    
    results = []
    for lead in leads:
        score = lead_scorer.score_lead({
            'email': lead.email,
            'phone': lead.phone,
            'message': lead.message or '',
        })
        results.append({
            'id': lead.id,
            'email': lead.email,
            'submitted_at': lead.submitted_at.isoformat() if lead.submitted_at else None,
            'score': score['score'],
            'grade': score['grade'],
        })
    
    return jsonify({'leads': results})


@ai_bp.route('/api/forecast')
@login_required
@admin_required
def api_forecast():
    """API endpoint for revenue forecast."""
    from app.modules.ai_intelligence import revenue_forecaster
    
    # Get last 12 months of revenue
    historical_data = []
    current_date = datetime.utcnow()
    
    for i in range(12, 0, -1):
        month_start = current_date.replace(day=1) - timedelta(days=i * 30)
        month_end = month_start + timedelta(days=30)
        
        month_revenue = db.session.query(
            db.func.sum(Order.total_cents)
        ).filter(
            Order.created_at >= month_start,
            Order.created_at < month_end,
            Order.status == 'completed'
        ).scalar() or 0
        
        historical_data.append({
            'date': month_start.isoformat()[:10],
            'revenue': month_revenue / 100,
        })
    
    forecast = revenue_forecaster.forecast_revenue(historical_data, periods=6)
    
    return jsonify({
        'historical': historical_data,
        'forecast': forecast,
    })
