def test_pantry_page_requires_login(client):
    response = client.get("/pantry/")

    assert response.status_code == 302


def test_logged_in_user_can_view_pantry(logged_in_client):
    response = logged_in_client.get("/pantry/")

    assert response.status_code == 200
    assert b"Your Pantry" in response.data
    assert b"Your ingredients" in response.data


def test_logged_in_user_can_add_ingredient(logged_in_client):
    response = logged_in_client.post(
        "/pantry/",
        data={"ingredient_name": "Tomatoes"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Tomatoes" in response.data
    assert b"Ingredient added to your pantry." in response.data


def test_duplicate_ingredient_is_rejected(logged_in_client):
    logged_in_client.post(
        "/pantry/",
        data={"ingredient_name": "Tomatoes"},
    )

    response = logged_in_client.post(
        "/pantry/",
        data={"ingredient_name": "Tomato"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"already in your pantry" in response.data


def test_empty_ingredient_is_rejected(logged_in_client):
    response = logged_in_client.post(
        "/pantry/",
        data={"ingredient_name": "   "},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Please enter an ingredient name." in response.data
