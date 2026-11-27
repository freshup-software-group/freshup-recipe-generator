import pytest

from app.extensions import db
from app.models import Recipe, RecipeIngredient, ShoppingList, User


def auth_is_wired(app):
    """UC-01 to UC-03 are Percy's work; these tests run once his routes land."""
    return "auth.login" in app.view_functions


needs_auth = pytest.mark.skipif(
    True, reason="waiting on the auth blueprint (UC-02)"
)


@pytest.fixture
def recipe_id(app):
    with app.app_context():
        recipe = Recipe(title="Tomato Pasta", instructions="Boil, mix, serve.")
        recipe.ingredients.append(
            RecipeIngredient(ingredient_name="Tomatoes", normalized_name="tomato")
        )
        db.session.add(recipe)
        db.session.commit()
        return recipe.id


@pytest.fixture
def signed_in(app, client):
    """Log a user in through the session, without depending on the auth routes."""
    with app.app_context():
        user = User(email="cook@example.com", password_hash="x")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True

    return client


def test_a_guest_can_generate_a_list(client, recipe_id):
    response = client.get(f"/shopping/generate/{recipe_id}")

    assert response.status_code == 200
    assert b"Tomatoes" in response.data


def test_an_unknown_recipe_returns_404(client):
    assert client.get("/shopping/generate/99999").status_code == 404


def test_a_signed_in_user_can_save_and_see_the_list(signed_in, recipe_id):
    saved = signed_in.post(f"/shopping/save/{recipe_id}", follow_redirects=True)
    assert saved.status_code == 200
    assert b"Tomatoes" in saved.data

    listing = signed_in.get("/shopping/lists")
    assert listing.status_code == 200
    assert b"Tomato Pasta" in listing.data


def test_opening_a_list_that_does_not_exist_returns_404(signed_in):
    assert signed_in.get("/shopping/lists/99999").status_code == 404


def test_removing_an_item_updates_the_page(signed_in, recipe_id, app):
    signed_in.post(f"/shopping/save/{recipe_id}", follow_redirects=True)

    with app.app_context():
        shopping_list = ShoppingList.query.one()
        list_id = shopping_list.id
        item_id = shopping_list.items[0].id

    before = signed_in.get(f"/shopping/lists/{list_id}")
    assert b"Tomatoes" in before.data

    removed = signed_in.post(
        f"/shopping/lists/{list_id}/items/{item_id}/remove",
        follow_redirects=True,
    )
    assert removed.status_code == 200
    assert b"Tomatoes" not in removed.data

    after = signed_in.get(f"/shopping/lists/{list_id}")
    assert b"Tomatoes" not in after.data


@needs_auth
def test_a_guest_is_redirected_when_saving(client, recipe_id):
    response = client.post(f"/shopping/save/{recipe_id}")

    assert response.status_code in (301, 302)
    assert "login" in response.headers["Location"]


@needs_auth
def test_a_guest_is_redirected_from_saved_lists(client):
    response = client.get("/shopping/lists")

    assert response.status_code in (301, 302)
    assert "login" in response.headers["Location"]
