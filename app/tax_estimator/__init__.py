from flask import Blueprint

tax_bp = Blueprint('tax_estimator', __name__, template_folder='templates')

def init_app(app):
    app.register_blueprint(tax_bp)
