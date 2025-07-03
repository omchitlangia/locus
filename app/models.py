from datetime import datetime
from app.extensions import db, login_manager
from flask_login import UserMixin

class User(db.Model, UserMixin):  # Add UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.email_verified  # Only allow verified users

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Revenue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='revenues')

class FixedCost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='fixed_costs')

class VariableCost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='variable_costs')

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