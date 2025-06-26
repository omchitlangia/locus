from flask import Blueprint

event_bp = Blueprint('event', __name__, template_folder='templates')  # Changed to 'event'

def init_app(app):
    app.register_blueprint(event_bp)  # Added url_prefix