"""Tests for GET /recipes/ (the search page), using the shared client fixture."""
import pytest

from app.extensions import db
from app.models import Recipe, RecipeIngredient
from app.recipes.routes import MAX_RESULTS
from app.recipes.search import EMPTY_INPUT_MESSAGE


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


def result_cards(page):
    """Split the rendered page into one HTML chunk per result, in order."""
    return page.split('<li class="card">')[1:]


def test_each_result_shows_score_as_x_of_y(client, saved_recipes):
    page = client.get("/recipes/?ingredients=egg, milk").get_data(as_text=True)
    boiled_egg, omelette = result_cards(page)
    assert "You have 1 of 1 ingredients" in boiled_egg
    assert "You have 2 of 3 ingredients" in omelette


def test_each_result_lists_matched_and_missing_ingredients(client, saved_recipes):
    page = client.get("/recipes/?ingredients=Eggs, Milk").get_data(as_text=True)
    [omelette] = [card for card in result_cards(page) if "Omelette" in card]
    assert "<strong>You have:</strong> egg, milk" in omelette
    assert "<strong>Missing:</strong> butter" in omelette


def test_full_match_says_nothing_missing(client, saved_recipes):
    page = client.get("/recipes/?ingredients=egg").get_data(as_text=True)
    [boiled_egg] = [card for card in result_cards(page) if "Boiled egg" in card]
    assert "Nothing missing" in boiled_egg
    assert "Missing:" not in boiled_egg


@pytest.mark.parametrize("text", ["", "   ", " , ,, "])
def test_empty_input_flashes_error_and_shows_form_again(client, saved_recipes, text):
    response = client.get("/recipes/", query_string={"ingredients": text})
    assert response.status_code == 200  # no crash, no 500 page
    page = response.get_data(as_text=True)
    assert f'<div class="flash flash-error" role="alert">{EMPTY_INPUT_MESSAGE}</div>' in page
    assert 'name="ingredients"' in page
    assert "matching recipes" not in page


def test_empty_input_message_is_not_repeated_on_next_page(client, saved_recipes):
    client.get("/recipes/?ingredients=")
    page = client.get("/recipes/").get_data(as_text=True)
    assert EMPTY_INPUT_MESSAGE not in page
