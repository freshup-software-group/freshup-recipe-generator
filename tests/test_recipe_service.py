"""Tests for recipe services: search_recipes() (UC-08, #3) and get_recipe helpers (UC-09, #12)."""
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from sqlalchemy import event

from app.extensions import db
from app.models import Recipe, RecipeIngredient
from app.recipes.search import EMPTY_INPUT_MESSAGE
from app.recipes.service import RecipeDetails, search_recipes, to_details


# ---------- search_recipes (UC-08) ----------

def add_recipe(title, *names):
    recipe = Recipe(
        title=title,
        instructions="Cook it.",
        ingredients=[
            RecipeIngredient(ingredient_name=name, normalized_name=name) for name in names
        ],
    )
    db.session.add(recipe)
    return recipe


@pytest.fixture
def saved_recipes(app):
    add_recipe("Omelette", "egg", "milk", "butter")
    add_recipe("Boiled egg", "egg")
    add_recipe("Rice pudding", "rice", "milk", "sugar")
    add_recipe("Plain rice", "rice")
    db.session.commit()


@contextmanager
def count_queries():
    """Count the SQL statements run inside the with-block."""
    statements = []

    def record(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", record)
    try:
        yield statements
    finally:
        event.remove(db.engine, "before_cursor_execute", record)


def test_returns_ranked_results_from_the_database(saved_recipes):
    results = search_recipes("Eggs, milk")
    assert [r.title for r in results] == ["Boiled egg", "Omelette", "Rice pudding"]
    assert results[1].matched == ("egg", "milk")
    assert results[1].missing == ("butter",)


def test_recipes_without_a_match_are_left_out(saved_recipes):
    assert [r.title for r in search_recipes("rice")] == ["Plain rice", "Rice pudding"]


def test_no_match_returns_empty_list(saved_recipes):
    assert search_recipes("chocolate") == []


def test_empty_input_raises_before_querying(saved_recipes):
    with count_queries() as statements:
        with pytest.raises(ValueError, match=EMPTY_INPUT_MESSAGE):
            search_recipes("  , ")
    assert statements == []


def test_loads_ingredients_without_one_query_per_recipe(saved_recipes):
    db.session.expire_all()  # force a real reload from the database
    with count_queries() as statements:
        search_recipes("egg")
    # One query for recipes + one for all their ingredients, not 1 + 4.
    assert len(statements) == 2


# ---------- get_recipe helpers (UC-09) ----------

# Build a fake recipe row so tests do not need the database
# Pass any field to override the default
def make_recipe(**overrides):
    data = dict(
        id=1,
        title="Pasta",
        ingredients=[
            SimpleNamespace(ingredient_name="penne rigate"),
            SimpleNamespace(ingredient_name="olive oil"),
            SimpleNamespace(ingredient_name="garlic"),
        ],
        instructions="Boil the pasta",
        meal_type="dessert",
        diet_tags="vegan,vegetarian",
        cuisine="Italian",
        image_url="https://example.com/pasta.jpg",
    )
    data.update(overrides)
    return SimpleNamespace(**data)


# to_details gives back a RecipeDetails object
def test_returns_recipe_details():
    assert isinstance(to_details(make_recipe()), RecipeDetails)


# id and title are copied as they are
def test_copies_id_and_title():
    details = to_details(make_recipe(id=7, title="Soup"))
    assert details.id == 7
    assert details.title == "Soup"


# Ingredient names keep the recipe's order
def test_ingredient_names_in_order():
    details = to_details(make_recipe())
    assert details.ingredient_names == [
        "penne rigate", "olive oil", "garlic"]


# Instructions, meal type, cuisine and image are copied over
def test_copies_text_fields():
    details = to_details(make_recipe())
    assert details.instructions == "Boil the pasta"
    assert details.meal_type == "dessert"
    assert details.cuisine == "Italian"
    assert details.image_url == "https://example.com/pasta.jpg"


# diet_tags stored as text becomes a clean list
def test_diet_tags_text_becomes_list():
    details = to_details(make_recipe(diet_tags=" vegan , vegetarian "))
    assert details.diet_tags == ["vegan", "vegetarian"]


# diet_tags that is already a list stays the same
def test_diet_tags_list_is_kept():
    details = to_details(make_recipe(diet_tags=["vegan"]))
    assert details.diet_tags == ["vegan"]


# Empty database fields become "" or [] instead of None
def test_none_fields_become_empty():
    details = to_details(make_recipe(
        instructions=None,
        meal_type=None,
        diet_tags=None,
        cuisine=None,
        image_url=None,
    ))
    assert details.instructions == ""
    assert details.meal_type == ""
    assert details.diet_tags == []
    assert details.cuisine == ""
    assert details.image_url == ""


# A recipe with no ingredients gives an empty list
def test_no_ingredients_gives_empty_list():
    details = to_details(make_recipe(ingredients=[]))
    assert details.ingredient_names == []
