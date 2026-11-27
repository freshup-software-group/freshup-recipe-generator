from app.common.ingredients import normalize_ingredient
from app.shopping.repository import ShoppingListRepository


class RecipeNotFoundError(Exception):
    """Raised when a shopping list is requested for a recipe that does not exist."""


def _repo(repository):
    return repository or ShoppingListRepository()


def missing_ingredients(recipe_id, user_id=None, repository=None):
    """Return the recipe ingredients the user does not already have.

    Matching is done on the normalized name, so "Tomatoes" in a recipe and
    "tomato" in a pantry count as the same ingredient.
    """
    repository = _repo(repository)
    recipe = repository.get_recipe(recipe_id)
    if recipe is None:
        raise RecipeNotFoundError(recipe_id)

    owned = repository.pantry_normalized_names(user_id)

    missing = []
    seen = set()
    for ingredient in recipe.ingredients:
        key = ingredient.normalized_name or normalize_ingredient(
            ingredient.ingredient_name
        )
        if key in owned or key in seen:
            continue
        seen.add(key)
        missing.append(
            {
                "ingredient_name": ingredient.ingredient_name,
                "normalized_name": key,
                "quantity": ingredient.quantity,
                "unit": ingredient.unit,
            }
        )
    return missing


def generate_shopping_list(recipe_id, user_id=None, repository=None):
    repository = _repo(repository)
    recipe = repository.get_recipe(recipe_id)
    if recipe is None:
        raise RecipeNotFoundError(recipe_id)

    items = missing_ingredients(recipe_id, user_id, repository)
    return {
        "recipe_id": recipe.id,
        "recipe_title": recipe.title,
        "missing": items,
        "complete": len(items) == 0,
    }


def save_shopping_list(user_id, recipe_id, repository=None):
    repository = _repo(repository)
    recipe = repository.get_recipe(recipe_id)
    if recipe is None:
        raise RecipeNotFoundError(recipe_id)

    items = missing_ingredients(recipe_id, user_id, repository)
    return repository.create(user_id, recipe, items)


def saved_lists(user_id, repository=None):
    return _repo(repository).list_for_user(user_id)


def saved_list(list_id, user_id, repository=None):
    return _repo(repository).get_for_user(list_id, user_id)


def remove_item(list_id, item_id, user_id, repository=None):
    return _repo(repository).delete_item(list_id, item_id, user_id)


def set_item_checked(list_id, item_id, user_id, checked, repository=None):
    return _repo(repository).set_item_checked(list_id, item_id, user_id, checked)
