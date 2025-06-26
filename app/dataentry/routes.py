from flask import render_template, request, redirect, session, flash, url_for
from app.extensions import db
from app.models import Revenue, FixedCost, VariableCost
from . import dataentry_bp
from flask_login import login_required, current_user

@dataentry_bp.route('/dashboard/dataentry')
@login_required
def index():
    total_revenue = db.session.query(db.func.sum(Revenue.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_fixed = db.session.query(db.func.sum(FixedCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_variable = db.session.query(db.func.sum(VariableCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
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
        entry = Revenue(user_id=current_user.id, amount=amount, remarks=remarks)  # Use current_user.id
        db.session.add(entry)
        db.session.commit()
        flash('Revenue added successfully!', 'success')
        return redirect(url_for('dataentry.index'))
    return render_template('/data_entry/data_form.html', entry_type='Revenue')

@dataentry_bp.route('/dashboard/dataentry/fixedcost', methods=['GET', 'POST'])
@login_required
def fixedcost():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        remarks = request.form['remarks']
        # user_id = session['user_id']
        entry = FixedCost(user_id=current_user.id, amount=amount, remarks=remarks)
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
        # user_id = session['user_id']
        entry = VariableCost(user_id=current_user.id, amount=amount, remarks=remarks)
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
