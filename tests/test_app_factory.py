import os

"""Smoke tests for the app skeleton (F4, #19)."""
from app import create_app


def test_testing_config_loaded():
    app = create_app("testing")
    assert app.config["TESTING"] is True
    # The URI comes from DATABASE_URL, so CI runs the suite against the same
    # PostgreSQL engine as production. It falls back to in-memory SQLite for a
    # quick local run with no database running.
    expected = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    assert app.config["SQLALCHEMY_DATABASE_URI"] == expected


def test_all_blueprints_registered():
    app = create_app("testing")
    assert {"auth", "pantry", "recipes", "shopping"} <= set(app.blueprints)


def test_home_page_responds():
    app = create_app("testing")
    assert app.test_client().get("/").status_code == 200
