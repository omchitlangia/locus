from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from datetime import datetime, timedelta
import numpy as np
from statsmodels.tsa.api import ExponentialSmoothing
from sklearn.metrics import r2_score
from . import forecast_bp
from app.models import Revenue, FixedCost, VariableCost, RevenuePrediction, Achievement, UserAchievement
from sklearn.linear_model import LinearRegression
from sqlalchemy import func

@forecast_bp.route('/dashboard/forecasting')
@login_required
def index():
    total_revenue = db.session.query(func.sum(Revenue.amount))\
                             .filter_by(user_id=current_user.id).scalar() or 0
    total_fixed = db.session.query(func.sum(FixedCost.amount))\
                           .filter_by(user_id=current_user.id).scalar() or 0
    total_variable = db.session.query(func.sum(VariableCost.amount))\
                              .filter_by(user_id=current_user.id).scalar() or 0
    
    return render_template('/forecasting/forecasting.html',
                         total_revenue=total_revenue,
                         total_fixed=total_fixed,
                         total_variable=total_variable)

@forecast_bp.route('/dashboard/forecasting/break_even', methods=['GET', 'POST'])
@login_required
def break_even():
    if request.method == 'POST':
        try:
            time_range = request.form.get('time_range', 'all')
            
            now = datetime.utcnow()
            if time_range == 'month':
                start_date = now - timedelta(days=30)
            elif time_range == 'quarter':
                start_date = now - timedelta(days=90)
            elif time_range == 'year':
                start_date = now - timedelta(days=365)
            else:
                start_date = None
            
            revenue_query = Revenue.query.filter_by(user_id=current_user.id)
            fixed_query = FixedCost.query.filter_by(user_id=current_user.id)
            variable_query = VariableCost.query.filter_by(user_id=current_user.id)
            
            if start_date:
                revenue_query = revenue_query.filter(Revenue.timestamp >= start_date)
                fixed_query = fixed_query.filter(FixedCost.timestamp >= start_date)
                variable_query = variable_query.filter(VariableCost.timestamp >= start_date)
            
            total_revenue = revenue_query.with_entities(func.sum(Revenue.amount)).scalar() or 0
            total_fixed = fixed_query.with_entities(func.sum(FixedCost.amount)).scalar() or 0
            total_variable = variable_query.with_entities(func.sum(VariableCost.amount)).scalar() or 0
            
            if total_revenue == 0:
                flash('No revenue data available for selected period', 'error')
                return redirect(url_for('.break_even')) 
            
            variable_cost_ratio = total_variable / total_revenue
            contribution_margin = 1 - variable_cost_ratio
            break_even_amount = total_fixed / contribution_margin if contribution_margin else 0
            
            return render_template('/forecasting/break_even.html',
                                 break_even=round(break_even_amount, 2),
                                 fixed_costs=round(total_fixed, 2),
                                 variable_cost_ratio=round(variable_cost_ratio*100, 2),
                                 contribution_margin=round(contribution_margin*100, 2),
                                 time_range=time_range)
            
        except Exception as e:
            flash(f'Error in calculation: {str(e)}', 'error')
            return redirect(url_for('.break_even'))  
    
    return render_template('/forecasting/break_even.html')

