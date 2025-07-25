from flask import render_template, request, flash
from flask_login import login_required, current_user
from app.extensions import db
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.models import Revenue, VariableCost, RevenuePrediction, User, Achievement, UserAchievement
from sqlalchemy import func
import logging
from app.models import User
from sqlalchemy import desc

from . import health_bp

logger = logging.getLogger(__name__)

# KPI categories with keys
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

def calculate_automatic_kpis(user_id):
    kpis = {}
    now = datetime.utcnow()
    # Revenue Growth: Current month vs previous month revenue
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

    if prev_rev > 0:
        kpis['revenue_growth'] = min(((current_rev - prev_rev) / prev_rev) * 100, 100)
    elif current_rev > 0:
        kpis['revenue_growth'] = 100.0
    else:
        kpis['revenue_growth'] = None

    # Gross Profit Margin: (Revenue - Variable Costs) / Revenue * 100
    variable_costs = db.session.query(func.sum(VariableCost.amount))\
        .filter_by(user_id=user_id)\
        .filter(VariableCost.timestamp >= current_month_start)\
        .scalar() or 0

    if current_rev > 0:
        kpis['gross_profit_margin'] = min(((current_rev - variable_costs) / current_rev) * 100, 100)
    else:
        kpis['gross_profit_margin'] = None

    # Forecast Accuracy: latest r_squared from RevenuePrediction
    latest_r2 = db.session.query(RevenuePrediction.r_squared)\
        .filter_by(user_id=user_id)\
        .order_by(RevenuePrediction.prediction_date.desc())\
        .first()

    if latest_r2 and latest_r2[0] is not None:
        kpis['forecast_accuracy'] = min(latest_r2[0] * 100, 100)
    else:
        kpis['forecast_accuracy'] = None

    return kpis

def unlock_health_score_achievements(score):
    all_thresholds = [
        (75, 'health_score_75'),
        (90, 'health_score_90'),
        (100, 'health_score_100')
    ]
    for threshold, action in all_thresholds:
        achievement = Achievement.query.filter_by(required_action=action).first()
        if not achievement:
            continue
        user_achievement = UserAchievement.query.filter_by(
            user_id=current_user.id,
            achievement_id=achievement.id
        ).first()

        if score >= threshold:
            if not user_achievement:
                user_achievement = UserAchievement(
                    user_id=current_user.id,
                    achievement_id=achievement.id,
                    progress=1,
                    unlocked_at=datetime.utcnow()
                )
                db.session.add(user_achievement)
            elif user_achievement.unlocked_at is None:
                user_achievement.progress = 1
                user_achievement.unlocked_at = datetime.utcnow()
        else:
            # Calculate progress towards achievement if not unlocked
            prev_threshold = next((t for t in reversed(all_thresholds) if t[0] < threshold), (0, None))
            progress = min(max((score - prev_threshold[0]) / (threshold - prev_threshold[0]), 0), 1)
            if not user_achievement:
                user_achievement = UserAchievement(
                    user_id=current_user.id,
                    achievement_id=achievement.id,
                    progress=progress,
                    unlocked_at=None
                )
                db.session.add(user_achievement)
            elif user_achievement.unlocked_at is None:
                user_achievement.progress = progress
    db.session.commit()

@health_bp.route('/dashboard/business_health', methods=['GET', 'POST'])
@login_required
def business_health():
    try:
        kpis = {k: None for category in ALL_KPIS.values() for k in category}
        auto_kpis = calculate_automatic_kpis(current_user.id)
        kpis.update(auto_kpis)

        if request.method == 'POST':
            # Update manual KPIs from form inputs
            for kpi in ALL_KPIS['manual']:
                value = request.form.get(kpi, type=float)
                if value is not None:
                    if kpi == 'cac':
                        kpis[kpi] = min(value, 1000)  # CAC capped at 1000
                    else:
                        kpis[kpi] = min(value, 100)   # Others capped at 100

            # Combine all valid KPIs (auto + manual) for health score calculation
            valid_kpis = {k: v for k, v in kpis.items() if v is not None}
            health_score = round(min(
                sum(valid_kpis.values()) / len(valid_kpis) if valid_kpis else 0,
                100
            ), 2)

            # Update the current user's health score in DB
            current_user.health_score = health_score
            db.session.commit()

            # Unlock achievements based on health score thresholds
            unlock_health_score_achievements(health_score)

            flash('Business health score updated successfully!', 'success')
        else:
            health_score = current_user.health_score or 0

        # --- Leaderboard calculation (unchanged) ---
        # Get all users with health scores ordered descending
        all_users = User.query.filter(User.health_score.isnot(None)).order_by(User.health_score.desc()).all()
        
        ranked_users = []
        for i, user in enumerate(all_users):
            if i > 0 and user.health_score == all_users[i-1].health_score:
                rank = ranked_users[-1]['rank']
            else:
                rank = i + 1
            ranked_users.append({'rank': rank, 'user': user, 'score': user.health_score})
        
        # Current user's rank
        user_rank = next((u['rank'] for u in ranked_users if u['user'].id == current_user.id), None)
        user_score = current_user.health_score or 0

        return render_template(
            'business_health/business_health.html',
            health_score=health_score,
            kpis=kpis,
            kpi_categories=ALL_KPIS,
            top_users=ranked_users[:10],  # Optional: pass top 10 users for leaderboard display
            user_rank=user_rank,
            user_score=user_score,
            current_user=current_user,
            total_users=len(all_users)
        )

    except Exception as e:
        logger.error(f"Error in business_health route: {e}", exc_info=True)
        flash('An error occurred while processing your request.', 'error')
        # Fallback render with default zeroes
        return render_template(
            'business_health/business_health.html',
            health_score=0,
            kpis={k: None for category in ALL_KPIS.values() for k in category},
            kpi_categories=ALL_KPIS,
            top_users=[],
            user_rank=None,
            user_score=0,
            current_user=current_user,
            total_users=0
        )
@health_bp.route('/dashboard/business_health/leaderboard')
@login_required
def leaderboard():
    # Query all users with a non-null health score, ordered descending
    users = User.query.filter(User.health_score.isnot(None)).order_by(desc(User.health_score)).all()
    
    ranked_users = []
    last_score = None
    last_rank = 0
    num_same_rank = 0
    
    for idx, user in enumerate(users, start=1):
        if user.health_score == last_score:
            # Same score as previous => same rank
            rank = last_rank
            num_same_rank += 1
        else:
            # New distinct score, rank increases by previous tie count + 1
            rank = last_rank + num_same_rank + 1
            last_rank = rank
            last_score = user.health_score
            num_same_rank = 0
        
        ranked_users.append({
            'rank': rank,
            'user': user,
            'score': user.health_score
        })
    
    return render_template('business_health/leaderboard.html', top_users=ranked_users)