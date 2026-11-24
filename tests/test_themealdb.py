import json
from pathlib import Path

import pytest

from app.themealdb import parse_meal

SAMPLE_PATH = Path(__file__).parent / "data" / "themealdb_sample.json"


@pytest.fixture
def sample_meals():
    """Meals from the saved API sample, keyed by idMeal."""
    with SAMPLE_PATH.open(encoding="utf-8") as f:
        return {meal["idMeal"]: meal for meal in json.load(f)["meals"]}


def make_meal(ingredients):
    """Build a minimal API meal dict from a list of (ingredient, measure) slots."""
    meal = {"idMeal": "1", "strMeal": "Test meal", "strInstructions": "Cook it."}
    for slot, (name, measure) in enumerate(ingredients, start=1):
        meal[f"strIngredient{slot}"] = name
        meal[f"strMeasure{slot}"] = measure
    return meal


def test_parses_recipe_fields(sample_meals):
    recipe = parse_meal(sample_meals["53150"])
    assert recipe["external_id"] == "53150"
    assert recipe["title"] == "Padron peppers"
    assert recipe["instructions"].startswith("step 1")


def test_name_without_comma_is_normalized_and_measure_kept(sample_meals):
    ingredients = parse_meal(sample_meals["52767"])["ingredients"]
    assert ("ground almond", "125g/4½oz") in ingredients  # ½ is "½"


def test_name_with_comma_moves_note_into_quantity(sample_meals):
    ingredients = parse_meal(sample_meals["52767"])["ingredients"]
    assert ("free-range egg", "1, beaten") in ingredients


def test_comma_note_with_empty_measure_becomes_quantity():
    recipe = parse_meal(make_meal([("Garlic, crushed", " ")]))
    assert recipe["ingredients"] == [("garlic", "crushed")]


def test_unused_slots_are_skipped(sample_meals):
    # Bakewell tart: slots 1-10 used, 11-15 are "" and 16-20 are null.
    assert len(parse_meal(sample_meals["52767"])["ingredients"]) == 10
    # Padron peppers: slots 3-20 have "" names and " " measures.
    assert len(parse_meal(sample_meals["53150"])["ingredients"]) == 2


def test_whitespace_only_and_null_names_are_skipped():
    meal = make_meal([("   ", "1 tsp"), (None, None), ("Salt", "Pinch")])
    assert parse_meal(meal)["ingredients"] == [("salt", "Pinch")]
