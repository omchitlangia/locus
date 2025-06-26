
from .forms import ROICalculatorForm, BudgetAllocatorForm
from .services import calculate_roi, optimize_budget
# routes.py (updated)
from flask import render_template, request, flash, redirect, url_for, session
from flask_login import login_required
from . import opt_bp

@opt_bp.route('/dashboard/optimization')
@login_required
def optimization_menu():
    """Show optimization tools menu"""
    return render_template('/optimization/optimization_menu.html')

@opt_bp.route('/dashboard/optimization/roi-calculator', methods=['GET', 'POST'])
@login_required
def roi_calculator():
    """Handle ROI Calculator form submission"""
    form = ROICalculatorForm()
    result = None
    
    if form.validate_on_submit():
        result = calculate_roi(
            selling_price=float(form.selling_price.data),
            units_sold=float(form.units_sold.data),
            cost=float(form.cost.data)
        )
        
        if 'error' in result:
            flash(f"Calculation error: {result['error']}", 'danger')
        else:
            flash("ROI calculated successfully!", 'success')
    
    return render_template('/optimization/roi_calculator.html', 
                         form=form, 
                         result=result)

@opt_bp.route('/dashboard/optimization/budget-allocator', methods=['GET', 'POST'])
def budget_allocator():
    if request.method == 'POST':
        # Get form data
        total_budget = float(request.form.get('total_budget'))
        campaigns = []
        
        # Get all campaign data
        i = 0
        while f'campaigns-{i}-name' in request.form:
            campaigns.append({
                'name': request.form.get(f'campaigns-{i}-name'),
                'roi_percent': float(request.form.get(f'campaigns-{i}-roi_percent')),
                'max_allocation': float(request.form.get(f'campaigns-{i}-max_allocation'))
            })
            i += 1
        
        # Optimize and store result
        session['result'] = optimize_budget(total_budget, campaigns)
        return redirect('/dashboard/optimization/optimization-results')
    
    # GET request - show empty form
    return render_template('/optimization/simple_allocator.html')

@opt_bp.route('/dashboard/optimization/optimization-results')
def show_results():
    result = session.get('result')
    if not result:
        return redirect('/budget-allocator')
    return render_template('/optimization/simple_results.html', result=result)