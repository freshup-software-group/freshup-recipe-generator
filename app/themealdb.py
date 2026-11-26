"""Turn TheMealDB API data (https://www.themealdb.com) into Freshup recipe data."""
import json
import string
from typing import NamedTuple
from urllib.request import Request, urlopen

from app.common.ingredients import normalize_ingredient

# Official API, free test key "1" (educational use). One request per first letter.
SEARCH_URL = "https://www.themealdb.com/api/json/v1/1/search.php?f={letter}"
REQUEST_TIMEOUT_SECONDS = 10
# Generic client name; urllib's default "Python-urllib/x.y" is blocked by some servers.
USER_AGENT = "recipe-loader/1.0"

# TheMealDB stores ingredients in numbered slots strIngredient1..20 / strMeasure1..20.
MAX_INGREDIENT_SLOTS = 20

# TheMealDB has one strCategory per meal. Some categories give a meal type, some a
# diet tag; the rest (Miscellaneous, unknown names) map to neither.
MAIN_DISH_CATEGORIES = {"beef", "chicken", "seafood", "pork", "lamb", "goat", "pasta"}
MEAL_TYPE_BY_CATEGORY = {
    "breakfast": "breakfast",
    "dessert": "dessert",
    "starter": "starter",
    "side": "side",
    **{category: "main" for category in MAIN_DISH_CATEGORIES},
}
# Vegan food is also vegetarian, so a "vegetarian" filter must find vegan recipes.
DIET_TAGS_BY_CATEGORY = {
    "vegetarian": ["vegetarian"],
    "vegan": ["vegan", "vegetarian"],
}


def _clean(value):
    """Return value trimmed, treating None (JSON null) as an empty string."""
    return (value or "").strip()


class ParsedIngredient(NamedTuple):
    """One recipe ingredient; field names match the RecipeIngredient columns."""

    ingredient_name: str  # as written by TheMealDB, before any comma
    normalized_name: str  # normalize_ingredient(ingredient_name), used for matching
    quantity: str         # measure plus any comma note, "" if neither


def _parse_ingredient(raw_name, raw_measure):
    """Return a ParsedIngredient for one slot, or None if the slot is unused.

    A note after the first comma ("egg, beaten") is moved into the quantity
    text ("1, beaten") so the name matches the pantry but nothing is lost.
    """
    name_part, _, note = _clean(raw_name).partition(",")
    ingredient_name = name_part.strip()
    normalized_name = normalize_ingredient(ingredient_name)
    if not normalized_name:
        return None
    quantity_parts = [part for part in (_clean(raw_measure), note.strip()) if part]
    return ParsedIngredient(ingredient_name, normalized_name, ", ".join(quantity_parts))


def map_category(category):
    """Map a TheMealDB strCategory to a Freshup meal_type and diet_tags list."""
    key = _clean(category).lower()
    return {
        "meal_type": MEAL_TYPE_BY_CATEGORY.get(key),
        # list() returns a copy, so callers can't modify the shared constant.
        "diet_tags": list(DIET_TAGS_BY_CATEGORY.get(key, [])),
    }


def parse_meal(meal):
    """Convert one meal dict from the API into recipe data (no database access)."""
    ingredients = []
    for slot in range(1, MAX_INGREDIENT_SLOTS + 1):
        ingredient = _parse_ingredient(
            meal.get(f"strIngredient{slot}"), meal.get(f"strMeasure{slot}")
        )
        if ingredient is not None:
            ingredients.append(ingredient)
    return {
        "external_id": _clean(meal.get("idMeal")),
        "title": _clean(meal.get("strMeal")),
        "instructions": _clean(meal.get("strInstructions")),
        "ingredients": ingredients,
    }


class TheMealDBError(Exception):
    """TheMealDB could not be reached or sent a response we cannot use."""


def _fetch_letter(letter):
    """Return the list of raw meal dicts whose name starts with letter."""
    url = SEARCH_URL.format(letter=letter)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except OSError as error:
        # OSError covers URLError, HTTPError, timeouts and dropped connections.
        raise TheMealDBError(f"Could not reach TheMealDB ({url}): {error}") from error
    except ValueError as error:
        # ValueError covers invalid JSON and undecodable bytes.
        raise TheMealDBError(f"TheMealDB sent invalid JSON ({url}): {error}") from error

    if not isinstance(payload, dict) or "meals" not in payload:
        raise TheMealDBError(f"TheMealDB sent an unexpected response ({url})")
    meals = payload["meals"]
    if meals is None:
        return []  # {"meals": null} means no meal starts with this letter
    if not isinstance(meals, list):
        raise TheMealDBError(f"TheMealDB sent an unexpected response ({url})")
    return meals


def fetch_all_meals():
    """Download every meal (letters a-z) and return them as one list.

    All or nothing: if any request fails, TheMealDBError is raised and no meals
    are returned, so the caller never saves a partial dataset.
    """
    meals = []
    for letter in string.ascii_lowercase:
        meals.extend(_fetch_letter(letter))
    return meals
