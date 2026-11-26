"""Shared pytest fixtures for all modules (F7, #18).

Imports are inside the fixtures so this file does not break the existing
tests before the app skeleton (F4) and models (F5) are merged.
"""
import pytest


@pytest.fixture
def app():
    """A Flask app using the testing config, with a fresh database."""
    from app import create_app
    from app.extensions import db

    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for sending requests to the app."""
    return app.test_client()


@pytest.fixture
def logged_in_client(app, client):
    """A test client whose session belongs to a saved test user."""
    from werkzeug.security import generate_password_hash

    from app.extensions import db
    from app.models import User

    user = User(
        email="test@example.com",
        password_hash=generate_password_hash("Password123!"),
    )
    db.session.add(user)
    db.session.commit()

    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True

    return client