@forecast_bp.route('/dashboard/forecasting/revenue_prediction', methods=['GET', 'POST'])
@login_required
def revenue_prediction():
    if request.method == 'POST':
        try:
            time_range = request.form.get('time_range', 'all')
            if time_range not in ['month', 'quarter', 'year', 'all']:
                raise ValueError("Invalid time range selected")

            now = datetime.utcnow()
            date_filters = {
                'month': now - timedelta(days=30),
                'quarter': now - timedelta(days=90),
                'year': now - timedelta(days=365),
                'all': None
            }
            start_date = date_filters.get(time_range)

            query = Revenue.query.filter_by(user_id=current_user.id)
            if start_date:
                query = query.filter(Revenue.timestamp >= start_date)
            
            revenues = query.order_by(Revenue.timestamp).all()
            
            if len(revenues) < 5:
                flash('❌ Minimum 5 historical entries required for reliable predictions', 'error')
                return redirect(url_for('.revenue_prediction'))
                
            unique_dates = {rev.timestamp.date() for rev in revenues}
            if len(unique_dates) < 3:
                flash('❌ Data must span at least 3 different calendar dates', 'error')
                return redirect(url_for('.revenue_prediction'))

            sorted_revenues = sorted(revenues, key=lambda x: x.timestamp)
            timestamps = [rev.timestamp for rev in sorted_revenues]
            amounts = [rev.amount for rev in sorted_revenues]
            
            day_deltas = [(ts - timestamps[0]).days for ts in timestamps]
            X = np.array(day_deltas).reshape(-1, 1)
            y = np.array(amounts)
            
            try:
                model = ExponentialSmoothing(
                    y,
                    trend='add',
                    seasonal='add' if len(revenues) > 12 else None,
                    seasonal_periods=12
                )
                model_fit = model.fit()
            except Exception as e:
                raise ValueError(f"Model fitting failed: {str(e)}")
            
            forecast = model_fit.forecast(3)
            forecast_dates = [now + timedelta(days=30*(i+1)) for i in range(3)]
            
            std_dev = np.std(y[-6:]) if len(y) >= 6 else np.std(y)
            confidence_multiplier = 1.96
            
            r_squared = r2_score(y, model_fit.fittedvalues)
            
            predictions = []
            for i, (date, amount) in enumerate(zip(forecast_dates, forecast)):
                ci = std_dev * confidence_multiplier * (i+1)
                predictions.append({
                    'period': f"Period {i+1}",
                    'date': date.strftime('%Y-%m-%d'),
                    'amount': round(float(amount), 2),
                    'ci_lower': round(float(amount - ci), 2),
                    'ci_upper': round(float(amount + ci), 2),
                    'trend': '↑' if amount > y[-1] else '↓'
                })
            
            for pred in predictions:
                new_pred = RevenuePrediction(
                    user_id=current_user.id,
                    prediction_date=datetime.utcnow(),
                    period_start=datetime.strptime(pred['date'], '%Y-%m-%d'),
                    period_end=datetime.strptime(pred['date'], '%Y-%m-%d') + timedelta(days=30),
                    predicted_amount=pred['amount'],
                    actual_amount=None,
                    r_squared=r_squared
                )
                db.session.add(new_pred)
            
            # EXACT MATCH TO SKU ACHIEVEMENT TRACKING START
            forecast_count = RevenuePrediction.query.filter_by(user_id=current_user.id).count()
            unlocked = []
            forecast_achievements = [
                ('fifth_forecast', 5, 'Rising Analyst'),
                ('fifteenth_forecast', 15, 'Seasoned Forecaster'), 
                ('thirtieth_forecast', 30, 'Master Tracker')
            ]

            progress_messages = []
            for action, threshold, name in forecast_achievements:
                achievement = Achievement.query.filter_by(required_action=action).first()
                if not achievement:
                    continue
                
                user_achievement = UserAchievement.query.filter_by(
                    user_id=current_user.id,
                    achievement_id=achievement.id
                ).first()
                
                if not user_achievement:
                    capped_progress = min(forecast_count, threshold)
                    user_achievement = UserAchievement(
                        user_id=current_user.id,
                        achievement_id=achievement.id,
                        progress=capped_progress,
                        unlocked_at=datetime.utcnow() if capped_progress >= threshold else None
                    )
                    db.session.add(user_achievement)
                else:
                    new_progress = min(forecast_count, threshold)
                    if user_achievement.progress != new_progress:
                        user_achievement.progress = new_progress
                    
                    if new_progress >= threshold and not user_achievement.unlocked_at:
                        user_achievement.unlocked_at = datetime.utcnow()
                        unlocked.append(achievement)
                
                if not user_achievement.unlocked_at:
                    progress_messages.append(f"{name}: {user_achievement.progress}/{threshold}")
            # EXACT MATCH TO SKU ACHIEVEMENT TRACKING END

            db.session.commit()

            if unlocked:
                for achievement in unlocked:
                    flash(f'🏆 Achievement Unlocked: {achievement.name}!', 'success')
            elif progress_messages:
                flash('Forecast generated! Progress: ' + ', '.join(progress_messages), 'info')
            
            return render_template(
                '/forecasting/revenue_prediction.html',
                predictions=predictions,
                historical_data=[(ts.strftime('%Y-%m-%d'), amount) 
                               for ts, amount in zip(timestamps, amounts)],
                r_squared=round(r_squared, 2),
                time_range=time_range,
                last_actual=y[-1]
            )
            
        except Exception as e:
            db.session.rollback()
            flash(f'⚠️ Prediction error: {str(e)}', 'error')
            return redirect(url_for('.revenue_prediction'))
    
    return render_template('/forecasting/revenue_prediction.html')