"""
Phase 14: Enhanced Analytics Routes

Provides comprehensive analytics dashboard with traffic breakdown,
visitor analysis, session tracking, and conversion funnel management.
"""

from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import (
    PageView, VisitorSession, ConversionGoal, Conversion, 
    Funnel, FunnelStep, db
)
from app.modules.decorators import role_required
from app.modules.reporting import (
    calculate_traffic_metrics, calculate_daily_revenue,
    get_date_range_presets, track_conversion
)
from sqlalchemy import func, desc, case
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/admin/analytics')


@analytics_bp.route('/')
@login_required
@role_required('admin')
def dashboard():
    """Enhanced analytics dashboard with key metrics."""
    # Date range from query params or default to last 30 days
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get traffic metrics
    metrics = calculate_traffic_metrics(start_date, end_date)
    
    # Total views (all time)
    total_views = PageView.query.count()
    
    # Top pages
    top_pages = db.session.query(
        PageView.url, func.count(PageView.id).label('count')
    ).filter(
        PageView.timestamp >= start_date
    ).group_by(PageView.url).order_by(desc('count')).limit(10).all()
    
    # Conversion goals summary
    goals = ConversionGoal.query.filter_by(is_active=True).all()
    goal_stats = []
    for goal in goals:
        conversions = Conversion.query.filter(
            Conversion.goal_id == goal.id,
            Conversion.timestamp >= start_date
        ).count()
        goal_stats.append({
            'goal': goal,
            'conversions': conversions
        })
    
    return render_template('admin/analytics/dashboard.html',
        total_views=total_views,
        metrics=metrics,
        top_pages=top_pages,
        goal_stats=goal_stats,
        days=days,
        presets=get_date_range_presets()
    )


@analytics_bp.route('/traffic')
@login_required
@role_required('admin')
def traffic():
    """Traffic breakdown by sources, pages, and devices."""
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # UTM source breakdown
    sources = db.session.query(
        PageView.utm_source,
        func.count(PageView.id).label('views'),
        func.count(func.distinct(PageView.session_id)).label('sessions')
    ).filter(
        PageView.timestamp >= start_date,
        PageView.timestamp <= end_date
    ).group_by(PageView.utm_source).order_by(desc('views')).all()
    
    # UTM medium breakdown
    mediums = db.session.query(
        PageView.utm_medium,
        func.count(PageView.id).label('views')
    ).filter(
        PageView.timestamp >= start_date,
        PageView.timestamp <= end_date
    ).group_by(PageView.utm_medium).order_by(desc('views')).all()
    
    # Top landing pages
    landing_pages = db.session.query(
        VisitorSession.entry_page,
        func.count(VisitorSession.id).label('sessions')
    ).filter(
        VisitorSession.started_at >= start_date,
        VisitorSession.started_at <= end_date
    ).group_by(VisitorSession.entry_page).order_by(desc('sessions')).limit(10).all()
    
    # Device breakdown
    devices = db.session.query(
        PageView.device_type,
        func.count(PageView.id).label('views')
    ).filter(
        PageView.timestamp >= start_date,
        PageView.timestamp <= end_date
    ).group_by(PageView.device_type).all()
    
    # Browser breakdown
    browsers = db.session.query(
        PageView.browser,
        func.count(PageView.id).label('views')
    ).filter(
        PageView.timestamp >= start_date,
        PageView.timestamp <= end_date
    ).group_by(PageView.browser).order_by(desc('views')).limit(10).all()
    
    return render_template('admin/analytics/traffic.html',
        sources=sources,
        mediums=mediums,
        landing_pages=landing_pages,
        devices=devices,
        browsers=browsers,
        days=days
    )


