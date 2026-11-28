# Tests for the home page (F7.1, #27)
import re

import pytest


# All the links on a page
def get_links(response):
    return re.findall(r'href="([^"]+)"', response.get_data(as_text=True))


# Home page uses the base layout and shows the intro (NFR-1.3)
def test_home_page_uses_base_layout(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'class="nav"' in response.data
    assert b"Find recipes with what you already have" in response.data


# The search card links to the real search page (NFR-1.1)
def test_search_card_links_to_search_page(client):
    response = client.get("/")
    assert b'href="/recipes/"' in response.data


# Every link a guest sees opens without an error
def test_guest_sees_no_dead_links(client):
    for link in get_links(client.get("/")):
        assert client.get(link).status_code < 400, link


# Every link a logged-in user sees opens without an error
def test_logged_in_user_sees_no_dead_links(logged_in_client):
    for link in get_links(logged_in_client.get("/")):
        assert logged_in_client.get(link).status_code < 400, link


# The pantry card only shows once the pantry page exists
def test_pantry_card_only_when_route_exists(app, logged_in_client):
    response = logged_in_client.get("/")
    has_pantry = "pantry.index" in app.view_functions
    assert (b"Go to my pantry" in response.data) == has_pantry


# The old skeleton placeholder text is gone
def test_placeholder_text_is_gone(client):
    response = client.get("/")
    assert b"Freshup Recipe Generator is running." not in response.data


# A guest is invited to register or log in
def test_guest_sees_register_prompt(app, client):
    # Skipped until the auth routes are merged (UC-01, UC-02)
    if "auth.register" not in app.view_functions:
        pytest.skip("auth routes not merged yet")
    response = client.get("/")
    assert b"Create an account" in response.data


# A logged-in user does not see the register prompt
def test_logged_in_user_has_no_register_prompt(logged_in_client):
    response = logged_in_client.get("/")
    assert b"Create an account" not in response.data
