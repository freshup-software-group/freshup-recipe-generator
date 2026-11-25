"""Recipe search by entered ingredients (UC-08). Pure functions, no database."""
from app.common.ingredients import normalize_ingredient


def parse_ingredient_input(text):
    """Turn the user's comma-separated input into a list of normalized names.

    "Tomatoes, , Garlic " -> ["tomato", "garlic"]
    """
    names = (normalize_ingredient(part) for part in text.split(","))
    return [name for name in names if name]
