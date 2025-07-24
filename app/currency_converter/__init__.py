# app/currency_converter/__init__.py

from flask import Blueprint

currency_bp = Blueprint('currency_converter',__name__,template_folder='templates' ) # correct relative path from this file


def init_app(app):
    app.register_blueprint(currency_bp)
