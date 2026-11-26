"""Shared error pages for the whole app (NFR-5.2)."""
from flask import render_template


def register_error_handlers(app):
    """Show the shared 404 and 500 pages instead of Flask's defaults."""

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500
