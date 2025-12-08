"""
Phase 27: AI & Business Intelligence Module

ML-based analytics including lead scoring, churn prediction, and forecasting.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pickle
import os

from flask import Flask, current_app


class LeadScorer:
    """
    Machine learning-based lead scoring.
    
    Scores leads based on behavior and demographic data.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.model = None
        self.feature_weights = {
            'email_domain_corporate': 10,
            'has_phone': 5,
            'message_length': 0.01,
            'page_views': 2,
            'time_on_site': 0.1,
            'return_visits': 5,
            'form_completeness': 15,
            'requested_demo': 20,
            'downloaded_resource': 10,
        }
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
        self._load_model()
    
    def _load_model(self):
        """Load trained model if available."""
        model_path = os.path.join(
            current_app.instance_path if current_app else '.',
            'models',
            'lead_scorer.pkl'
        )
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
            except Exception:
                pass
    
    def score_lead(self, lead_data: Dict) -> Dict[str, Any]:
        """
        Calculate lead score.
        
        Args:
            lead_data: Dict containing lead information
        
        Returns:
            Dict with score and breakdown
        """
        score = 0
        breakdown = {}
        
        # Email domain scoring
        email = lead_data.get('email', '')
        if '@' in email:
            domain = email.split('@')[1].lower()
            free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
            if domain not in free_domains:
                breakdown['corporate_email'] = self.feature_weights['email_domain_corporate']
                score += self.feature_weights['email_domain_corporate']
        
        # Phone number
        if lead_data.get('phone'):
            breakdown['has_phone'] = self.feature_weights['has_phone']
            score += self.feature_weights['has_phone']
        
        # Message length (engagement indicator)
        message = lead_data.get('message', '')
        if len(message) > 50:
            msg_score = min(10, len(message) * self.feature_weights['message_length'])
            breakdown['message_engagement'] = round(msg_score, 1)
            score += msg_score
        
        # Behavioral data
        page_views = lead_data.get('page_views', 0)
        if page_views > 0:
            pv_score = min(20, page_views * self.feature_weights['page_views'])
            breakdown['page_views'] = round(pv_score, 1)
            score += pv_score
        
        # Form completeness
        fields_filled = sum(1 for v in lead_data.values() if v)
        total_fields = len(lead_data)
        if total_fields > 0:
            completeness = (fields_filled / total_fields) * self.feature_weights['form_completeness']
            breakdown['form_completeness'] = round(completeness, 1)
            score += completeness
        
        # Demo request (high intent)
        if lead_data.get('requested_demo') or 'demo' in message.lower():
            breakdown['demo_request'] = self.feature_weights['requested_demo']
            score += self.feature_weights['requested_demo']
        
        # Normalize score to 0-100
        final_score = min(100, max(0, score))
        
        # Determine grade
        if final_score >= 80:
            grade = 'A'
        elif final_score >= 60:
            grade = 'B'
        elif final_score >= 40:
            grade = 'C'
        elif final_score >= 20:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': round(final_score, 1),
            'grade': grade,
            'breakdown': breakdown,
            'recommendation': self._get_recommendation(final_score, breakdown),
        }
    
    def _get_recommendation(self, score: float, breakdown: Dict) -> str:
        """Generate action recommendation based on score."""
        if score >= 80:
            return "Hot lead - contact immediately via phone"
        elif score >= 60:
            return "Qualified lead - send personalized follow-up"
        elif score >= 40:
            return "Warm lead - add to nurture sequence"
        elif score >= 20:
            return "Cold lead - add to general newsletter"
        else:
            return "Low priority - monitor for future engagement"
    
    def batch_score_leads(self, leads: List[Dict]) -> List[Dict]:
        """Score multiple leads at once."""
        return [self.score_lead(lead) for lead in leads]


