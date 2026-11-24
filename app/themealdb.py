"""Turn TheMealDB API data (https://www.themealdb.com) into Freshup recipe data."""
from app.utils import normalize_ingredient

# TheMealDB stores ingredients in numbered slots strIngredient1..20 / strMeasure1..20.
MAX_INGREDIENT_SLOTS = 20

# TheMealDB has one strCategory per meal. Some categories are a meal type, some a
# diet; the rest (Beef, Seafood, Pasta, Miscellaneous, ...) map to neither.
MEAL_TYPE_CATEGORIES = {"breakfast", "dessert", "starter", "side"}
DIET_TAG_CATEGORIES = {"vegetarian", "vegan"}


def _clean(value):
    """Return value trimmed, treating None (JSON null) as an empty string."""
    return (value or "").strip()


def _parse_ingredient(raw_name, raw_measure):
    """Return (name, quantity) for one slot, or None if the slot is unused.

    A note after the first comma ("egg, beaten") is moved into the quantity
    text ("1, beaten") so the name matches the pantry but nothing is lost.
    """
    name_part, _, note = _clean(raw_name).partition(",")
    name = normalize_ingredient(name_part)
    if not name:
        return None
    quantity_parts = [part for part in (_clean(raw_measure), note.strip()) if part]
    return name, ", ".join(quantity_parts)


def map_category(category):
    """Map a TheMealDB strCategory to a Freshup meal_type and diet_tags list."""
    key = _clean(category).lower()
    return {
        "meal_type": key if key in MEAL_TYPE_CATEGORIES else None,
        "diet_tags": [key] if key in DIET_TAG_CATEGORIES else [],
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
