
from sqlalchemy.exc import IntegrityError

from app.common.ingredients import normalize_ingredient
from app.pantry.repository import PantryRepository


class DuplicateIngredientError(Exception):
    """Raised when an ingredient already exists in the user's pantry."""


class InvalidIngredientError(Exception):
    """Raised when an ingredient name is empty or invalid."""


def _repo(repository):
    return repository or PantryRepository()


def add_ingredient(user_id, ingredient_name, repository=None):
    """Add an ingredient to a user's pantry."""
    repository = _repo(repository)

    if not isinstance(ingredient_name, str) or not ingredient_name.strip():
        raise InvalidIngredientError("Please enter an ingredient name.")

    ingredient_name = " ".join(ingredient_name.split())
    normalized_name = normalize_ingredient(ingredient_name)

    if not normalized_name:
        raise InvalidIngredientError("Please enter an ingredient name.")

    existing = repository.get_by_normalized_name(
        user_id,
        normalized_name,
    )

    if existing is not None:
        raise DuplicateIngredientError(
            f"{ingredient_name} is already in your pantry."
        )

    try:
        return repository.add(
            user_id,
            ingredient_name,
            normalized_name,
        )
    except IntegrityError:
        repository.session.rollback()
        raise DuplicateIngredientError(
            f"{ingredient_name} is already in your pantry."
        )


def get_pantry_ingredients(user_id, repository=None):
    """Return a list of ingredient names in the user's pantry."""
    if user_id is None:
        return []

    items = _repo(repository).list_for_user(user_id)
    return [item.ingredient_name for item in items]


def get_pantry_items(user_id, repository=None):
    """Return the user's pantry item records."""
    return _repo(repository).list_for_user(user_id)
