# Tests for the shared UI shell (F7, #18): layout, nav, flash and errors.
import pytest
from flask import flash, render_template_string

PAGE = '{% extends "base.html" %}{% block content %}Hello{% endblock %}'


# Unknown pages show the shared 404 page inside the base layout.
def test_unknown_page_shows_404_page(client):
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404
    assert b"Page not found" in response.data


# The 404 page uses base.html, so the nav bar is there (NFR-1.3).
def test_error_page_has_nav_bar(client):
    response = client.get("/this-page-does-not-exist")
    assert b'class="nav"' in response.data
    assert b"Search recipes" in response.data


# A visitor who is not logged in sees Log in and Register.
def test_guest_sees_login_and_register(app, client):
    # Skipped until the auth routes are merged (UC-01, UC-02)
    if "auth.login" not in app.view_functions:
        pytest.skip("auth routes not merged yet")
    response = client.get("/this-page-does-not-exist")
    assert b"Log in" in response.data
    assert b"Register" in response.data
    assert b"Log out" not in response.data


# Unexpected errors show the shared 500 page (NFR-5.2).
def test_server_error_shows_500_page(app):
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.route("/boom")
    def boom():
        raise RuntimeError("boom")

    response = app.test_client().get("/boom")
    assert response.status_code == 500
    assert b"Something went wrong" in response.data


# Flash messages appear on any page that extends base.html.
def test_flash_message_is_rendered(app):
    with app.test_request_context():
        flash("Ingredient added", "success")
        html = render_template_string(PAGE)
    assert "Ingredient added" in html
    assert "flash-success" in html


# Pages that extend base.html keep their own content.
def test_page_content_goes_in_content_block(app):
    with app.test_request_context():
        html = render_template_string(PAGE)
    assert "Hello" in html


# The shared stylesheet is served.
def test_stylesheet_is_served(client):
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
