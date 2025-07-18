from flask import Blueprint

profile_bp = Blueprint('profile', __name__, template_folder='templates')

def init_app(app):
    """Initialize the profile blueprint with the Flask application"""
    app.register_blueprint(profile_bp)