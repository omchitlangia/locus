# app/currency_converter/routes.py

from flask import render_template, Blueprint
from flask_login import login_required, current_user
from . import currency_bp

@currency_bp.route('/dashboard/currency-converter', methods=['GET'])
@login_required
def converter():
    return render_template('currency_converter/converter.html')
