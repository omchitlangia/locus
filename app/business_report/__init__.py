from flask import Blueprint

report_bp = Blueprint(
    'business_report',
    __name__,
    template_folder='templates',
)

def init_app(app):
    app.register_blueprint(report_bp)
