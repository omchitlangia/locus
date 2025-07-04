from datetime import datetime
from app.extensions import db, login_manager
from flask_login import UserMixin

class SKU(db.Model):
    __tablename__ = 'sku'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    cost_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))
    expiry_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"SKU('{self.code}', '{self.name}')"

    def is_expired(self):
        return self.expiry_date and self.expiry_date < datetime.now().date()

    def is_available(self):
        return self.quantity > 0 and not self.is_expired()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.email_verified

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Revenue(db.Model):
    __tablename__ = 'revenue'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'))
    
    user = db.relationship('User', backref='revenues')
    bill = db.relationship('Bill', backref='revenue_entries')

class FixedCost(db.Model):
    __tablename__ = 'fixed_cost'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'))
    
    user = db.relationship('User', backref='fixed_costs')

class VariableCost(db.Model):
    __tablename__ = 'variable_cost'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'))
    
    user = db.relationship('User', backref='variable_costs')
    bill = db.relationship('Bill', backref='variable_cost_entries')

class Event(db.Model):
    __tablename__ = 'event'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(50))
    marketing_cost = db.Column(db.Float, default=0)
    logistics_cost = db.Column(db.Float, default=0)
    hiring_cost = db.Column(db.Float, default=0)
    other_cost = db.Column(db.Float, default=0)
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

class BillingItem(db.Model):
    __tablename__ = 'billing_item'
    
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    sku_id = db.Column(db.Integer, db.ForeignKey('sku.id'), nullable=False)
    sku_code = db.Column(db.String(20), nullable=False)
    sku_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    expiry_date = db.Column(db.Date)
    
    sku = db.relationship('SKU', backref='billing_items')
    bill = db.relationship('Bill', backref='items')

    def __repr__(self):
        return f'<BillingItem {self.sku_code} x{self.quantity}>'

class Bill(db.Model):
    __tablename__ = 'bill'
    
    id = db.Column(db.Integer, primary_key=True)
    bill_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    discount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    grand_total = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), default='Cash')
    payment_status = db.Column(db.String(20), default='paid')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', backref='bills')

    def __repr__(self):
        return f'<Bill {self.bill_number}>'