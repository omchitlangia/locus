from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.sku.forms import SKUForm
from . import sku_bp
from sqlalchemy import func, or_, and_, desc
from datetime import datetime
from app.models import SKU

@sku_bp.route('/management', methods=['GET', 'POST'])
@login_required
def index():
    form = SKUForm()
    search_query = request.args.get('search', '')
    show_all = request.args.get('show_all', 'false') == 'true'

    if form.validate_on_submit():
        try:
            # Check if SKU code already exists
            existing_sku = SKU.query.filter_by(code=form.code.data, user_id=current_user.id).first()
            if existing_sku:
                flash('SKU code already exists!', 'danger')
                return redirect(url_for('sku.index'))
            
            sku = SKU(
                code=form.code.data,
                name=form.name.data,
                description=form.description.data,
                cost_price=form.cost_price.data,
                selling_price=form.selling_price.data,
                quantity=form.quantity.data if form.quantity.data else 0,
                category=form.category.data,
                expiry_date=form.expiry_date.data,
                user_id=current_user.id,
                created_at=datetime.utcnow()  # Add creation timestamp
            )
            db.session.add(sku)
            db.session.commit()
            flash('SKU added successfully!', 'success')
            return redirect(url_for('sku.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating SKU: {str(e)}', 'danger')

    # Base query - newest first, but expired/out-of-stock last
    base_query = SKU.query.filter_by(user_id=current_user.id)
    
    # Apply search filter if search query exists
    if search_query:
        base_query = base_query.filter(or_(
            SKU.code.ilike(f'%{search_query}%'),
            SKU.name.ilike(f'%{search_query}%'),
            SKU.category.ilike(f'%{search_query}%'),
            SKU.description.ilike(f'%{search_query}%')
        ))

    # Get all SKUs and sort them with problematic ones last
    all_skus = base_query.all()
    
    # Categorize SKUs
    active_skus = []
    problematic_skus = []
    
    for sku in all_skus:
        if sku.is_expired() or sku.quantity <= 0:
            problematic_skus.append(sku)
        else:
            active_skus.append(sku)
    
    # Sort active SKUs by creation date (newest first)
    active_skus.sort(key=lambda x: x.created_at, reverse=True)
    # Sort problematic SKUs by severity (expired first, then out-of-stock)
    problematic_skus.sort(key=lambda x: (x.is_expired(), x.quantity <= 0), reverse=True)
    
    # Combine the lists
    sorted_skus = active_skus + problematic_skus

    # For display - limit to 3 if not showing all and no search
    if not show_all and not search_query:
        skus = sorted_skus[:3]
    else:
        skus = sorted_skus

    # Enhanced analytics calculations
    analytics = {
        'total_skus': len(all_skus),
        'total_inventory_value': sum(sku.cost_price * sku.quantity for sku in all_skus),
        'total_potential_revenue': sum(sku.selling_price * sku.quantity for sku in all_skus),
        'category_breakdown': db.session.query(
            SKU.category,
            func.count(SKU.id).label('count'),
            func.sum(SKU.cost_price * SKU.quantity).label('total_cost'),
            func.sum(SKU.selling_price * SKU.quantity).label('total_value')
        ).filter_by(user_id=current_user.id).group_by(SKU.category).all()
    }

    for sku in all_skus:
        sku.profit = sku.selling_price - sku.cost_price
        sku.profit_margin = (sku.profit / sku.selling_price) * 100 if sku.selling_price else 0
        sku.inventory_value = sku.cost_price * sku.quantity
        sku.revenue_potential = sku.selling_price * sku.quantity

    return render_template('sku/sku_management.html',
        form=form,
        skus=skus,
        all_skus_count=len(all_skus),
        analytics=analytics,
        search_query=search_query,
        show_all=show_all)

@sku_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    sku = SKU.query.get_or_404(id)
    if sku.user_id != current_user.id:
        flash('You do not have permission to edit this SKU', 'danger')
        return redirect(url_for('sku.index'))
    
    form = SKUForm(obj=sku)

    if form.validate_on_submit():
        try:
            # Check if SKU code is being changed to one that already exists
            if form.code.data != sku.code:
                existing_sku = SKU.query.filter_by(code=form.code.data, user_id=current_user.id).first()
                if existing_sku:
                    flash('SKU code already exists!', 'danger')
                    return redirect(url_for('sku.edit', id=id))
            
            form.populate_obj(sku)
            db.session.commit()
            flash('SKU updated successfully!', 'success')
            return redirect(url_for('sku.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating SKU: {str(e)}', 'danger')

    return render_template('sku/edit.html', form=form)