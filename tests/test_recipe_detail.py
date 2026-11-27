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
