"""Recipe search by entered ingredients (UC-08). Pure functions, no database."""
from app.common.ingredients import normalize_ingredient

# UC-08 alternative flow; the route can show this text to the user as-is.
EMPTY_INPUT_MESSAGE = "Enter at least one ingredient."


def parse_ingredient_input(text):
    """Turn the user's comma-separated input into a list of unique normalized names.

    "Tomatoes, , Garlic, tomato" -> ["tomato", "garlic"]

    Raises ValueError(EMPTY_INPUT_MESSAGE) if no ingredient is left, including
    for None (a missing form field), so the route never crashes on bad input.
    """
    names = (normalize_ingredient(part) for part in (text or "").split(","))
    # dict.fromkeys() drops repeats but keeps first-seen order (dicts are ordered).
    unique_names = list(dict.fromkeys(name for name in names if name))
    if not unique_names:
        raise ValueError(EMPTY_INPUT_MESSAGE)
    return unique_names
