from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Event
from datetime import datetime
from . import event_bp

@event_bp.route('/dashboard/ep')
@login_required
def index():
    events = Event.query.filter_by(user_id=current_user.id).order_by(Event.start_date).all()
    return render_template('/ep/event_list.html', events=events)

@event_bp.route('/dashboard/ep/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            description = request.form['description']
            event_type = request.form['event_type']
            category = request.form.get('category', '')
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
            is_recurring = 'is_recurring' in request.form
            recurrence_pattern = request.form.get('recurrence_pattern', '')
            
            # Cost fields
            marketing_cost = float(request.form.get('marketing_cost', 0))
            logistics_cost = float(request.form.get('logistics_cost', 0))
            hiring_cost = float(request.form.get('hiring_cost', 0))
            other_cost = float(request.form.get('other_cost', 0))
            
            # Revenue impact
            expected_revenue_boost = float(request.form.get('expected_revenue_boost', 0))
            
            # Create event
            event = Event(
                user_id=current_user.id,
                name=name,
                description=description,
                event_type=event_type,
                category=category if event_type == 'business' else None,
                start_date=start_date,
                end_date=end_date,
                is_recurring=is_recurring,
                recurrence_pattern=recurrence_pattern if is_recurring else None,
                marketing_cost=marketing_cost,
                logistics_cost=logistics_cost,
                hiring_cost=hiring_cost,
                other_cost=other_cost,
                expected_revenue_boost=expected_revenue_boost
            )
            
            db.session.add(event)
            db.session.commit()
            
            flash('Event created successfully!', 'success')
            return redirect(url_for('event.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating event: {str(e)}', 'error')
    
    return render_template('/ep/create_event.html')

@event_bp.route('/dashboard/ep/<int:event_id>')
@login_required
def event_detail(event_id):
    event = Event.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    return render_template('/ep/event_detail.html', event=event)

@event_bp.route('/dashboard/ep/calendar')
@login_required
def calendar_view():
    events = Event.query.filter_by(user_id=current_user.id).all()
    return render_template('/ep/calendar_view.html', events=events)