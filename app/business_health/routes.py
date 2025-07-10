from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np
from statsmodels.tsa.api import ExponentialSmoothing
from sklearn.metrics import r2_score
from . import health_bp
from app.models import Revenue, FixedCost, VariableCost, RevenuePrediction
from sqlalchemy import func, and_
import logging

logger = logging.getLogger(__name__)

@health_bp.route('/dashboard/business_health', methods=['GET', 'POST'])
@login_required
def business_health():
    if request.method == 'POST':
        try:
            user_inputs = {
                'customer_retention': min(float(request.form.get('customer_retention', 0)), 100),  # Capped at 100
                'marketing_roi': min(float(request.form.get('marketing_roi', 0)), 100),          # Capped at 100
                'cac': min(float(request.form.get('cac', 0)), 100),                              # Capped at 100
                'team_efficiency': min(float(request.form.get('team_efficiency', 0)), 100),      # Capped at 100
                'user_growth': min(float(request.form.get('user_growth', 0)), 100)               # Capped at 100
            }
            
            kpis = calculate_kpis_from_db(current_user.id)
            
            # Update with user inputs (only positive values)
            for k, v in user_inputs.items():
                if v >= 0:
                    kpis[k] = v if k != 'cac' else min(v, 1000)  # Cap CAC at 1000
            
            # Apply capping to all KPIs at 100
            for k in kpis:
                if isinstance(kpis[k], (int, float)):
                    kpis[k] = min(kpis[k], 100)
            
            valid_kpis = {k: v for k, v in kpis.items() if v is not None and v >= 0}
            health_score = min(sum(valid_kpis.values()) / len(valid_kpis) if valid_kpis else 0, 100)  # Capped at 100
            
            return render_template('/business_health/business_health.html',
                                health_score=round(health_score, 2),
                                kpis=kpis)
            
        except Exception as e:
            logger.error(f"Error calculating health score: {str(e)}", exc_info=True)
            flash(f'Error calculating health score: {str(e)}', 'error')
            return redirect(url_for('.business_health'))
    
    try:
        kpis = calculate_kpis_from_db(current_user.id)
        # Apply capping to all KPIs at 100
        for k in kpis:
            if isinstance(kpis[k], (int, float)):
                kpis[k] = min(kpis[k], 100)
        
        valid_kpis = {k: v for k, v in kpis.items() if v is not None and v >= 0}
        health_score = min(sum(valid_kpis.values()) / len(valid_kpis) if valid_kpis else 0, 100)  # Capped at 100
        
        return render_template('/business_health/business_health.html',
                            health_score=round(health_score, 2),
                            kpis=kpis)
    except Exception as e:
        logger.error(f"Error calculating health score: {str(e)}", exc_info=True)
        flash(f'Error calculating health score: {str(e)}', 'error')
        return render_template('/business_health/business_health.html',
                            health_score=0,
                            kpis={})

def get_current_month_revenue(user_id):
    """Get revenue for current calendar month"""
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    return db.session.query(func.sum(Revenue.amount))\
                   .filter_by(user_id=user_id)\
                   .filter(Revenue.timestamp >= month_start)\
                   .scalar() or 0

def calculate_kpis_from_db(user_id):
    """Calculate all KPIs from database with proper month boundaries"""
    kpis = {
        'revenue_growth': None,
        'gross_profit_margin': None,
        'forecast_accuracy': None,
        'customer_retention': None,
        'marketing_roi': None,
        'cac': None,
        'team_efficiency': None,
        'user_growth': None,
        'opex_ratio': None,
    }
    
    now = datetime.utcnow()
    current_month_start = datetime(now.year, now.month, 1)
    prev_month = (now - relativedelta(months=1))
    prev_month_start = datetime(prev_month.year, prev_month.month, 1)
    prev_month_end = current_month_start - timedelta(days=1)
    
    # 1. Revenue Growth Rate (Month-over-Month)
    current_rev = db.session.query(func.sum(Revenue.amount))\
                      .filter_by(user_id=user_id)\
                      .filter(Revenue.timestamp >= current_month_start)\
                      .scalar() or 0
    
    prev_rev = db.session.query(func.sum(Revenue.amount))\
                   .filter_by(user_id=user_id)\
                   .filter(and_(
                       Revenue.timestamp >= prev_month_start,
                       Revenue.timestamp <= prev_month_end))\
                   .scalar() or 0
    
    if prev_rev > 0:
        growth = ((current_rev - prev_rev) / prev_rev) * 100
        kpis['revenue_growth'] = min(round(growth, 2), 100)  # Capped at 100
    elif prev_rev == 0 and current_rev > 0:
        kpis['revenue_growth'] = 100  # Instead of ∞, cap at 100
    else:
        kpis['revenue_growth'] = 0.0
    
    # 2. Gross Profit Margin (using calendar month)
    variable_costs = db.session.query(func.sum(VariableCost.amount))\
                         .filter_by(user_id=user_id)\
                         .filter(VariableCost.timestamp >= current_month_start)\
                         .scalar() or 0
    
    if current_rev > 0:
        gross_profit = (current_rev - variable_costs) / current_rev * 100
        kpis['gross_profit_margin'] = min(round(max(gross_profit, 0), 2), 100)  # Capped at 100
    
    # 5. Forecast Accuracy
    latest_r2 = db.session.query(RevenuePrediction.r_squared)\
                    .filter_by(user_id=user_id)\
                    .filter(RevenuePrediction.r_squared.isnot(None))\
                    .order_by(RevenuePrediction.prediction_date.desc())\
                    .first()
    
    if latest_r2:
        kpis['forecast_accuracy'] = min(round(max(0, min(100, latest_r2[0] * 100)), 2), 100)  # Capped at 100
    
    return kpis