from flask import Blueprint

forecast_bp = Blueprint('forecasting', __name__, template_folder='templates')
def init_app(app):
    """Initialize the forecasting blueprint with the Flask application"""
    app.register_blueprint(forecast_bp)

    