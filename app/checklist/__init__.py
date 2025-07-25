from flask import Blueprint
checklist_bp = Blueprint('checklist', __name__)
from . import routes
