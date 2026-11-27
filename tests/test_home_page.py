# Tests for the home page (F7.1, #27, NFR-1.1, NFR-1.3)


# The home page loads and uses the shared layout with the nav bar
def test_home_page_uses_base_layout(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'class="nav"' in response.data
    assert b"Find recipes with what you already have" in response.data


# The home page links to the core functions
def test_home_page_links_to_core_functions(client):
    response = client.get("/")
    assert b'href="/recipes/"' in response.data
    assert b'href="/pantry/"' in response.data
    assert b'href="/shopping/"' in response.data


# The old skeleton placeholder text is gone
def test_placeholder_text_is_gone(client):
    response = client.get("/")
    assert b"Freshup Recipe Generator is running." not in response.data


# A guest is invited to register or log in
def test_guest_sees_register_prompt(client):
    response = client.get("/")
    assert b"Create an account" in response.data


# A logged-in user does not see the register prompt
def test_logged_in_user_has_no_register_prompt(logged_in_client):
    response = logged_in_client.get("/")
    assert b"Create an account" not in response.data
