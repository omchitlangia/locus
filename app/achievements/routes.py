from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.achievements import bp
from app.models import Achievement, UserAchievement
from datetime import datetime
from sqlalchemy import func, and_

DEFAULT_ACHIEVEMENTS = [
    {
        'name': 'Starting Sales',
        'description': 'Generate 5 bills',
        'icon_class': 'pixel-icon-receipt',
        'required_action': 'fifth_bill',
        'required_count': 5
    },
    {
        'name': 'Busy Cashier',
        'description': 'Generate 15 bills',
        'icon_class': 'pixel-icon-receipt',
        'required_action': 'fifteenth_bill',
        'required_count': 15
    },
    {
        'name': 'Thriving Trade',
        'description': 'Generate 30 bills',
        'icon_class': 'pixel-icon-receipt',
        'required_action': 'thirtieth_bill',
        'required_count': 30
    }, 
    {
        'name': 'Health Conscious',
        'description': 'Achieve a Business Health Score above 75',
        'icon_class': 'pixel-icon-heart',
        'required_action': 'health_score_75',
        'required_count': 1
    },
    {
        'name': 'Peak Performer',
        'description': 'Achieve a Business Health Score above 90',
        'icon_class': 'pixel-icon-heart',
        'required_action': 'health_score_90',
        'required_count': 1
    },
    {
        'name': 'Perfect Score',
        'description': 'Achieve a Business Health Score of 100',
        'icon_class': 'pixel-icon-heart',
        'required_action': 'health_score_100',
        'required_count': 1
    },   
    {
        'name': 'Rising Analyst',
        'description': 'Complete 5 forecasts',
        'icon_class': 'pixel-icon-chart',
        'required_action': 'fifth_forecast',
        'required_count': 5
    },
    {
        'name': 'Seasoned Forecaster',
        'description': 'Complete 15 forecasts',
        'icon_class': 'pixel-icon-chart',
        'required_action': 'fifteenth_forecast',
        'required_count': 15
    },
    {
        'name': 'Master Tracker',
        'description': 'Complete 30 forecasts',
        'icon_class': 'pixel-icon-chart',
        'required_action': 'thirtieth_forecast',
        'required_count': 30
    },
    {
        'name': 'Elite Entrepreneur',
        'description': 'Reach ₹100,000 in total revenue',
        'icon_class': 'pixel-icon-trophy',
        'required_action': '100k_earned',
        'required_count': 100000
    },
    {
        'name': 'Total Tycoon',
        'description': 'Reach ₹1,000,000 in total revenue',
        'icon_class': 'pixel-icon-trophy',
        'required_action': '1mil_earned',
        'required_count': 1000000
    },
    {
        'name': 'Keeping Tabs',
        'description': 'Enter your first set of data',
        'icon_class': 'pixel-icon-upload',
        'required_action': 'first_data_entry',
        'required_count': 1
    },
    {
        'name': 'Budding Business',
        'description': 'Enter 5 SKUs into the system',
        'icon_class': 'pixel-icon-database',
        'required_action': 'fifth_sku',
        'required_count': 5
    },
    {
        'name': 'Healthy Stock',
        'description': 'Enter 15 SKUs into the system',
        'icon_class': 'pixel-icon-database',
        'required_action': 'fifteenth_sku',
        'required_count': 15
    },
    {
        'name': 'Chasing Profits',
        'description': 'Enter 30 SKUs into the system',
        'icon_class': 'pixel-icon-database',
        'required_action': 'thirtieth_sku',
        'required_count': 30
    }
]

