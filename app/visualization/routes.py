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
        
        # CHANGED: Added explicit query construction and debug prints
        print(f"Fetching revenue for user {current_user.id} from {start_date} to {end_date}")
        
        revenue = db.session.query(Revenue).filter(
            Revenue.user_id == current_user.id,
            Revenue.timestamp >= start_date,
            Revenue.timestamp <= end_date
        ).order_by(Revenue.timestamp.desc()).all()
        
        fixed = db.session.query(FixedCost).filter(
            FixedCost.user_id == current_user.id,
            FixedCost.timestamp >= start_date,
            FixedCost.timestamp <= end_date
        ).order_by(FixedCost.timestamp.desc()).all()
        
        variable = db.session.query(VariableCost).filter(
            VariableCost.user_id == current_user.id,
            VariableCost.timestamp >= start_date,
            VariableCost.timestamp <= end_date
        ).order_by(VariableCost.timestamp.desc()).all()
        
        # CHANGED: More robust total calculation
        total_revenue = sum(t.amount for t in revenue) if revenue else 0
        total_fixed = sum(t.amount for t in fixed) if fixed else 0
        total_variable = sum(t.amount for t in variable) if variable else 0
        gross_profit = total_revenue - total_variable
        net_profit = gross_profit - total_fixed
        
        print(f"Totals - Revenue: {total_revenue}, Fixed: {total_fixed}, Variable: {total_variable}")
        
        data = {
            'timeframe': timeframe,
            'revenue': [{
                'date': t.timestamp.strftime('%Y-%m-%d'), 
                'description': getattr(t, 'description', getattr(t, 'name', 'Revenue')), 
                'amount': t.amount
            } for t in revenue],
            'fixed_costs': [{
                'date': t.timestamp.strftime('%Y-%m-%d'), 
                'description': getattr(t, 'description', getattr(t, 'name', 'Fixed Cost')), 
                'amount': t.amount
            } for t in fixed],
            'variable_costs': [{
                'date': t.timestamp.strftime('%Y-%m-%d'), 
                'description': getattr(t, 'description', getattr(t, 'name', 'Variable Cost')), 
                'amount': t.amount
            } for t in variable],
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
        
        # CHANGED: Added user_id filter and debug print
        print(f"Fetching sales trends for user {current_user.id}")
        
        if timeframe == 'month':
            start_date = end_date - relativedelta(months=1)
            date_format = '%Y-%m-%d'
            group_expr = func.date(Revenue.timestamp)
        elif timeframe == 'quarter':
            start_date = end_date - relativedelta(months=3)
            date_format = '%Y-%m-%W'
            group_expr = func.concat(
                func.year(Revenue.timestamp), 
                '-', 
                func.lpad(func.week(Revenue.timestamp), 2, '0'))
        elif timeframe == 'year':
            start_date = end_date - relativedelta(years=1)
            date_format = '%Y-%m'
            group_expr = func.date_format(Revenue.timestamp, '%Y-%m')
        else:  # all_time
            first_revenue = db.session.query(Revenue).filter_by(
                user_id=current_user.id
            ).order_by(Revenue.timestamp.asc()).first()
            if not first_revenue:
                return jsonify({'error': 'No revenue data available'})
            start_date = first_revenue.timestamp
            date_format = '%Y'
            group_expr = func.year(Revenue.timestamp)

        # CHANGED: Added explicit user_id filter
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

        # Generate plot with improved styling
        plt.figure(figsize=(10, 5), facecolor='#121212')
        ax = plt.axes()
        ax.set_facecolor('#1e1e1e')
        
        # CHANGED: Improved chart styling
        plt.plot(periods, amounts, marker='o', color='#00e5ff', linewidth=2, markersize=8)
        plt.title(f'Sales Trends - {timeframe.replace("_", " ").title()}', 
                 color='white', pad=20, fontsize=14)
        plt.xlabel('Period', color='white')
        plt.ylabel('Revenue (₹)', color='white')
        plt.xticks(rotation=45, color='white')
        plt.yticks(color='white')
        plt.grid(True, linestyle='--', alpha=0.3, color='#555')
        
        # Set spine colors
        for spine in ax.spines.values():
            spine.set_color('#00e5ff')
            
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', transparent=False, dpi=120, 
                   facecolor='#121212', edgecolor='none')
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
        # CHANGED: Added explicit user_id filtering
        total_fixed = db.session.query(func.sum(FixedCost.amount)).filter(
            FixedCost.user_id == current_user.id
        ).scalar() or 0
        
        total_variable = db.session.query(func.sum(VariableCost.amount)).filter(
            VariableCost.user_id == current_user.id
        ).scalar() or 0
        
        if total_fixed == 0 and total_variable == 0:
            return render_template('visualization/cost_breakdown.html',
                                plot_url=None,
                                fixed_costs=0,
                                variable_costs=0)
        
        # CHANGED: Completely redesigned pie chart
        plt.figure(figsize=(8, 8), facecolor='#121212')
        
        # Create gradient colors
        colors = ['#4e79a7', '#f28e2b']
        explode = (0.05, 0)
        
        wedges, texts, autotexts = plt.pie(
            [total_fixed, total_variable],
            labels=['Fixed Costs', 'Variable Costs'],
            colors=colors,
            autopct=lambda p: f'{p:.1f}%\n({p*sum([total_fixed,total_variable])/100:,.2f} ₹)',
            startangle=90,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
            textprops={'color': 'white', 'fontsize': 12},
            explode=explode,
            shadow=True,
            pctdistance=0.85
        )
        
        # Improve autopct styling
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
        
        # Add center circle
        centre_circle = plt.Circle((0,0), 0.70, fc='#121212')
        plt.gca().add_artist(centre_circle)
        
        # Add title and legend
        plt.title('Cost Breakdown\n', color='white', fontsize=14, fontweight='bold', y=1.05)
        plt.legend(
            [f'Fixed: ₹{total_fixed:,.2f}', f'Variable: ₹{total_variable:,.2f}'],
            loc='upper right',
            bbox_to_anchor=(1.3, 1),
            frameon=False,
            labelcolor='white'
        )
        
        # Equal aspect ratio
        plt.axis('equal')
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(
            buffer,
            format='png',
            dpi=120,
            bbox_inches='tight',
            facecolor='#121212',
            edgecolor='none'
        )
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return render_template('visualization/cost_breakdown.html',
                            plot_url=plot_data,
                            fixed_costs=total_fixed,
                            variable_costs=total_variable)
    except Exception as e:
        current_app.logger.error(f"Error generating cost breakdown: {str(e)}")
        abort(500, description="Error generating cost breakdown")

# CHANGED: Added debug endpoint
@visualization_bp.route('/debug/revenue')
@login_required
def debug_revenue():
    """Debug endpoint to check revenue data"""
    revenues = Revenue.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'count': len(revenues),
        'revenues': [{
            'id': r.id,
            'amount': r.amount,
            'timestamp': r.timestamp.isoformat(),
            'description': r.description
        } for r in revenues]
    })