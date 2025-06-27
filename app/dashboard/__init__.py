from .routes import dash_bp

def init_app(app):
    app.register_blueprint(dash_bp, url_prefix='/dashboard')