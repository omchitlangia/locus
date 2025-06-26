from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.sku.models import SKU
from app.sku.forms import SKUForm
from . import sku_bp
from sqlalchemy import func

@sku_bp.route('/management', methods=['GET', 'POST'])
@login_required
def index():
    form = SKUForm()
    
    if form.validate_on_submit():
        try:
            sku = SKU(
                code=form.code.data,
                name=form.name.data,
                description=form.description.data,
                cost_price=form.cost_price.data,
                selling_price=form.selling_price.data,
                quantity=form.quantity.data,
                category=form.category.data,
                user_id=current_user.id
            )
            db.session.add(sku)
            db.session.commit()
            flash('SKU added successfully!', 'success')
            return redirect(url_for('sku.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating SKU: {str(e)}', 'danger')
    
    skus = SKU.query.filter_by(user_id=current_user.id).all()
    
    # Enhanced analytics calculations
    analytics = {
        'total_skus': len(skus),
        'total_inventory_value': sum(sku.cost_price * sku.quantity for sku in skus),
        'total_potential_revenue': sum(sku.selling_price * sku.quantity for sku in skus),
        'category_breakdown': db.session.query(
            SKU.category,
            func.count(SKU.id).label('count'),
            func.sum(SKU.cost_price * SKU.quantity).label('total_cost'),
            func.sum(SKU.selling_price * SKU.quantity).label('total_value')
        ).filter_by(user_id=current_user.id).group_by(SKU.category).all()
    }

    for sku in skus:
        sku.profit = sku.selling_price - sku.cost_price
        sku.profit_margin = (sku.profit / sku.selling_price) * 100 if sku.selling_price else 0
        sku.inventory_value = sku.cost_price * sku.quantity
        sku.revenue_potential = sku.selling_price * sku.quantity

    return render_template('sku/sku_management.html',
                         form=form,
                         skus=skus,
                         analytics=analytics)