@analytics_bp.route('/visitors')
@login_required
@role_required('admin')
def visitors():
    """Unique visitor analysis with session details."""
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Daily unique visitors
    daily_visitors = db.session.query(
        func.date(VisitorSession.started_at).label('date'),
        func.count(VisitorSession.id).label('sessions'),
        func.count(func.distinct(VisitorSession.ip_hash)).label('unique_visitors')
    ).filter(
        VisitorSession.started_at >= start_date,
        VisitorSession.started_at <= end_date
    ).group_by(
        func.date(VisitorSession.started_at)
    ).order_by(
        func.date(VisitorSession.started_at)
    ).all()
    
    # New vs returning (based on user_id presence)
    new_visitors = VisitorSession.query.filter(
        VisitorSession.started_at >= start_date,
        VisitorSession.started_at <= end_date,
        VisitorSession.user_id.is_(None)
    ).count()
    
    returning_visitors = VisitorSession.query.filter(
        VisitorSession.started_at >= start_date,
        VisitorSession.started_at <= end_date,
        VisitorSession.user_id.isnot(None)
    ).count()
    
    # Top referrers
    referrers = db.session.query(
        VisitorSession.referrer,
        func.count(VisitorSession.id).label('sessions')
    ).filter(
        VisitorSession.started_at >= start_date,
        VisitorSession.started_at <= end_date,
        VisitorSession.referrer.isnot(None),
        VisitorSession.referrer != ''
    ).group_by(VisitorSession.referrer).order_by(desc('sessions')).limit(10).all()
    
    # Country breakdown (if available)
    countries = db.session.query(
        VisitorSession.country,
        func.count(VisitorSession.id).label('sessions')
    ).filter(
        VisitorSession.started_at >= start_date,
        VisitorSession.started_at <= end_date,
        VisitorSession.country.isnot(None)
    ).group_by(VisitorSession.country).order_by(desc('sessions')).limit(10).all()
    
    return render_template('admin/analytics/visitors.html',
        daily_visitors=daily_visitors,
        new_visitors=new_visitors,
        returning_visitors=returning_visitors,
        referrers=referrers,
        countries=countries,
        days=days
    )


