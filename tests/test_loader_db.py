"""Database tests for the recipe loader, on an in-memory SQLite database."""
import json
from pathlib import Path
from unittest import mock

import pytest
from sqlalchemy.exc import OperationalError

from app import create_app
from app.extensions import db
from app.models import Recipe, RecipeIngredient
from app.recipe_loader import save_meals

SAMPLE_PATH = Path(__file__).parent / "data" / "themealdb_sample.json"


@pytest.fixture
def app():
    """A fresh app with an empty in-memory database for each test."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


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
