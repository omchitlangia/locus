from flask import Blueprint

# Add the prefix here instead of during registration
sku_bp = Blueprint('sku', __name__)

from . import routes  # Keep this import after creating the blueprint