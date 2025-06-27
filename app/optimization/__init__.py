from flask import Blueprint

opt_bp = Blueprint(
    'optimization',
    __name__,
    template_folder='templates'
)

def init_app(app):
    app.register_blueprint(opt_bp)