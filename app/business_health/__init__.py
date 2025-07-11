# app/business_health/__init__.py
from flask import Blueprint

health_bp = Blueprint('business_health', __name__, template_folder='templates')

from . import routes  # This import must come AFTER the blueprint creation

def init_app(app):
    """Initialize the business health blueprint with the Flask application"""
    app.register_blueprint(health_bp)