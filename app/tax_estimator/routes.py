from flask import render_template
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Revenue, FixedCost, VariableCost
from . import tax_bp
from sqlalchemy import func

@tax_bp.route('/dashboard/tax-estimator', methods=['GET'])
@login_required
def tax_estimator():
    # Fetch totals from dataentry
    total_revenue = db.session.query(func.sum(Revenue.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_fixed = db.session.query(func.sum(FixedCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_variable = db.session.query(func.sum(VariableCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_expense = total_fixed + total_variable

    return render_template('tax_estimator/estimator.html',
                           total_revenue=round(total_revenue, 2),
                           total_expense=round(total_expense, 2))
