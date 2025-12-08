import json
from datetime import datetime
from app.models import User, ContactFormSubmission, Order, Appointment
from app.database import db

def collect_user_data(email=None, user_id=None):
    """
    Collects all data associated with a user by email or user_id.
    Returns a dictionary of data.
    """
    data = {}
    
    user = None
    if user_id:
        user = User.query.get(user_id)
        if user and not email:
            email = user.email
    elif email:
        user = User.query.filter_by(email=email).first()
        
    if user:
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'roles': [role.name for role in user.roles],
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None
        }
        
    if email:
        # Contact Submissions
        submissions = ContactFormSubmission.query.filter_by(email=email).all()
        data['contact_submissions'] = [{
            'id': s.id,
            'first_name': s.first_name,
            'last_name': s.last_name,
            'message': s.message,
            'submitted_at': s.submitted_at.isoformat() if s.submitted_at else None
        } for s in submissions]
        
        # Appointments
        appointments = Appointment.query.filter_by(email=email).all()
        data['appointments'] = [{
            'id': a.id,
            'date': a.preferred_date_time.isoformat() if a.preferred_date_time else None,
            'service': a.service.name if a.service else None,
            'status': a.status
        } for a in appointments]
        
        # Orders (by email or user_id if we have it)
        orders_query = Order.query.filter((Order.email == email))
        if user:
             orders_query = orders_query.union(Order.query.filter(Order.user_id == user.id))
             
        orders = orders_query.all()
        data['orders'] = [{
            'id': o.id,
            'total': o.total_amount,
            'status': o.status,
            'created_at': o.created_at.isoformat() if o.created_at else None,
            'items': [{
                'product': i.product.name,
                'quantity': i.quantity,
                'price': i.price_at_purchase
            } for i in o.items]
        } for o in orders]

    return data

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
