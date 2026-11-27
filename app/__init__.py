"""Application factory."""
import os

from flask import Flask, render_template

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
        # Home page with links to core functions (NFR-1.1, NFR-1.3)
        return render_template("index.html")

    @app.cli.command("init-db")
    def init_db():
        """Create all tables from the models."""
        db.create_all()
        print("Database tables created.")

    # Show the shared 404 and 500 pages (F7)
    from .errors import register_error_handlers
    register_error_handlers(app)

    # Register the flask load-recipes command (F6)
    from .recipe_loader import load_recipes_command
    app.cli.add_command(load_recipes_command)

    # Let templates check that a route exists before linking to it (F7.1)
    @app.context_processor
    def route_helpers():
        def has_endpoint(name):
            return name in app.view_functions
        return {"has_endpoint": has_endpoint}

    return app
