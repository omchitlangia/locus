from flask import render_template, request, redirect, session, flash, url_for
from app.extensions import db
from app.models import Revenue, FixedCost, VariableCost, Achievement, UserAchievement
from . import dataentry_bp
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func

@dataentry_bp.route('/dashboard/dataentry')
@login_required
def index():
    total_revenue = db.session.query(func.sum(Revenue.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_fixed = db.session.query(func.sum(FixedCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_variable = db.session.query(func.sum(VariableCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
    profit = total_revenue - total_fixed - total_variable
    
    return render_template('/data_entry/dataentry.html',
                         total_revenue=total_revenue,
                         total_fixed=total_fixed,
                         total_variable=total_variable,
                         profit=profit)

@dataentry_bp.route('/dashboard/dataentry/revenue', methods=['GET', 'POST'])
@login_required
def revenue():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        remarks = request.form['remarks']
        entry = Revenue(
            user_id=current_user.id,
            amount=amount,
            remarks=remarks,
            timestamp=datetime.utcnow()
        )
        db.session.add(entry)
        
        try:
            # Commit immediately to ensure we have current data
            db.session.commit()
            
            # Get fresh total revenue after commit (fixed syntax)
            total_revenue = db.session.query(
                func.sum(Revenue.amount)
            ).filter_by(
                user_id=current_user.id
            ).scalar() or 0

            # Revenue achievement thresholds
            revenue_achievements = [
                ('100k_earned', 100000, 'Elite Entrepreneur'),
                ('1mil_earned', 1000000, 'Total Tycoon')
            ]

            unlocked = []
            progress_messages = []

            for action, threshold, name in revenue_achievements:
                achievement = Achievement.query.filter_by(required_action=action).first()
                if not achievement:
                    continue

                user_achievement = UserAchievement.query.filter_by(
                    user_id=current_user.id,
                    achievement_id=achievement.id
                ).first()

                if not user_achievement:
                    user_achievement = UserAchievement(
                        user_id=current_user.id,
                        achievement_id=achievement.id,
                        progress=0,
                        unlocked_at=None
                    )
                    db.session.add(user_achievement)

                new_progress = min(total_revenue, threshold)
                
                if new_progress > user_achievement.progress:
                    user_achievement.progress = new_progress
                    if new_progress >= threshold and not user_achievement.unlocked_at:
                        user_achievement.unlocked_at = datetime.utcnow()
                        unlocked.append(achievement)

                if not user_achievement.unlocked_at:
                    progress_messages.append(
                        f"{name}: {user_achievement.progress:,}/{threshold:,}"
                    )

            db.session.commit()

            if unlocked:
                for achievement in unlocked:
                    flash(f'🏆 Achievement Unlocked: {achievement.name}!', 'success')
            elif progress_messages:
                flash('Revenue added! Progress: ' + ', '.join(progress_messages), 'info')
            else:
                flash('Revenue added successfully!', 'success')

            return redirect(url_for('dataentry.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error processing revenue entry: {str(e)}', 'error')
            return redirect(url_for('dataentry.index'))

    return render_template('/data_entry/data_form.html', entry_type='Revenue')

@dataentry_bp.route('/dashboard/dataentry/fixedcost', methods=['GET', 'POST'])
@login_required
def fixedcost():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        remarks = request.form['remarks']
        entry = FixedCost(user_id=current_user.id, amount=amount, remarks=remarks, timestamp=datetime.utcnow())
        db.session.add(entry)
        db.session.commit()
        flash('Fixed cost added successfully!', 'success')
        return redirect(url_for('dataentry.index'))
    return render_template('/data_entry/data_form.html', entry_type='FixedCost')

@dataentry_bp.route('/dashboard/dataentry/variablecost', methods=['GET', 'POST'])
@login_required
def variablecost():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        remarks = request.form['remarks']
        entry = VariableCost(user_id=current_user.id, amount=amount, remarks=remarks, timestamp=datetime.utcnow())
        db.session.add(entry)
        db.session.commit()
        flash('Variable cost added successfully!', 'success')
        return redirect(url_for('dataentry.index'))
    return render_template('/data_entry/data_form.html', entry_type='VariableCost')

@dataentry_bp.route('/dashboard/dataentry/view/<entry_type>')
@login_required
def view_entries(entry_type):
    page = request.args.get('page', 1, type=int)
    per_page = 10

    model = {
        'Revenue': Revenue,
        'FixedCost': FixedCost, 
        'VariableCost': VariableCost
    }.get(entry_type)
    
    if not model:
        flash('Invalid entry type', 'error')
        return redirect(url_for('dataentry.index'))

    entries = model.query.filter_by(user_id=current_user.id)\
                        .order_by(model.timestamp.desc())\
                        .paginate(page=page, per_page=per_page)
    
    return render_template('/data_entry/data_view.html',
                        entries=entries.items,
                        pagination=entries,
                        entry_type=entry_type)