class ChurnPredictor:
    """
    Predict customer churn risk based on behavior patterns.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.risk_weights = {
            'days_since_last_order': 0.5,
            'days_since_login': 0.3,
            'order_frequency_decline': 0.4,
            'support_tickets': 0.2,
            'negative_feedback': 0.5,
            'subscription_near_expiry': 0.3,
        }
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
    
    def predict_churn(self, customer_data: Dict) -> Dict[str, Any]:
        """
        Predict churn probability for a customer.
        
        Args:
            customer_data: Dict containing customer behavior data
        
        Returns:
            Dict with churn probability and risk factors
        """
        risk_score = 0
        risk_factors = []
        
        # Days since last order
        days_since_order = customer_data.get('days_since_last_order', 0)
        if days_since_order > 90:
            factor_score = min(30, days_since_order * 0.2)
            risk_score += factor_score
            risk_factors.append({
                'factor': 'No recent orders',
                'detail': f'{days_since_order} days since last order',
                'score': round(factor_score, 1),
            })
        
        # Days since login
        days_since_login = customer_data.get('days_since_login', 0)
        if days_since_login > 30:
            factor_score = min(25, days_since_login * 0.3)
            risk_score += factor_score
            risk_factors.append({
                'factor': 'Low login activity',
                'detail': f'{days_since_login} days since last login',
                'score': round(factor_score, 1),
            })
        
        # Order frequency decline
        current_frequency = customer_data.get('current_order_frequency', 0)
        previous_frequency = customer_data.get('previous_order_frequency', 0)
        if previous_frequency > 0:
            decline = (previous_frequency - current_frequency) / previous_frequency
            if decline > 0.3:
                factor_score = decline * 30
                risk_score += factor_score
                risk_factors.append({
                    'factor': 'Decreasing order frequency',
                    'detail': f'{int(decline * 100)}% decline in orders',
                    'score': round(factor_score, 1),
                })
        
        # Support tickets
        open_tickets = customer_data.get('open_support_tickets', 0)
        if open_tickets > 0:
            factor_score = open_tickets * 5
            risk_score += factor_score
            risk_factors.append({
                'factor': 'Unresolved support issues',
                'detail': f'{open_tickets} open tickets',
                'score': round(factor_score, 1),
            })
        
        # Negative feedback
        negative_reviews = customer_data.get('negative_reviews', 0)
        if negative_reviews > 0:
            factor_score = negative_reviews * 10
            risk_score += factor_score
            risk_factors.append({
                'factor': 'Negative feedback',
                'detail': f'{negative_reviews} negative reviews',
                'score': round(factor_score, 1),
            })
        
        # Normalize to probability
        churn_probability = min(1.0, risk_score / 100)
        
        # Determine risk level
        if churn_probability >= 0.7:
            risk_level = 'high'
        elif churn_probability >= 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'churn_probability': round(churn_probability, 3),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'retention_recommendations': self._get_retention_actions(risk_level, risk_factors),
        }
    
    def _get_retention_actions(self, risk_level: str, factors: List) -> List[str]:
        """Generate retention action recommendations."""
        actions = []
        
        if risk_level == 'high':
            actions.append("Immediate personal outreach from account manager")
            actions.append("Offer exclusive discount or loyalty reward")
        
        for factor in factors:
            if 'support' in factor['factor'].lower():
                actions.append("Prioritize resolution of open support tickets")
            if 'order' in factor['factor'].lower():
                actions.append("Send personalized product recommendations")
            if 'login' in factor['factor'].lower():
                actions.append("Send re-engagement email with new features")
        
        return actions


class RevenueForecaster:
    """
    Time-series based revenue forecasting.
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
    
    def forecast_revenue(self, historical_data: List[Dict], 
                        periods: int = 12) -> Dict[str, Any]:
        """
        Forecast future revenue based on historical data.
        
        Args:
            historical_data: List of {date, revenue} dictionaries
            periods: Number of future periods to forecast
        
        Returns:
            Dict with forecast and confidence intervals
        """
        if len(historical_data) < 3:
            return {'error': 'Insufficient historical data'}
        
        # Extract values
        revenues = [d['revenue'] for d in historical_data]
        
        # Simple moving average forecast
        window = min(3, len(revenues))
        moving_avg = sum(revenues[-window:]) / window
        
        # Calculate trend
        if len(revenues) >= 6:
            first_half = sum(revenues[:len(revenues)//2]) / (len(revenues)//2)
            second_half = sum(revenues[len(revenues)//2:]) / (len(revenues) - len(revenues)//2)
            trend = (second_half - first_half) / first_half if first_half > 0 else 0
        else:
            trend = 0
        
        # Calculate seasonality (simple approach)
        if len(revenues) >= 12:
            seasonal_factors = self._calculate_seasonality(revenues)
        else:
            seasonal_factors = [1.0] * 12
        
        # Generate forecast
        forecasts = []
        current_base = moving_avg
        last_date = datetime.fromisoformat(historical_data[-1]['date'])
        
        for i in range(periods):
            forecast_date = last_date + timedelta(days=30 * (i + 1))
            month = forecast_date.month - 1
            
            # Apply trend and seasonality
            forecast_value = current_base * (1 + trend) * seasonal_factors[month]
            current_base = forecast_value
            
            # Calculate confidence interval (simplified)
            std_dev = self._calculate_std_dev(revenues)
            confidence_width = std_dev * 1.96  # 95% confidence
            
            forecasts.append({
                'date': forecast_date.isoformat()[:10],
                'revenue': round(forecast_value, 2),
                'lower_bound': round(max(0, forecast_value - confidence_width), 2),
                'upper_bound': round(forecast_value + confidence_width, 2),
            })
        
        return {
            'forecasts': forecasts,
            'trend': round(trend * 100, 1),  # As percentage
            'confidence_level': 0.95,
            'method': 'Moving Average with Trend',
            'total_forecast': round(sum(f['revenue'] for f in forecasts), 2),
        }
    
    def _calculate_seasonality(self, revenues: List[float]) -> List[float]:
        """Calculate monthly seasonality factors."""
        # Group by month equivalent (assuming monthly data)
        monthly_avg = sum(revenues) / len(revenues)
        factors = []
        
        for i in range(12):
            month_values = [revenues[j] for j in range(i, len(revenues), 12)]
            if month_values:
                month_avg = sum(month_values) / len(month_values)
                factors.append(month_avg / monthly_avg if monthly_avg > 0 else 1.0)
            else:
                factors.append(1.0)
        
        return factors
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5


class AnomalyDetector:
    """
    Detect anomalies in business metrics.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.sensitivity = 2.0  # Standard deviations for anomaly
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app
        self.sensitivity = app.config.get('ANOMALY_SENSITIVITY', 2.0)
    
    def detect_anomalies(self, data: List[Dict], 
                        value_field: str = 'value') -> List[Dict]:
        """
        Detect anomalies in time series data.
        
        Args:
            data: List of {date, value} dictionaries
            value_field: Name of the value field
        
        Returns:
            List of detected anomalies
        """
        if len(data) < 5:
            return []
        
        values = [d[value_field] for d in data]
        
        # Calculate statistics
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Detect anomalies
        anomalies = []
        threshold = self.sensitivity * std_dev
        
        for i, item in enumerate(data):
            value = item[value_field]
            deviation = abs(value - mean)
            
            if deviation > threshold:
                z_score = (value - mean) / std_dev if std_dev > 0 else 0
                
                anomalies.append({
                    'date': item.get('date'),
                    'value': value,
                    'expected': round(mean, 2),
                    'deviation': round(deviation, 2),
                    'z_score': round(z_score, 2),
                    'type': 'spike' if value > mean else 'dip',
                    'severity': 'high' if abs(z_score) > 3 else 'medium',
                })
        
        return anomalies
    
    def monitor_metrics(self, metrics: Dict[str, List[Dict]]) -> Dict[str, List]:
        """
        Monitor multiple metrics for anomalies.
        
        Args:
            metrics: Dict of metric_name -> data list
        
        Returns:
            Dict of metric_name -> anomalies list
        """
        results = {}
        
        for metric_name, data in metrics.items():
            anomalies = self.detect_anomalies(data)
            if anomalies:
                results[metric_name] = anomalies
        
        return results


class BusinessIntelligence:
    """
    High-level business intelligence orchestration.
    """
    
    def __init__(self, app=None):
        self.lead_scorer = LeadScorer()
        self.churn_predictor = ChurnPredictor()
        self.revenue_forecaster = RevenueForecaster()
        self.anomaly_detector = AnomalyDetector()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize all components with Flask app."""
        self.lead_scorer.init_app(app)
        self.churn_predictor.init_app(app)
        self.revenue_forecaster.init_app(app)
        self.anomaly_detector.init_app(app)
    
    def get_dashboard_insights(self) -> Dict[str, Any]:
        """
        Generate insights for the admin dashboard.
        """
        from app.models import ContactFormSubmission, Order, User
        from datetime import datetime, timedelta
        
        insights = {
            'lead_insights': {},
            'revenue_insights': {},
            'customer_insights': {},
            'anomalies': [],
        }
        
        # Get recent leads and score them
        recent_leads = ContactFormSubmission.query.filter(
            ContactFormSubmission.submitted_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        if recent_leads:
            scores = [self.lead_scorer.score_lead({
                'email': lead.email,
                'phone': lead.phone,
                'message': lead.message or '',
            }) for lead in recent_leads]
            
            insights['lead_insights'] = {
                'total': len(scores),
                'average_score': round(sum(s['score'] for s in scores) / len(scores), 1),
                'hot_leads': len([s for s in scores if s['grade'] == 'A']),
                'qualified_leads': len([s for s in scores if s['grade'] in ['A', 'B']]),
            }
        
        return insights


# Global instances
lead_scorer = LeadScorer()
churn_predictor = ChurnPredictor()
revenue_forecaster = RevenueForecaster()
anomaly_detector = AnomalyDetector()
business_intelligence = BusinessIntelligence()
