"""Tests for GET /recipes/ (the search page), using the shared client fixture."""
import pytest

from app.extensions import db
from app.models import Recipe, RecipeIngredient
from app.recipes.routes import MAX_RESULTS


def add_recipe(title, *names):
    db.session.add(Recipe(
        title=title,
        instructions="Cook it.",
        ingredients=[RecipeIngredient(ingredient_name=n, normalized_name=n) for n in names],
    ))


@pytest.fixture
def saved_recipes(app):
    add_recipe("Omelette", "egg", "milk", "butter")
    add_recipe("Boiled egg", "egg")
    add_recipe("Plain rice", "rice")
    db.session.commit()


def test_without_query_shows_empty_form(client, saved_recipes):
    response = client.get("/recipes/")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'name="ingredients"' in page
    assert "matching recipes" not in page
    assert "Omelette" not in page


def test_nav_link_reaches_the_search_page(client):
    # base.html links "Search recipes" to /recipes/.
    assert client.get("/recipes/").status_code == 200


def test_with_query_shows_ranked_results(client, saved_recipes):
    response = client.get("/recipes/", query_string={"ingredients": "Eggs, milk"})
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Showing 2 of 2 matching recipes" in page
    assert page.index("Boiled egg") < page.index("Omelette")  # best match first
    assert "Plain rice" not in page


def test_query_is_kept_in_the_form(client, saved_recipes):
    page = client.get("/recipes/?ingredients=rice").get_data(as_text=True)
    assert 'value="rice"' in page


def test_shows_at_most_max_results_but_counts_all(client, app):
    for number in range(MAX_RESULTS + 5):
        add_recipe(f"Egg dish {number:02d}", "egg")
    db.session.commit()
    page = client.get("/recipes/?ingredients=egg").get_data(as_text=True)
    assert f"Showing {MAX_RESULTS} of {MAX_RESULTS + 5} matching recipes" in page
    assert page.count("<h2>Egg dish") == MAX_RESULTS


def test_query_text_is_escaped(client, saved_recipes):
    page = client.get("/recipes/?ingredients=<script>egg").get_data(as_text=True)
    assert "<script>" not in page
