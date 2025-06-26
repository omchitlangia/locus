from flask import Blueprint

visualization_bp = Blueprint('visualization', __name__, template_folder='templates')

def init_app(app):
    app.register_blueprint(visualization_bp)