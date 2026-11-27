"""Recipe search by entered ingredients (UC-08). Pure functions, no database.

Limitation: matching compares normalized names exactly, so a recipe's
"chopped onion", "cherry tomato" or "garlic clove" does not match a pantry
"onion", "tomato" or "garlic". Last-word matching was evaluated and rejected:
it adds false positives ("coconut milk" for milk, "peanut butter" for butter)
and still misses names like "garlic clove" or "chicken breast".
See docs/known-limitations.md.
"""
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


# UC-07 outcomes of a pantry search; the route picks its message from these.
STATUS_OK = "ok"                      # at least one recipe matched
STATUS_EMPTY_PANTRY = "empty_pantry"  # the user has no pantry items yet
STATUS_NO_MATCHES = "no_matches"      # pantry has items, but no recipe uses them
PANTRY_STATUSES = (STATUS_OK, STATUS_EMPTY_PANTRY, STATUS_NO_MATCHES)


@dataclass(frozen=True)
class PantrySearchResult:
    """Outcome of a pantry search: a status plus the ranked SearchResults."""

    status: str
    results: tuple = ()  # SearchResults, best first; empty unless status is ok

    def __post_init__(self):
        if self.status not in PANTRY_STATUSES:
            raise ValueError(f"Unknown pantry search status: {self.status!r}")
        # Accept any iterable but store a tuple, so the result stays read-only.
        object.__setattr__(self, "results", tuple(self.results))


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
    A recipe ingredient listed twice counts once; a recipe with no ingredients
    scores 0.0. Zero-score results are returned; rank_recipes() filters them.
    """
    have = {normalize_ingredient(name) for name in user_ingredients}
    # Same de-duplication as parse_ingredient_input(): unique, first-seen order.
    needed = list(dict.fromkeys(normalize_ingredient(name) for name in recipe.ingredient_names))
    matched = tuple(name for name in needed if name in have)
    missing = tuple(name for name in needed if name not in have)
    return SearchResult(
        id=recipe.id,
        title=recipe.title,
        matched=matched,
        missing=missing,
        score=len(matched) / len(needed) if needed else 0.0,
    )


def rank_recipes(user_ingredients, recipes):
    """Return SearchResults for recipes sharing at least one ingredient, best first.

    Order: highest score, then most matched ingredients, then title A-Z
    (ignoring case). Recipes with no matched ingredient are left out.
    """
    results = [match_recipe(user_ingredients, recipe) for recipe in recipes]
    results = [result for result in results if result.matched]
    # Negating score and count sorts those descending while title stays ascending.
    return sorted(
        results,
        key=lambda result: (-result.score, -len(result.matched), result.title.casefold()),
    )