@analytics_bp.route('/sessions')
@login_required
@role_required('admin')
def sessions():
    """Session flow visualization."""
    days = request.args.get('days', 7, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Recent sessions with details
    recent_sessions = VisitorSession.query.filter(
        VisitorSession.started_at >= start_date
    ).order_by(desc(VisitorSession.started_at)).limit(100).all()
    
    # Session duration distribution
    durations = db.session.query(
        case(
            (VisitorSession.duration_seconds < 30, '0-30s'),
            (VisitorSession.duration_seconds < 120, '30s-2m'),
            (VisitorSession.duration_seconds < 300, '2-5m'),
            (VisitorSession.duration_seconds < 600, '5-10m'),
            else_='10m+'
        ).label('bucket'),
        func.count(VisitorSession.id).label('count')
    ).filter(
        VisitorSession.started_at >= start_date,
        VisitorSession.duration_seconds.isnot(None)
    ).group_by('bucket').all()
    
    # Pages per session distribution
    pages_dist = db.session.query(
        case(
            (VisitorSession.pages_viewed == 1, '1 page'),
            (VisitorSession.pages_viewed <= 3, '2-3 pages'),
            (VisitorSession.pages_viewed <= 5, '4-5 pages'),
            (VisitorSession.pages_viewed <= 10, '6-10 pages'),
            else_='10+ pages'
        ).label('bucket'),
        func.count(VisitorSession.id).label('count')
    ).filter(
        VisitorSession.started_at >= start_date
    ).group_by('bucket').all()
    
    # Bounce rate trend
    bounce_trend = db.session.query(
        func.date(VisitorSession.started_at).label('date'),
        func.count(VisitorSession.id).label('total'),
        func.sum(func.cast(VisitorSession.bounce, db.Integer)).label('bounces')
    ).filter(
        VisitorSession.started_at >= start_date
    ).group_by(
        func.date(VisitorSession.started_at)
    ).order_by(
        func.date(VisitorSession.started_at)
    ).all()
    
    return render_template('admin/analytics/sessions.html',
        recent_sessions=recent_sessions,
        durations=durations,
        pages_dist=pages_dist,
        bounce_trend=bounce_trend,
        days=days
    )


# ============================================================================
# Conversion Goals
# ============================================================================

@analytics_bp.route('/goals')
@login_required
@role_required('admin')
def goals():
    """Conversion goal management."""
    import json
    from app.forms import CSRFTokenForm
    
    goals_list = ConversionGoal.query.order_by(desc(ConversionGoal.created_at)).all()
    form = CSRFTokenForm()
    
    # Get conversion counts for each goal (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    goal_metrics = {}
    for goal in goals_list:
        count = Conversion.query.filter(
            Conversion.goal_id == goal.id,
            Conversion.timestamp >= thirty_days_ago
        ).count()
        total_value = db.session.query(
            func.sum(Conversion.value)
        ).filter(
            Conversion.goal_id == goal.id,
            Conversion.timestamp >= thirty_days_ago
        ).scalar() or 0
        goal_metrics[goal.id] = {'count': count, 'value': total_value}
    
    # Goal type badges
    type_colors = {'page_visit': 'info', 'form_submit': 'primary', 'purchase': 'success', 'signup': 'warning'}
    
    # Serialize for AdminDataTable
    goals_json = json.dumps([{
        'id': g.id,
        'name': f'<strong>{g.name}</strong>' + (f'<br><small class="text-muted">{g.description[:50]}...</small>' if g.description and len(g.description) > 50 else (f'<br><small class="text-muted">{g.description}</small>' if g.description else '')),
        'type': f'<span class="badge bg-{type_colors.get(g.goal_type, "secondary")}">{g.goal_type.replace("_", " ").title() if g.goal_type else "-"}</span>',
        'target_path': f'<code>{g.target_path}</code>' if g.target_path else '-',
        'value': f'${g.target_value:.2f}' if g.target_value else '-',
        'conversions': f'<span class="badge bg-primary rounded-pill">{goal_metrics[g.id]["count"]}</span>',
        'total_value': f'${goal_metrics[g.id]["value"]:.2f}' if goal_metrics[g.id]["value"] else '-',
        'status': '<span class="badge bg-success">Active</span>' if g.is_active else '<span class="badge bg-secondary">Inactive</span>',
        'actions': f'<a href="{url_for("analytics.edit_goal", goal_id=g.id)}" class="btn btn-sm btn-outline-primary" title="Edit"><i class="fas fa-edit"></i></a> <form action="{url_for("analytics.delete_goal", goal_id=g.id)}" method="POST" class="d-inline" onsubmit="return confirm(\'Delete this goal?\');"><input type="hidden" name="csrf_token" value="{form.csrf_token._value()}"><button type="submit" class="btn btn-sm btn-outline-danger" title="Delete"><i class="fas fa-trash"></i></button></form>'
    } for g in goals_list])
    
    return render_template('admin/analytics/goals/index.html',
        goals=goals_list,
        metrics=goal_metrics,
        goals_json=goals_json
    )


@analytics_bp.route('/goals/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_goal():
    """Create a new conversion goal."""
    if request.method == 'POST':
        goal = ConversionGoal(
            name=request.form.get('name'),
            description=request.form.get('description'),
            goal_type=request.form.get('goal_type'),
            target_path=request.form.get('target_path'),
            target_value=float(request.form.get('target_value') or 0),
            count_once_per_session=request.form.get('count_once_per_session') == 'on',
            created_by_id=current_user.id
        )
        db.session.add(goal)
        db.session.commit()
        flash('Conversion goal created successfully.', 'success')
        return redirect(url_for('analytics.goals'))
    
    return render_template('admin/analytics/goals/create.html')


@analytics_bp.route('/goals/<int:goal_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_goal(goal_id):
    """Edit an existing conversion goal."""
    goal = ConversionGoal.query.get_or_404(goal_id)
    
    if request.method == 'POST':
        goal.name = request.form.get('name')
        goal.description = request.form.get('description')
        goal.goal_type = request.form.get('goal_type')
        goal.target_path = request.form.get('target_path')
        goal.target_value = float(request.form.get('target_value') or 0)
        goal.count_once_per_session = request.form.get('count_once_per_session') == 'on'
        goal.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Conversion goal updated.', 'success')
        return redirect(url_for('analytics.goals'))
    
    return render_template('admin/analytics/goals/edit.html', goal=goal)


@analytics_bp.route('/goals/<int:goal_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_goal(goal_id):
    """Delete a conversion goal."""
    goal = ConversionGoal.query.get_or_404(goal_id)
    db.session.delete(goal)
    db.session.commit()
    flash('Conversion goal deleted.', 'success')
    return redirect(url_for('analytics.goals'))


# ============================================================================
# Funnels
# ============================================================================

@analytics_bp.route('/funnels')
@login_required
@role_required('admin')
def funnels():
    """List all conversion funnels."""
    funnels_list = Funnel.query.order_by(desc(Funnel.created_at)).all()
    
    # Calculate conversion rates for each funnel
    funnel_data = []
    for funnel in funnels_list:
        steps = funnel.steps.order_by(FunnelStep.step_order).all()
        rates = funnel.calculate_conversion_rates()
        final_rate = rates[-1]['rate'] if rates and len(rates) > 1 else 0
        funnel_data.append({
            'funnel': funnel,
            'step_count': len(steps),
            'conversion_rate': final_rate
        })
    
    return render_template('admin/analytics/funnels/index.html',
        funnels=funnel_data
    )


@analytics_bp.route('/funnels/<int:funnel_id>')
@login_required
@role_required('admin')
def funnel_detail(funnel_id):
    """Funnel detail with conversion rates."""
    funnel = Funnel.query.get_or_404(funnel_id)
    
    # Get date range
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Calculate rates
    rates = funnel.calculate_conversion_rates(start_date, end_date)
    
    return render_template('admin/analytics/funnels/detail.html',
        funnel=funnel,
        rates=rates,
        days=days
    )


@analytics_bp.route('/funnels/new', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_funnel():
    """Create a new conversion funnel."""
    goals = ConversionGoal.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        funnel = Funnel(
            name=request.form.get('name'),
            description=request.form.get('description'),
            created_by_id=current_user.id
        )
        db.session.add(funnel)
        db.session.flush()  # Get funnel ID
        
        # Add steps
        step_names = request.form.getlist('step_name[]')
        step_goals = request.form.getlist('step_goal[]')
        
        for i, (name, goal_id) in enumerate(zip(step_names, step_goals)):
            if name and goal_id:
                step = FunnelStep(
                    funnel_id=funnel.id,
                    goal_id=int(goal_id),
                    name=name,
                    step_order=i
                )
                db.session.add(step)
        
        db.session.commit()
        flash('Funnel created successfully.', 'success')
        return redirect(url_for('analytics.funnels'))
    
    return render_template('admin/analytics/funnels/create.html', goals=goals)


@analytics_bp.route('/funnels/<int:funnel_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_funnel(funnel_id):
    """Delete a funnel."""
    funnel = Funnel.query.get_or_404(funnel_id)
    db.session.delete(funnel)
    db.session.commit()
    flash('Funnel deleted.', 'success')
    return redirect(url_for('analytics.funnels'))


# ============================================================================
# API Endpoints for Charts
# ============================================================================

@analytics_bp.route('/api/daily_traffic')
@login_required
@role_required('admin')
def daily_traffic():
    """API: Daily traffic data for charts."""
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    results = db.session.query(
        func.date(PageView.timestamp).label('date'),
        func.count(PageView.id).label('page_views'),
        func.count(func.distinct(PageView.session_id)).label('sessions')
    ).filter(
        PageView.timestamp >= start_date
    ).group_by(
        func.date(PageView.timestamp)
    ).order_by(
        func.date(PageView.timestamp).asc()
    ).all()
    
    data = {
        'labels': [str(r.date) for r in results],
        'page_views': [r.page_views for r in results],
        'sessions': [r.sessions for r in results]
    }
    return jsonify(data)


@analytics_bp.route('/api/utm_breakdown')
@login_required
@role_required('admin')
def utm_breakdown():
    """API: UTM source breakdown for charts."""
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    results = db.session.query(
        func.coalesce(PageView.utm_source, 'Direct').label('source'),
        func.count(PageView.id).label('views')
    ).filter(
        PageView.timestamp >= start_date
    ).group_by(
        PageView.utm_source
    ).order_by(desc('views')).limit(10).all()
    
    data = {
        'labels': [r.source for r in results],
        'values': [r.views for r in results]
    }
    return jsonify(data)


@analytics_bp.route('/api/device_breakdown')
@login_required
@role_required('admin')
def device_breakdown():
    """API: Device type breakdown for charts."""
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    results = db.session.query(
        func.coalesce(PageView.device_type, 'Unknown').label('device'),
        func.count(PageView.id).label('views')
    ).filter(
        PageView.timestamp >= start_date
    ).group_by(
        PageView.device_type
    ).all()
    
    data = {
        'labels': [r.device for r in results],
        'values': [r.views for r in results]
    }
    return jsonify(data)


@analytics_bp.route('/api/funnel/<int:funnel_id>')
@login_required
@role_required('admin')
def funnel_api(funnel_id):
    """API: Funnel data for visualization."""
    funnel = Funnel.query.get_or_404(funnel_id)
    days = request.args.get('days', 30, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    rates = funnel.calculate_conversion_rates(start_date, end_date)
    
    data = {
        'name': funnel.name,
        'steps': [
            {
                'name': r['step'].name,
                'count': r['count'],
                'rate': r['rate'],
                'drop_off': r['drop_off']
            }
            for r in rates
        ]
    }
    return jsonify(data)
