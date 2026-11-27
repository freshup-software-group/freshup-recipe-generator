# Tests for the recipe details page (UC-09, #12)
from app.extensions import db
from app.models import Recipe, RecipeIngredient


# Save a recipe in the test database and return it
def add_recipe(title="Garlic pasta", names=("pasta", "garlic")):
    recipe = Recipe(
        title=title,
        instructions="Boil the pasta.",
        ingredients=[
            RecipeIngredient(ingredient_name=name, normalized_name=name)
            for name in names
        ],
    )
    db.session.add(recipe)
    db.session.commit()
    return recipe


# A recipe that does not exist shows the 404 page
def test_missing_recipe_shows_404(client):
    response = client.get("/recipes/99999")
    assert response.status_code == 404
    assert b"Page not found" in response.data


# An existing recipe opens and shows its title
def test_recipe_page_shows_title(client):
    recipe = add_recipe()
    response = client.get(f"/recipes/{recipe.id}")
    assert response.status_code == 200
    assert b"Garlic pasta" in response.data


# The page lists the ingredients and shows the instructions
def test_recipe_page_shows_ingredients_and_instructions(client):
    recipe = add_recipe()
    response = client.get(f"/recipes/{recipe.id}")
    assert b"<li>pasta</li>" in response.data
    assert b"<li>garlic</li>" in response.data
    assert b"Boil the pasta." in response.data


# A guest is told to log in to compare with their pantry
def test_guest_sees_log_in_note(client):
    recipe = add_recipe()
    response = client.get(f"/recipes/{recipe.id}")
    assert b"Log in to see which ingredients you already have" in response.data


# A logged-in user does not see the guest note
def test_logged_in_user_has_no_guest_note(logged_in_client):
    recipe = add_recipe()
    response = logged_in_client.get(f"/recipes/{recipe.id}")
    assert b"Log in to see which ingredients you already have" not in response.data
