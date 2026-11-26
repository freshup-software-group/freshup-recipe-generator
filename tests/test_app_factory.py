"""Smoke tests for the app skeleton (F4, #19)."""
from app import create_app


def test_testing_config_loaded():
    app = create_app("testing")
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"


def test_all_blueprints_registered():
    app = create_app("testing")
    assert {"auth", "pantry", "recipes", "shopping"} <= set(app.blueprints)


def test_home_page_responds():
    app = create_app("testing")
    assert app.test_client().get("/").status_code == 200
