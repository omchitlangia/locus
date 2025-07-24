from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user, fresh_login_required
from app.extensions import db
from datetime import date, timedelta
from app.models import FixedCost, Revenue, VariableCost, DailyStreak, Achievement, UserAchievement, User
from sqlalchemy import and_, func

dash_bp = Blueprint('dashboard', __name__)

def update_streak_for_user(user_id):
    today = date.today()
    entry = DailyStreak.query.filter_by(user_id=user_id).first()
    if entry:
        if entry.last_active_date == today:
            return entry.current_streak
        if entry.last_active_date == today - timedelta(days=1):
            entry.current_streak += 1
        else:
            entry.current_streak = 1
        entry.last_active_date = today
    else:
        entry = DailyStreak(user_id=user_id, current_streak=1, last_active_date=today)
        db.session.add(entry)
    db.session.commit()
    return entry.current_streak

@dash_bp.route('/dashboard')
@fresh_login_required
def dashboard():
    # Calculate totals like in dataentry route
    total_revenue = db.session.query(db.func.sum(Revenue.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_fixed = db.session.query(db.func.sum(FixedCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_variable = db.session.query(db.func.sum(VariableCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
    profit = total_revenue - total_fixed - total_variable

    streak_count = update_streak_for_user(current_user.id)

    # Get all users ordered by health_score (highest first)
    all_users = User.query.filter(User.health_score.isnot(None)) \
        .order_by(User.health_score.desc()).all()

    # Calculate ranks (handle ties, same as in leaderboard route)
    ranked_users = []
    for i, user in enumerate(all_users):
        if i > 0 and user.health_score == all_users[i-1].health_score:
            rank = ranked_users[-1]['rank']
        else:
            rank = i + 1
        ranked_users.append({'rank': rank, 'user': user, 'score': user.health_score})

    # Find current user's rank
    user_rank = next(
        (u['rank'] for u in ranked_users if u['user'].id == current_user.id),
        None
    )

    # Fetch all achievements for the default set
    DEFAULT_ACHIEVEMENTS_NAMES = [  # Keep names in sync with your DEFAULT_ACHIEVEMENTS
        'Starting Sales', 'Busy Cashier', 'Thriving Trade',
        'Health Conscious', 'Peak Performer', 'Perfect Score',
        'Rising Analyst', 'Seasoned Forecaster', 'Master Tracker',
        'Elite Entrepreneur', 'Total Tycoon', 'Keeping Tabs',
        'Budding Business', 'Healthy Stock', 'Chasing Profits'
    ]

    # Get all achievement entries joined with progress and "unlocked" info
    achievements_query = (
        db.session.query(
            Achievement,
            func.coalesce(UserAchievement.progress, 0).label('progress'),
            UserAchievement.unlocked_at,
            (func.coalesce(UserAchievement.progress, 0) >= Achievement.required_count)
        )
        .outerjoin(
            UserAchievement,
            and_(
                UserAchievement.achievement_id == Achievement.id,
                UserAchievement.user_id == current_user.id
            )
        )
        .filter(Achievement.name.in_(DEFAULT_ACHIEVEMENTS_NAMES))
    )

    # Count unlocked achievements
    achievements_unlocked = sum(
        1 for _, _, _, is_unlocked in achievements_query if is_unlocked
    )

    return render_template('dashboard.html', profit=profit,
        user=current_user, 
        streak_count=streak_count,
        achievements_unlocked=achievements_unlocked,
        user_rank=user_rank)

@dash_bp.route('/dashboard/dataentry')
@login_required
def dataentry():
    return redirect(url_for('dataentry.index'))