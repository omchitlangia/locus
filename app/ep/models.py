from datetime import datetime
from app.extensions import db
from flask_login import current_user

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50), nullable=False)  # 'business' or 'personal'
    category = db.Column(db.String(50))  # 'sales', 'hiring', 'expansion', etc.
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(50))  # 'daily', 'weekly', 'monthly', 'yearly'
    
    # Cost fields
    marketing_cost = db.Column(db.Float, default=0)
    logistics_cost = db.Column(db.Float, default=0)
    hiring_cost = db.Column(db.Float, default=0)
    other_cost = db.Column(db.Float, default=0)
    
    # Revenue impact estimation
    expected_revenue_boost = db.Column(db.Float, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='events')
    
    @property
    def total_cost(self):
        return self.marketing_cost + self.logistics_cost + self.hiring_cost + self.other_cost
    
    @property
    def net_impact(self):
        return self.expected_revenue_boost - self.total_cost