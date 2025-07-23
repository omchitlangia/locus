from flask import Blueprint

bp = Blueprint('achievements', __name__)

from app.achievements import routes