"""Recipe services: search (UC-08) and lookups for details, search and shopping lists."""
from dataclasses import dataclass, field

from sqlalchemy.orm import selectinload

from app.common.ingredients import normalize_ingredient
from app.models import Recipe
from app.recipes.search import parse_ingredient_input, rank_recipes


def search_recipes(text):
    """Return every recipe sharing an ingredient with text, best match first.

    Raises ValueError(EMPTY_INPUT_MESSAGE) for empty input, before touching
    the database. The caller decides how many results to show.
    """
    user_ingredients = parse_ingredient_input(text)
    # selectinload fetches all ingredients in one extra query, instead of one
    # query per recipe when rank_recipes() reads recipe.ingredient_names (N+1).
    recipes = Recipe.query.options(selectinload(Recipe.ingredients)).all()
    return rank_recipes(user_ingredients, recipes)


# A recipe as the rest of the app sees it
@dataclass
class RecipeDetails:
    id: int
    title: str
    ingredient_names: list = field(default_factory=list)
    instructions: str = ""
    meal_type: str = ""
    diet_tags: list = field(default_factory=list)
    cuisine: str = ""
    image_url: str = ""


# diet_tags may be stored as "vegan,vegetarian" or as a list
# Always return a clean list like ["vegan", "vegetarian"]
def _split_tags(tags):
    if not tags:
        return []
    if isinstance(tags, str):
        tags = tags.split(",")
    return [tag.strip() for tag in tags if tag.strip()]


# Turn a Recipe database row into a RecipeDetails object
# Missing optional fields become empty strings
def to_details(recipe):
    return RecipeDetails(
        id=recipe.id,
        title=recipe.title,
        ingredient_names=[item.ingredient_name for item in recipe.ingredients],
        instructions=recipe.instructions or "",
        meal_type=recipe.meal_type or "",
        diet_tags=_split_tags(recipe.diet_tags),
        cuisine=recipe.cuisine or "",
        image_url=recipe.image_url or "",
    )


# Return the recipe with this id, or None if it does not exist
# Imports are inside the function so this file works before the
# models (F5) are merged
def get_recipe(recipe_id):
    from app.extensions import db
    from app.models import Recipe

    recipe = db.session.get(Recipe, recipe_id)
    if recipe is None:
        return None
    return to_details(recipe)


# Split a recipe's ingredients into the ones the user has and the ones
# they are missing (FR-4.3, FR-4.4)
# Names are compared with the shared normalize_ingredient() (FR-3.4)
def split_have_missing(recipe_ingredients, pantry_ingredients,
                       normalize=normalize_ingredient):
    pantry = {normalize(name) for name in pantry_ingredients}
    have = []
    missing = []
    for name in recipe_ingredients:
        if normalize(name) in pantry:
            have.append(name)
        else:
            missing.append(name)
    return have, missing
