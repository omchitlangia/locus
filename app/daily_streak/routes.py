from flask import render_template
from flask_login import login_required, current_user
from datetime import date, timedelta
from app.extensions import db
from app.models import DailyStreak
from . import streak_bp

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

@streak_bp.route('/dashboard/streak')
@login_required
def show_streak():
    streak_count = update_streak_for_user(current_user.id)
    badge = None
    if streak_count >= 30:
        badge = '🔥 Streak Master (30+)'
    elif streak_count >= 10:
        badge = '⚡ Streak Pro (10+)'
    elif streak_count >= 5:
        badge = '⭐ Streak Starter (5+)'
    icon = "🔥" if streak_count >= 1 else ""
    return render_template(
        'daily_streak/streak.html',
        streak_count=streak_count,
        badge=badge,
        icon=icon
    )
