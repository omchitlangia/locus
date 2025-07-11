from flask import render_template, request, flash
from flask_login import login_required, current_user
from app.extensions import db
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.models import Revenue, VariableCost, RevenuePrediction, User
from sqlalchemy import func, and_
import logging
from . import health_bp

logger = logging.getLogger(__name__)

# Define all possible KPIs with their display names and categories
ALL_KPIS = {
    'automatic': {
        'revenue_growth': 'Revenue Growth',
        'gross_profit_margin': 'Gross Profit Margin', 
        'forecast_accuracy': 'Forecast Accuracy'
    },
    'manual': {
        'customer_retention': 'Customer Retention',
        'marketing_roi': 'Marketing ROI',
        'cac': 'Customer Acquisition Cost',
        'team_efficiency': 'Team Efficiency',
        'user_growth': 'User Growth'
    }
}

@health_bp.route('/dashboard/business_health', methods=['GET', 'POST'])
@login_required
def business_health():
    try:
        # Initialize all KPIs with None
        kpis = {k: None for category in ALL_KPIS.values() for k in category}
        
        # Calculate automatic KPIs from database
        auto_kpis = calculate_automatic_kpis(current_user.id)
        kpis.update(auto_kpis)

        if request.method == 'POST':
            # Process form inputs for manual KPIs
            for kpi in ALL_KPIS['manual']:
                value = request.form.get(kpi, type=float)
                if value is not None:
                    # Apply appropriate capping
                    if kpi == 'cac':
                        kpis[kpi] = min(value, 1000)  # Higher cap for CAC
                    else:
                        kpis[kpi] = min(value, 100)   # Standard 100% cap

        # Calculate health score using only available KPIs
        valid_kpis = {k: v for k, v in kpis.items() if v is not None}
        health_score = min(
            sum(valid_kpis.values()) / len(valid_kpis) if valid_kpis else 0,
            100
        )

        # Update user's health score
        current_user.health_score = health_score
        db.session.commit()

        return render_template(
            'business_health/business_health.html',
            health_score=round(health_score, 2),
            kpis=kpis,
            kpi_categories=ALL_KPIS
        )

    except Exception as e:
        logger.error(f"Error in business_health: {str(e)}", exc_info=True)
        flash('An error occurred while processing your request', 'error')
        return render_template(
            'business_health/business_health.html',
            health_score=0,
            kpis={k: None for category in ALL_KPIS.values() for k in category},
            kpi_categories=ALL_KPIS
        )

def calculate_automatic_kpis(user_id):
    """Calculate KPIs that are automatically derived from database"""
    kpis = {}
    now = datetime.utcnow()
    
    # 1. Revenue Growth Calculation
    current_month_start = datetime(now.year, now.month, 1)
    prev_month_start = (now - relativedelta(months=1)).replace(day=1)
    prev_month_end = current_month_start - timedelta(days=1)

    current_rev = db.session.query(func.sum(Revenue.amount))\
                  .filter_by(user_id=user_id)\
                  .filter(Revenue.timestamp >= current_month_start)\
                  .scalar() or 0
        
    prev_rev = db.session.query(func.sum(Revenue.amount))\
               .filter_by(user_id=user_id)\
               .filter(Revenue.timestamp.between(prev_month_start, prev_month_end))\
               .scalar() or 0

    kpis['revenue_growth'] = 0.0  # Default
    if prev_rev > 0:
        kpis['revenue_growth'] = min(((current_rev - prev_rev) / prev_rev) * 100, 100)
    elif current_rev > 0:
        kpis['revenue_growth'] = 100.0  # Infinite growth case

    # 2. Gross Profit Margin
    variable_costs = db.session.query(func.sum(VariableCost.amount))\
                     .filter_by(user_id=user_id)\
                     .filter(VariableCost.timestamp >= current_month_start)\
                     .scalar() or 0

    if current_rev > 0:
        kpis['gross_profit_margin'] = min(
            ((current_rev - variable_costs) / current_rev) * 100,
            100
        )

    # 3. Forecast Accuracy
    latest_r2 = db.session.query(RevenuePrediction.r_squared)\
                .filter_by(user_id=user_id)\
                .order_by(RevenuePrediction.prediction_date.desc())\
                .first()

    if latest_r2 and latest_r2[0] is not None:
        kpis['forecast_accuracy'] = min(latest_r2[0] * 100, 100)

    return kpis

@health_bp.route('/dashboard/leaderboard')
@login_required
def leaderboard():
    try:
        # Get ALL users with health scores, ordered by score (highest first)
        all_users = User.query.filter(User.health_score.isnot(None))\
                     .order_by(User.health_score.desc())\
                     .all()

        # Calculate ranks with proper tie handling
        ranked_users = []
        current_rank = 1
        
        for i, user in enumerate(all_users):
            # Same rank if same score as previous user
            if i > 0 and user.health_score == all_users[i-1].health_score:
                rank = ranked_users[-1]['rank']
            else:
                rank = i + 1
                current_rank = rank
                
            ranked_users.append({
                'rank': rank,
                'user': user,
                'score': user.health_score
            })

        # Find current user's rank
        user_rank = next(
            (u['rank'] for u in ranked_users if u['user'].id == current_user.id),
            None
        )
        user_score = current_user.health_score

        return render_template(
            'business_health/leaderboard.html',
            top_users=ranked_users[:10],  # Show top 10
            user_rank=user_rank,
            user_score=user_score,
            current_user=current_user,
            total_users=len(all_users)
        )

    except Exception as e:
        logger.error(f"Leaderboard error: {str(e)}", exc_info=True)
        flash('Error loading leaderboard', 'error')
        return render_template(
            'business_health/leaderboard.html',
            top_users=[],
            user_rank=None,
            user_score=current_user.health_score,
            current_user=current_user,
            total_users=0
        )