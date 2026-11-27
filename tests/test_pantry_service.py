import pytest

from app.extensions import db
from app.models import PantryItem, User
from app.pantry import service


@pytest.fixture
def user(app):
    with app.app_context():
        user = User(email="pantry@example.com", password_hash="x")
        db.session.add(user)
        db.session.commit()
        return user.id


def test_add_ingredient_saves_to_pantry(app, user):
    with app.app_context():
        item = service.add_ingredient(user, "Tomatoes")

        assert item.ingredient_name == "Tomatoes"
        assert item.normalized_name == "tomato"

        stored = PantryItem.query.filter_by(user_id=user).one()
        assert stored.normalized_name == "tomato"


def test_add_ingredient_normalizes_name(app, user):
    with app.app_context():
        item = service.add_ingredient(user, "  Cherry   Tomatoes  ")

        assert item.normalized_name == "cherry tomato"


def test_duplicate_ingredient_is_rejected_after_normalization(app, user):
    with app.app_context():
        service.add_ingredient(user, "Tomatoes")

        with pytest.raises(service.DuplicateIngredientError):
            service.add_ingredient(user, "Tomato")


def test_empty_ingredient_is_rejected(app, user):
    with app.app_context():
        with pytest.raises(service.InvalidIngredientError):
            service.add_ingredient(user, "   ")


def test_get_pantry_ingredients_returns_names(app, user):
    with app.app_context():
        service.add_ingredient(user, "Tomatoes")
        service.add_ingredient(user, "Pasta")

        ingredients = service.get_pantry_ingredients(user)

        assert ingredients == ["Pasta", "Tomatoes"]


def test_get_pantry_items_returns_user_items_only(app, user):
    with app.app_context():
        other = User(email="other@example.com", password_hash="x")
        db.session.add(other)
        db.session.commit()

        service.add_ingredient(user, "Tomatoes")
        service.add_ingredient(other.id, "Pasta")

        items = service.get_pantry_items(user)

        assert [item.ingredient_name for item in items] == ["Tomatoes"]