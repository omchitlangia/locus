from flask import Blueprint

streak_bp = Blueprint(
    'daily_streak',
    __name__,
    template_folder='../templates'   # points to the root-level templates folder
)
