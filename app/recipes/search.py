"""Recipe search by entered ingredients (UC-08). Pure functions, no database."""
from dataclasses import dataclass

from app.common.ingredients import normalize_ingredient

# UC-08 alternative flow; the route can show this text to the user as-is.
EMPTY_INPUT_MESSAGE = "Enter at least one ingredient."


@dataclass(frozen=True)
class RecipeData:
    """Plain-data recipe with the attributes search needs.

    Any object with .id, .title and .ingredient_names works (for example the
    team's get_recipe() result); this class is a stand-in for tests and tools.
    """

    id: int
    title: str
    ingredient_names: tuple


@dataclass(frozen=True)
class SearchResult:
    """How well one recipe matches the user's ingredients."""

    id: int
    title: str
    matched: tuple  # recipe ingredients the user has, in recipe order
    missing: tuple  # recipe ingredients the user lacks, in recipe order
    score: float    # len(matched) / number of recipe ingredients, 0.0 to 1.0


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


def match_recipe(user_ingredients, recipe):
    """Compare the user's ingredients with one recipe's ingredients.

    Both sides are normalized, so "Tomatoes" matches a recipe's "tomato".
    """
    have = {normalize_ingredient(name) for name in user_ingredients}
    needed = [normalize_ingredient(name) for name in recipe.ingredient_names]
    matched = tuple(name for name in needed if name in have)
    missing = tuple(name for name in needed if name not in have)
    return SearchResult(
        id=recipe.id,
        title=recipe.title,
        matched=matched,
        missing=missing,
        score=len(matched) / len(needed),
    )
