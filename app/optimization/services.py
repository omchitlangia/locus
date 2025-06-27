from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus

def calculate_roi(selling_price: float, units_sold: float, cost: float) -> dict:
    """
    Calculate ROI with comprehensive error handling
    Returns: {
        'revenue': float,
        'net_profit': float,
        'roi': float,
        'error': str (if any)
    }
    """
    try:
        if cost <= 0:
            return {'error': 'Cost must be greater than zero'}
            
        revenue = selling_price * units_sold
        net_profit = revenue - cost
        roi = (net_profit / cost) * 100
        
        return {
            'revenue': round(revenue, 2),
            'net_profit': round(net_profit, 2),
            'roi': round(roi, 2)
        }
    except Exception as e:
        return {'error': f'Calculation error: {str(e)}'}

def optimize_budget(total_budget: float, campaigns: list) -> dict:
    """
    Optimize budget allocation using linear programming
    Returns: {
        'allocations': list[dict],
        'total_allocated': float,
        'total_roi': float,
        'status': str,
        'error': str (if any)
    }
    """
    try:
        # Validate inputs
        if total_budget <= 0:
            return {'error': 'Total budget must be positive'}
        if not campaigns:
            return {'error': 'At least one campaign required'}

        # Create optimization problem
        prob = LpProblem("BudgetAllocation", LpMaximize)
        
        # Create decision variables
        vars = []
        for i, campaign in enumerate(campaigns):
            vars.append(LpVariable(
                name=f"campaign_{i}",
                lowBound=0,
                upBound=campaign['max_allocation']
            ))
        
        # Objective function: Maximize total ROI
        prob += lpSum(
            var * (campaigns[i]['roi_percent'] / 100)
            for i, var in enumerate(vars)
        )
        
        # Constraint: Total budget
        prob += lpSum(vars) <= total_budget
        
        # Solve the problem
        status_code = prob.solve()
        
        # Prepare results
        allocations = []
        for i, var in enumerate(vars):
            allocations.append({
                'name': campaigns[i]['name'],
                'allocation': round(var.varValue, 2),
                'roi_percent': round(campaigns[i]['roi_percent'], 1),
                'roi_contribution': round(var.varValue * (campaigns[i]['roi_percent'] / 100), 2)
            })
        
        return {
            'allocations': allocations,
            'total_allocated': round(sum(a['allocation'] for a in allocations), 2),
            'total_roi': round(sum(a['roi_contribution'] for a in allocations), 2),
            'status': LpStatus[status_code]
        }
        
    except Exception as e:
        return {'error': f'Optimization error: {str(e)}'}