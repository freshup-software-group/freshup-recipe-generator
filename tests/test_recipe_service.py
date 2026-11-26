"""Tests for search_recipes(), using the shared app fixture (in-memory DB)."""
from contextlib import contextmanager

import pytest
from sqlalchemy import event

from app.extensions import db
from app.models import Recipe, RecipeIngredient
from app.recipes.search import EMPTY_INPUT_MESSAGE
from app.recipes.service import search_recipes


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
