from flask import current_app
from flask import render_template, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Revenue, FixedCost, VariableCost
from . import visualization_bp
import matplotlib
matplotlib.use('Agg')  # Must be before pyplot import
import matplotlib.pyplot as plt
from flask import request, jsonify
from io import BytesIO
import base64
from sqlalchemy import func, text
from datetime import datetime
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    # Fallback implementation
    class relativedelta:
        def __init__(self, months=0, years=0):
            self.months = months
            self.years = years

def get_date_range(timeframe):
    end_date = datetime.utcnow()
    if timeframe == 'month':
        start_date = end_date - relativedelta(months=1)
    elif timeframe == 'quarter':
        start_date = end_date - relativedelta(months=3)
    elif timeframe == 'year':
        start_date = end_date - relativedelta(years=1)
    else:  # all_time
        start_date = datetime.min
    return start_date, end_date

@visualization_bp.route('/dashboard/visualization')
@login_required
def index():
    """Main visualization dashboard"""
    return render_template('visualization/visualization.html')

@visualization_bp.route('/dashboard/visualization/profit-loss')
@login_required
def profit_loss():
    """Profit & Loss Statement with timeframe selection"""
    timeframe = request.args.get('timeframe', 'month')  # Default to last month
    return render_template('visualization/profit_loss_new.html', timeframe=timeframe)

@visualization_bp.route('/dashboard/visualization/profit-loss/data')
@login_required
def profit_loss_data():
    """JSON endpoint for profit/loss data"""
    try:
        timeframe = request.args.get('timeframe', 'month')
        start_date, end_date = get_date_range(timeframe)
        
        # Get filtered transactions - use name if description doesn't exist
        revenue = Revenue.query.filter(
            Revenue.user_id == current_user.id,
            Revenue.timestamp >= start_date,
            Revenue.timestamp <= end_date
        ).order_by(Revenue.timestamp.desc()).all()
        
        fixed = FixedCost.query.filter(
            FixedCost.user_id == current_user.id,
            FixedCost.timestamp >= start_date,
            FixedCost.timestamp <= end_date
        ).order_by(FixedCost.timestamp.desc()).all()
        
        variable = VariableCost.query.filter(
            VariableCost.user_id == current_user.id,
            VariableCost.timestamp >= start_date,
            VariableCost.timestamp <= end_date
        ).order_by(VariableCost.timestamp.desc()).all()
        
        # Calculate totals
        total_revenue = sum(t.amount for t in revenue) or 0
        total_fixed = sum(t.amount for t in fixed) or 0
        total_variable = sum(t.amount for t in variable) or 0
        gross_profit = total_revenue - total_variable
        net_profit = gross_profit - total_fixed
        
        # Prepare data for JSON response - use name or category if description doesn't exist
        data = {
            'timeframe': timeframe,
            'revenue': [{'date': t.timestamp.strftime('%Y-%m-%d'), 
                        'description': getattr(t, 'description', getattr(t, 'name', 'Revenue')), 
                        'amount': t.amount} for t in revenue],
            'fixed_costs': [{'date': t.timestamp.strftime('%Y-%m-%d'), 
                           'description': getattr(t, 'description', getattr(t, 'name', 'Fixed Cost')), 
                           'amount': t.amount} for t in fixed],
            'variable_costs': [{'date': t.timestamp.strftime('%Y-%m-%d'), 
                              'description': getattr(t, 'description', getattr(t, 'name', 'Variable Cost')), 
                              'amount': t.amount} for t in variable],
            'totals': {
                'revenue': total_revenue,
                'fixed_costs': total_fixed,
                'variable_costs': total_variable,
                'gross_profit': gross_profit,
                'net_profit': net_profit
            }
        }
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error generating profit/loss data: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@visualization_bp.route('/dashboard/visualization/sales-trends')
@login_required
def sales_trends():
    """Sales Trends Visualization"""
    timeframe = request.args.get('timeframe', 'month')  # Default to last month
    return render_template('visualization/sales_trends_new.html', timeframe=timeframe)

