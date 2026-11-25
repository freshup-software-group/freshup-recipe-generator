"""Recipe search by entered ingredients (UC-08). Pure functions, no database."""
from app.common.ingredients import normalize_ingredient


def parse_ingredient_input(text):
    """Turn the user's comma-separated input into a list of unique normalized names.

    "Tomatoes, , Garlic, tomato" -> ["tomato", "garlic"]
    """
    names = (normalize_ingredient(part) for part in text.split(","))
    # dict.fromkeys() drops repeats but keeps first-seen order (dicts are ordered).
    return list(dict.fromkeys(name for name in names if name))