def init_achievements():
    """Ensure default achievements exist and are up-to-date"""
    existing_achievements = {a.name: a for a in Achievement.query.all()}

    for achievement_data in DEFAULT_ACHIEVEMENTS:
        if achievement_data['name'] not in existing_achievements:
            achievement = Achievement(
                name=achievement_data['name'], 
                description=achievement_data['description'], 
                icon_class=achievement_data['icon_class'], 
                required_action=achievement_data['required_action'], 
                required_count=achievement_data['required_count']
            )
            db.session.add(achievement)
        else:
            achievement = existing_achievements[achievement_data['name']]
            achievement.description = achievement_data['description']
            achievement.icon_class = achievement_data['icon_class']
            achievement.required_action = achievement_data['required_action']
            achievement.required_count = achievement_data['required_count']
    
    db.session.commit()

@bp.route('/achievements')
@login_required
def index():
    init_achievements()
    
    # Get all achievements with progress data
    achievements_query = db.session.query(
        Achievement,
        func.coalesce(UserAchievement.progress, 0).label('progress'),
        UserAchievement.unlocked_at,
        (func.coalesce(UserAchievement.progress, 0) >= Achievement.required_count)
    ).outerjoin(
        UserAchievement,
        and_(
            UserAchievement.achievement_id == Achievement.id,
            UserAchievement.user_id == current_user.id
        )
    ).filter(Achievement.name.in_([a['name'] for a in DEFAULT_ACHIEVEMENTS]))
    
    # Separate unlocked and locked achievements
    unlocked = []
    locked = []
    
    for achievement, progress, unlocked_at, is_unlocked in achievements_query:
        achievement_data = {
            'id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon_class,
            'progress': min(progress, achievement.required_count),  # Cap at 100%
            'required_progress': achievement.required_count,
            'is_locked': not is_unlocked,
            'unlocked_at': unlocked_at
        }
        
        if is_unlocked:
            unlocked.append(achievement_data)
        else:
            locked.append(achievement_data)
    
    # Sort unlocked by most recently unlocked first
    unlocked.sort(key=lambda x: x['unlocked_at'] or datetime.min, reverse=True)
    
    # Sort locked by predefined order
    achievement_order = [a['name'] for a in DEFAULT_ACHIEVEMENTS]
    locked.sort(key=lambda x: achievement_order.index(x['name']))
    
    # Combine with unlocked achievements first
    achievements_data = unlocked + locked
    
    return render_template('achievements/index.html', achievements=achievements_data)

def check_achievement_progress(user_id, action_type, increment=1):
    """Update progress for relevant achievements"""
    achievements = Achievement.query.filter(
        Achievement.required_action == action_type,
        Achievement.name.in_([a['name'] for a in DEFAULT_ACHIEVEMENTS])
    ).all()
    
    unlocked = []
    
    for achievement in achievements:
        user_achievement = UserAchievement.query.filter_by(
            user_id=user_id,
            achievement_id=achievement.id
        ).first()

        if not user_achievement:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                progress=0,
                unlocked_at=None
            )
            db.session.add(user_achievement)

        if user_achievement.unlocked_at is None:
            user_achievement.progress += increment
            
            if user_achievement.progress >= achievement.required_count:
                user_achievement.unlocked_at = datetime.utcnow()
                unlocked.append(achievement)
    
    db.session.commit()
    return unlocked

@bp.route('/test_progress/<action_type>')
@login_required
def test_progress(action_type):
    """Test route for all achievement types"""
    valid_actions = {a['required_action'] for a in DEFAULT_ACHIEVEMENTS}
    
    if action_type not in valid_actions:
        flash('Invalid action type', 'danger')
        return redirect(url_for('achievements.index'))
    
    unlocked = check_achievement_progress(current_user.id, action_type)
    
    if unlocked:
        flash(f'Unlocked achievement: {unlocked[0].name}', 'success')
    else:
        achievement = Achievement.query.filter_by(required_action=action_type).first()
        progress = UserAchievement.query.filter_by(
            user_id=current_user.id,
            achievement_id=achievement.id
        ).first()
        current = progress.progress if progress else 0
        total = achievement.required_count
        flash(f'Progress: {current}/{total} ({current/total*100:.1f}%)', 'info')
    
    return redirect(url_for('achievements.index'))