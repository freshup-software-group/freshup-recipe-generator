import json
from pathlib import Path

import pytest

from app.themealdb import map_category, parse_meal

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
    assert ("ground almonds", "ground almond", "125g/4½oz") in ingredients  # ½ = "½"


def test_name_with_comma_moves_note_into_quantity(sample_meals):
    ingredients = parse_meal(sample_meals["52767"])["ingredients"]
    assert ("free-range egg", "free-range egg", "1, beaten") in ingredients


def test_comma_note_with_empty_measure_becomes_quantity():
    recipe = parse_meal(make_meal([("Garlic, crushed", " ")]))
    assert recipe["ingredients"] == [("Garlic", "garlic", "crushed")]


def test_ingredient_name_keeps_original_case_before_the_comma():
    recipe = parse_meal(make_meal([("  Cherry Tomatoes , halved", "200g")]))
    assert recipe["ingredients"] == [("Cherry Tomatoes", "cherry tomato", "200g, halved")]


def test_ingredient_fields_match_model_column_names():
    [ingredient] = parse_meal(make_meal([("Eggs", "2")]))["ingredients"]
    assert ingredient.ingredient_name == "Eggs"
    assert ingredient.normalized_name == "egg"
    assert ingredient.quantity == "2"


def test_unused_slots_are_skipped(sample_meals):
    # Bakewell tart: slots 1-10 used, 11-15 are "" and 16-20 are null.
    assert len(parse_meal(sample_meals["52767"])["ingredients"]) == 10
    # Padron peppers: slots 3-20 have "" names and " " measures.
    assert len(parse_meal(sample_meals["53150"])["ingredients"]) == 2


def test_whitespace_only_and_null_names_are_skipped():
    meal = make_meal([("   ", "1 tsp"), (None, None), ("Salt", "Pinch")])
    assert parse_meal(meal)["ingredients"] == [("Salt", "salt", "Pinch")]


@pytest.mark.parametrize("category", ["Breakfast", "Dessert", "Starter", "Side"])
def test_meal_type_category_sets_meal_type(category):
    assert map_category(category) == {"meal_type": category.lower(), "diet_tags": []}


def test_vegetarian_category_sets_vegetarian_tag():
    assert map_category("Vegetarian") == {"meal_type": None, "diet_tags": ["vegetarian"]}


def test_vegan_category_is_also_tagged_vegetarian():
    assert map_category("Vegan") == {"meal_type": None, "diet_tags": ["vegan", "vegetarian"]}


def test_diet_tags_are_a_fresh_list_each_call():
    map_category("Vegan")["diet_tags"].append("changed")
    assert map_category("Vegan")["diet_tags"] == ["vegan", "vegetarian"]


@pytest.mark.parametrize(
    "category", ["Beef", "Chicken", "Seafood", "Pork", "Lamb", "Goat", "Pasta"]
)
def test_protein_and_pasta_categories_are_main(category):
    assert map_category(category) == {"meal_type": "main", "diet_tags": []}


@pytest.mark.parametrize("category", ["  BEEF ", "chicken", "\tPasta\n", " sEaFoOd"])
def test_main_category_match_ignores_case_and_whitespace(category):
    assert map_category(category)["meal_type"] == "main"


@pytest.mark.parametrize("category", ["Vegetarian", "Vegan"])
def test_diet_categories_have_no_meal_type(category):
    assert map_category(category)["meal_type"] is None


@pytest.mark.parametrize("category", ["Miscellaneous", "Unknown", "", None])
def test_other_category_sets_neither(category):
    assert map_category(category) == {"meal_type": None, "diet_tags": []}


def test_category_match_ignores_case_and_whitespace():
    assert map_category("  VEGAN ")["diet_tags"] == ["vegan", "vegetarian"]


def test_sample_meals_map_to_expected_categories(sample_meals):
    assert map_category(sample_meals["52767"]["strCategory"])["meal_type"] == "dessert"
    assert map_category(sample_meals["53150"]["strCategory"])["diet_tags"] == [
        "vegan", "vegetarian",
    ]
