# Recipe lookups shared by the details page, search and shopping lists
from dataclasses import dataclass, field


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


# Default way to compare names: ignore case and extra spaces
# Swap in normalize_ingredient() once Roberto's F6 is merged
def _simple_normalize(name):
    return " ".join(name.lower().split())


# Split a recipe's ingredients into the ones the user has and the ones
# they are missing (FR-4.3, FR-4.4)
def split_have_missing(recipe_ingredients, pantry_ingredients,
                       normalize=_simple_normalize):
    pantry = {normalize(name) for name in pantry_ingredients}
    have = []
    missing = []
    for name in recipe_ingredients:
        if normalize(name) in pantry:
            have.append(name)
        else:
            missing.append(name)
    return have, missing
