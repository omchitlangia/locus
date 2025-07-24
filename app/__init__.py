from flask import Flask
from app.extensions import db, bcrypt, mail, login_manager
from flask_migrate import Migrate
from config import Config 
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.dataentry.routes import dataentry_bp
    app.register_blueprint(dataentry_bp)

    from app.dashboard.routes import dash_bp
    app.register_blueprint(dash_bp)

    from app.optimization.routes import opt_bp
    app.register_blueprint(opt_bp)

    from app.visualization.routes import visualization_bp
    app.register_blueprint(visualization_bp)

    from app.forecasting.routes import forecast_bp
    app.register_blueprint(forecast_bp)

    from app.ep.routes import event_bp
    app.register_blueprint(event_bp)

    from app.sku.routes import sku_bp
    app.register_blueprint(sku_bp)

    from app.achievements.routes import bp as achievements_bp
    app.register_blueprint(achievements_bp)

    from app.billing.routes import billing_bp
    app.register_blueprint(billing_bp)

    from app.business_health.routes import health_bp
    app.register_blueprint(health_bp)

    from app.profilepage.routes import profile_bp
    app.register_blueprint(profile_bp)
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    from app.daily_streak.routes import streak_bp
    app.register_blueprint(streak_bp)
    return app