@visualization_bp.route('/dashboard/visualization/sales-trends/data')
@login_required
def sales_trends_data():
    """JSON endpoint for sales trends data"""
    try:
        timeframe = request.args.get('timeframe', 'month')
        end_date = datetime.utcnow()
        
        # Get start date based on timeframe
        if timeframe == 'month':
            start_date = end_date - relativedelta(months=1)
            date_format = '%Y-%m-%d'  # Daily
            group_expr = func.date(Revenue.timestamp)
        elif timeframe == 'quarter':
            start_date = end_date - relativedelta(months=3)
            date_format = '%Y-%m-%W'  # Weekly
            group_expr = func.concat(
                func.year(Revenue.timestamp), 
                '-', 
                func.lpad(func.week(Revenue.timestamp), 2, '0'))
        elif timeframe == 'year':
            start_date = end_date - relativedelta(years=1)
            date_format = '%Y-%m'  # Monthly
            group_expr = func.date_format(Revenue.timestamp, '%Y-%m')
        else:  # all_time
            first_revenue = Revenue.query.filter_by(user_id=current_user.id)\
                          .order_by(Revenue.timestamp.asc()).first()
            if not first_revenue:
                return jsonify({'error': 'No revenue data available'})
            start_date = first_revenue.timestamp
            date_format = '%Y'  # Yearly
            group_expr = func.year(Revenue.timestamp)

        # Query the data using text() for MySQL compatibility
        sales_data = db.session.query(
            group_expr.label('period'),
            func.sum(Revenue.amount).label('total')
        ).filter(
            Revenue.user_id == current_user.id,
            Revenue.timestamp >= start_date,
            Revenue.timestamp <= end_date
        ).group_by(text('period')).order_by(text('period')).all()

        if not sales_data:
            return jsonify({'error': 'No revenue data available for the selected timeframe'})

        # Format periods for display
        periods = []
        amounts = []
        for row in sales_data:
            try:
                if timeframe == 'month':
                    periods.append(row.period.strftime('%Y-%m-%d'))
                elif timeframe == 'quarter':
                    periods.append(f"{row.period}")
                elif timeframe == 'year':
                    periods.append(f"{row.period}")
                else:  # all_time
                    periods.append(f"{row.period}")
                amounts.append(float(row.total))
            except Exception as e:
                current_app.logger.error(f"Error formatting period {row.period}: {str(e)}")
                continue

        if not periods:
            return jsonify({'error': 'No valid data points available after formatting'})

        # Generate plot
        plt.figure(figsize=(10, 5))
        plt.plot(periods, amounts, marker='o', color='#00e5ff')
        plt.title(f'Sales Trends - {timeframe.replace("_", " ").title()}')
        plt.xlabel('Period')
        plt.ylabel('Revenue (₹)')
        plt.xticks(rotation=45)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', transparent=True, dpi=100)
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return jsonify({
            'timeframe': timeframe,
            'periods': periods,
            'amounts': amounts,
            'plot_url': plot_data
        })
    except Exception as e:
        current_app.logger.error(f"Error generating sales trends: {str(e)}")
        return jsonify({'error': f"Failed to generate sales trends: {str(e)}"}), 500

@visualization_bp.route('/dashboard/visualization/cost-breakdown')
@login_required
def cost_breakdown():
    """Cost Breakdown Visualization"""
    try:
        total_fixed = db.session.query(db.func.sum(FixedCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
        total_variable = db.session.query(db.func.sum(VariableCost.amount)).filter_by(user_id=current_user.id).scalar() or 0
        
        labels = ['Fixed Costs', 'Variable Costs']
        sizes = [total_fixed, total_variable]
        colors = ['#ff9999', '#66b3ff']
        
        plt.figure(figsize=(6,6))
        plt.pie(sizes, labels=labels, colors=colors, 
                autopct='%1.1f%%', startangle=90,
                wedgeprops={'edgecolor': 'black', 'linewidth': 1})
        plt.axis('equal')
        plt.title('Cost Breakdown')
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', transparent=True)
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return render_template('visualization/cost_breakdown.html',
                            plot_url=plot_data,
                            fixed_costs=total_fixed,
                            variable_costs=total_variable)
    except Exception as e:
        abort(500, description="Error generating cost breakdown")