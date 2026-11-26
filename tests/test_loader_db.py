"""Database tests for the recipe loader, on an in-memory SQLite database."""
import json
from pathlib import Path
from unittest import mock

import pytest
from sqlalchemy.exc import OperationalError

from app.extensions import db
from app.models import Recipe, RecipeIngredient, ShoppingList, User
from app.recipe_loader import save_meals

SAMPLE_PATH = Path(__file__).parent / "data" / "themealdb_sample.json"

# The app fixture (fresh in-memory database per test) comes from conftest.py.


@pytest.fixture
def sample_meals():
    with SAMPLE_PATH.open(encoding="utf-8") as f:
        return json.load(f)["meals"]


def recipe_by_external_id(external_id):
    return Recipe.query.filter_by(external_id=external_id).one()


def test_saves_valid_meals_and_skips_invalid_one(app, sample_meals):
    summary = save_meals(sample_meals)
    assert summary == {"created": 2, "updated": 0, "skipped": ["99990001"]}
    assert sorted(r.external_id for r in Recipe.query.all()) == ["52767", "53150"]


def test_saves_recipe_fields(app, sample_meals):
    save_meals(sample_meals)
    tart = recipe_by_external_id("52767")
    assert tart.title == "Bakewell tart"
    assert tart.instructions.startswith("To make the pastry")
    assert (tart.meal_type, tart.diet_tags) == ("dessert", "")
    assert (tart.cuisine, tart.source_url) == ("British", None)
    assert tart.image_url.endswith(".jpg")


def test_saves_diet_tags_as_comma_separated_text(app, sample_meals):
    save_meals(sample_meals)
    peppers = recipe_by_external_id("53150")
    assert (peppers.meal_type, peppers.diet_tags) == (None, "vegan,vegetarian")


def test_saves_ingredients_with_raw_and_normalized_names(app, sample_meals):
    save_meals(sample_meals)
    tart = recipe_by_external_id("52767")
    assert len(tart.ingredients) == 10
    [egg] = [item for item in tart.ingredients if item.normalized_name == "free-range egg"]
    assert (egg.ingredient_name, egg.quantity, egg.unit) == ("free-range egg", "1, beaten", None)
    assert "ground almond" in tart.ingredient_names  # property used by recipe search


def test_skips_meals_missing_title_or_id(app):
    meals = [
        {"idMeal": "1", "strMeal": "  ", "strInstructions": "Cook."},
        {"idMeal": "", "strMeal": "No id", "strInstructions": "Cook."},
    ]
    summary = save_meals(meals)
    assert summary == {"created": 0, "updated": 0, "skipped": ["1", "(no id) No id"]}
    assert Recipe.query.count() == 0


def test_empty_quantity_is_stored_as_null(app):
    meal = {"idMeal": "2", "strMeal": "Toast", "strInstructions": "Toast it.",
            "strIngredient1": "Bread", "strMeasure1": " "}
    save_meals([meal])
    assert RecipeIngredient.query.one().quantity is None


def test_no_meals_saves_nothing(app):
    assert save_meals([]) == {"created": 0, "updated": 0, "skipped": []}
    assert Recipe.query.count() == 0


def test_database_error_saves_nothing(app, sample_meals):
    error = OperationalError("COMMIT", {}, Exception("disk full"))
    with mock.patch.object(db.session, "commit", side_effect=error):
        with pytest.raises(OperationalError):
            save_meals(sample_meals)
    assert Recipe.query.count() == 0
    assert RecipeIngredient.query.count() == 0


def test_second_run_updates_instead_of_duplicating(app, sample_meals):
    save_meals(sample_meals)
    ids_before = {r.external_id: r.id for r in Recipe.query.all()}

    summary = save_meals(sample_meals)

    assert summary == {"created": 0, "updated": 2, "skipped": ["99990001"]}
    assert Recipe.query.count() == 2
    assert RecipeIngredient.query.count() == 12  # 10 + 2, not doubled
    # Same primary keys: the rows were updated, not replaced.
    assert {r.external_id: r.id for r in Recipe.query.all()} == ids_before


def test_update_applies_changed_data(app, sample_meals):
    save_meals(sample_meals)
    changed = dict(sample_meals[1], strMeal="Padron peppers (new)",
                   strIngredient2="Green Peppers", strMeasure2="400g")

    save_meals([changed])

    peppers = recipe_by_external_id("53150")
    assert peppers.title == "Padron peppers (new)"
    assert [(i.normalized_name, i.quantity) for i in peppers.ingredients] == [
        ("olive oil", "1 tablespoon"), ("green pepper", "400g"),
    ]
    assert RecipeIngredient.query.filter_by(normalized_name="padron pepper").count() == 0


def test_recipes_missing_from_a_later_run_are_kept(app, sample_meals):
    save_meals(sample_meals)
    save_meals(sample_meals[:1])  # only Bakewell tart this time
    assert sorted(r.external_id for r in Recipe.query.all()) == ["52767", "53150"]


def test_saved_shopping_list_still_points_at_updated_recipe(app, sample_meals):
    save_meals(sample_meals)
    peppers = recipe_by_external_id("53150")
    user = User(email="cook@example.com", password_hash="x")
    db.session.add(ShoppingList(user=user, recipe=peppers, recipe_title=peppers.title))
    db.session.commit()

    save_meals(sample_meals)

    shopping_list = ShoppingList.query.one()
    assert shopping_list.recipe is recipe_by_external_id("53150")


def test_repeated_id_in_one_batch_is_saved_once(app, sample_meals):
    summary = save_meals([sample_meals[1], sample_meals[1]])
    assert (summary["created"], summary["updated"]) == (1, 1)
    assert Recipe.query.count() == 1
