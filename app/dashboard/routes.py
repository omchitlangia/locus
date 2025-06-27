from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user, fresh_login_required
from app.extensions import db
from app.models import FixedCost, Revenue, VariableCost

dash_bp = Blueprint('dashboard', __name__)

@dash_bp.route('/dashboard')
@fresh_login_required
def dashboard():
    # Calculate totals like in dataentry route
    total_revenue = db.session.query(db.func.sum(Revenue.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_fixed = db.session.query(db.func.sum(FixedCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_variable = db.session.query(db.func.sum(VariableCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
    profit = total_revenue - total_fixed - total_variable
    
    return render_template('dashboard.html', profit=profit, user=current_user)

@dash_bp.route('/dashboard/dataentry')
@login_required
def dataentry():
    return redirect(url_for('dataentry.index'))

@dash_bp.route('/dashboard/analytics')
@login_required
def analytics():
    return render_template('dashboard.html', user=current_user)