# app/dataentry/__init__.py
from flask import Blueprint

dataentry_bp = Blueprint('dataentry', __name__, template_folder='templates')

def init_app(app):
    app.register_blueprint(dataentry_bp)