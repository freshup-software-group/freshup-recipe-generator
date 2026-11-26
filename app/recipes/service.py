"""Database side of recipe search (UC-08): load recipes, then rank them."""
from sqlalchemy.orm import selectinload

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
