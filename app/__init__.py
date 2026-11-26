"""Application factory."""
import os

from flask import Flask

from .config import config_by_name
from .extensions import db, login_manager


def create_app(config_name=None):
    """Build and return a configured Flask app.

    config_name: "development", "testing" or "production".
    Falls back to FLASK_CONFIG, then FLASK_ENV (set in docker-compose and
    CI), then "development".
    """
    config_name = (
        config_name
        or os.environ.get("FLASK_CONFIG")
        or os.environ.get("FLASK_ENV")
        or "development"
    )
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    login_manager.init_app(app)

    from .auth import bp as auth_bp
    from .pantry import bp as pantry_bp
    from .recipes import bp as recipes_bp
    from .shopping import bp as shopping_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(pantry_bp, url_prefix="/pantry")
    app.register_blueprint(recipes_bp, url_prefix="/recipes")
    app.register_blueprint(shopping_bp, url_prefix="/shopping")

    @app.route("/")
    def index():
        return "Freshup Recipe Generator is running."

    @app.cli.command("init-db")
    def init_db():
        """Create all tables from the models."""
        db.create_all()
        print("Database tables created.")

    return app
