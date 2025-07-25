from flask import render_template
from flask_login import login_required, current_user
from . import report_bp
from app.models import Revenue, FixedCost, VariableCost, RevenuePrediction, SKU, Bill, BillingItem
from sqlalchemy import func
from datetime import datetime, timedelta

@report_bp.route('/dashboard/business-report')
@login_required
def unified_report():
    user_id = current_user.id
    now = datetime.utcnow()

    def float_or_zero(x):
        return float(x) if x else 0.0

    # --- Revenue trend and profit/loss by month (last 6 months) ---
    months, monthly_revenue, monthly_fixed, monthly_variable, monthly_profit = [], [], [], [], []
    for i in range(6, 0, -1):
        m = (now - timedelta(days=30 * i))
        y, mon = m.year, m.month
        start = datetime(y, mon, 1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        r = float_or_zero(Revenue.query.with_entities(func.sum(Revenue.amount)).filter_by(user_id=user_id).filter(Revenue.timestamp >= start, Revenue.timestamp <= end).scalar())
        fc = float_or_zero(FixedCost.query.with_entities(func.sum(FixedCost.amount)).filter_by(user_id=user_id).filter(FixedCost.timestamp >= start, FixedCost.timestamp <= end).scalar())
        vc = float_or_zero(VariableCost.query.with_entities(func.sum(VariableCost.amount)).filter_by(user_id=user_id).filter(VariableCost.timestamp >= start, VariableCost.timestamp <= end).scalar())
        months.append(start.strftime('%b %Y'))
        monthly_revenue.append(r)
        monthly_fixed.append(fc)
        monthly_variable.append(vc)
        monthly_profit.append(r - fc - vc)

    # --- Sales Trends (by day, last 10 weeks) ---
    sales_labels, sales_trends_data = [], []
    sales_data = (Revenue.query
        .with_entities(func.DATE(Revenue.timestamp).label('dt'), func.sum(Revenue.amount).label('total'))
        .filter(Revenue.user_id == user_id)
        .filter(Revenue.timestamp >= now - timedelta(days=70))
        .group_by(func.DATE(Revenue.timestamp))
        .order_by(func.DATE(Revenue.timestamp))
        .all())
    for row in sales_data:
        sales_labels.append(row.dt.strftime('%b-%d'))
        sales_trends_data.append(float_or_zero(row.total))

    # --- Cost Breakdown (latest sum for each type) ---
    total_fixed = float_or_zero(FixedCost.query.with_entities(func.sum(FixedCost.amount)).filter_by(user_id=user_id).scalar())
    total_variable = float_or_zero(VariableCost.query.with_entities(func.sum(VariableCost.amount)).filter_by(user_id=user_id).scalar())
    cost_labels = ["Fixed", "Variable"]
    cost_data = [total_fixed, total_variable]

    # --- KPIs / Business Health ---
    current_month_start = datetime(now.year, now.month, 1)
    prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    prev_month_end = current_month_start - timedelta(days=1)
    rev_this = float_or_zero(Revenue.query.with_entities(func.sum(Revenue.amount)).filter_by(user_id=user_id).filter(Revenue.timestamp >= current_month_start).scalar())
    rev_prev = float_or_zero(Revenue.query.with_entities(func.sum(Revenue.amount)).filter_by(user_id=user_id).filter(Revenue.timestamp.between(prev_month_start, prev_month_end)).scalar())
    revenue_growth = ((rev_this - rev_prev) / rev_prev * 100) if rev_prev > 0 else (100 if rev_this > 0 else 0)
    gross_profit_margin = ((rev_this - total_variable) / rev_this * 100) if rev_this > 0 else 0

    latest_forecast = RevenuePrediction.query.filter_by(user_id=user_id).order_by(RevenuePrediction.prediction_date.desc()).first()
    forecast_accuracy = (latest_forecast.r_squared * 100) if latest_forecast and latest_forecast.r_squared else 0
    latest_forecast_value = latest_forecast.predicted_amount if latest_forecast else None

    # --- SKU, Bill, Manual KPI, Persona info ---
    top_skus = (
        SKU.query
        .filter_by(user_id=user_id)
        .join(BillingItem, BillingItem.sku_id == SKU.id)
        .group_by(SKU.id)
        .order_by(func.sum(BillingItem.quantity).desc())
        .limit(5)
        .with_entities(SKU.name, func.sum(BillingItem.quantity).label('sales'))
        .all()
    )
    total_bills = Bill.query.filter_by(user_id=user_id).count()
    outstanding_amount = float_or_zero(Bill.query.with_entities(func.sum(Bill.grand_total)).filter_by(user_id=user_id).filter(Bill.payment_status == 'Pending').scalar())
    skus = SKU.query.filter_by(user_id=user_id).all()
    total_sku_sales = float_or_zero(BillingItem.query.join(Bill).filter(Bill.user_id == user_id).with_entities(func.sum(BillingItem.quantity)).scalar())
    avg_inventory = (sum([sku.quantity for sku in skus]) / len(skus)) if skus else 0
    inventory_turnover = (total_sku_sales / avg_inventory) if avg_inventory > 0 else 0
    business_health_score = current_user.health_score or 0
    customer_retention = 0
    marketing_roi = 0
    team_efficiency = 0
    user_growth = 0
    persona_type = (current_user.persona or "Unknown").lower()
    persona_data = {
        "default": {"emoji": "❓", "one_liner": "No personality data available."},
        "analytical": {"emoji": "🧠", "one_liner": "Insightful. Precise. Data-driven."},
        "creative": {"emoji": "🎨", "one_liner": "Imaginative. Open-minded. Innovative."},
        "leader": {"emoji": "👑", "one_liner": "Confident. Motivational. Decisive."},
        "supporter": {"emoji": "🤝", "one_liner": "Empathetic. Reliable. Connector."}
    }
    persona_info = persona_data.get(persona_type, persona_data["default"])

    forecast_trends = [{'description': 'Forecast projects steady growth.'}]
    sales_trends = [{'description': 'Sales trend reflects recent activity.'}]
    cost_breakdown_desc = [{'label': 'Fixed Costs', 'amount': total_fixed}, {'label': 'Variable Costs', 'amount': total_variable}]
    profit_loss = [{'label': 'Net Profit', 'value': sum(monthly_profit)}]

    return render_template(
        'business_report/unified_report.html',
        kpis={
            'revenue_growth': round(revenue_growth, 2),
            'gross_profit_margin': round(gross_profit_margin, 2),
            'forecast_accuracy': round(forecast_accuracy, 2),
            'customer_retention': customer_retention,
            'marketing_roi': marketing_roi,
            'inventory_turnover': round(inventory_turnover, 2),
            'team_efficiency': team_efficiency,
            'user_growth': user_growth,
            'business_health': round(business_health_score, 2),
        },
        profit=round(sum(monthly_profit), 2),
        total_revenue=round(sum(monthly_revenue), 2),
        total_fixed=round(sum(monthly_fixed), 2),
        total_variable=round(sum(monthly_variable), 2),
        total_bills=total_bills,
        outstanding_amount=round(outstanding_amount, 2),
        top_skus=top_skus,
        latest_forecast=latest_forecast_value,
        forecast_trends=forecast_trends,
        sales_trends=sales_trends,
        cost_breakdown=cost_breakdown_desc,
        profit_loss=profit_loss,
        personality_profile={
            'type': persona_type.capitalize(),
            'one_liner': persona_info['one_liner'],
            'type_emoji': persona_info['emoji']
        },
        # Dynamic datasets for Chart.js (from visualization logic!)
        revenue_labels=months,
        monthly_revenue=monthly_revenue,
        profit_loss_labels=months,
        profit_loss_data=monthly_profit,
        sales_labels=sales_labels,
        sales_trends_data=sales_trends_data,
        cost_labels=cost_labels,
        cost_data=cost_data,
        forecast_actual_labels=months,
        actual_revenue=monthly_revenue,
        forecast_revenue=monthly_revenue  # Placeholder; use real if available
    )
