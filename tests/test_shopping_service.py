import pytest

from app.extensions import db
from app.models import PantryItem, Recipe, RecipeIngredient, User
from app.shopping import service


@pytest.fixture
def recipe(app):
    with app.app_context():
        recipe = Recipe(title="Tomato Pasta", instructions="Boil, mix, serve.")
        for name, normalized, quantity in [
            ("Tomatoes", "tomato", "400"),
            ("Pasta", "pasta", "250"),
            ("Olive Oil", "olive oil", "2"),
            ("Garlic", "garlic", "3"),
        ]:
            recipe.ingredients.append(
                RecipeIngredient(
                    ingredient_name=name,
                    normalized_name=normalized,
                    quantity=quantity,
                    unit="g",
                )
            )
        db.session.add(recipe)
        db.session.commit()
        return recipe.id


@pytest.fixture
def user(app):
    with app.app_context():
        user = User(email="cook@example.com", password_hash="x")
        db.session.add(user)
        db.session.commit()
        return user.id


def stock_pantry(app, user_id, normalized_names):
    with app.app_context():
        for normalized in normalized_names:
            db.session.add(
                PantryItem(
                    user_id=user_id,
                    ingredient_name=normalized,
                    normalized_name=normalized,
                )
            )
        db.session.commit()


def names(items):
    return [item["ingredient_name"] for item in items]


def test_missing_excludes_what_the_user_already_has(app, recipe, user):
    stock_pantry(app, user, ["pasta", "garlic"])

    with app.app_context():
        missing = service.missing_ingredients(recipe, user)

    assert names(missing) == ["Tomatoes", "Olive Oil"]


def test_matching_uses_the_normalized_name(app, recipe, user):
    stock_pantry(app, user, ["tomato", "pasta", "olive oil", "garlic"])

    with app.app_context():
        assert service.missing_ingredients(recipe, user) == []


def test_a_guest_is_missing_every_ingredient(app, recipe):
    with app.app_context():
        missing = service.missing_ingredients(recipe, None)

    assert names(missing) == ["Tomatoes", "Pasta", "Olive Oil", "Garlic"]


def test_generated_list_carries_quantities(app, recipe, user):
    with app.app_context():
        result = service.generate_shopping_list(recipe, user)

    assert result["missing"][0]["quantity"] == "400"
    assert result["missing"][0]["unit"] == "g"


def test_list_is_complete_when_nothing_is_missing(app, recipe, user):
    stock_pantry(app, user, ["tomato", "pasta", "olive oil", "garlic"])

    with app.app_context():
        result = service.generate_shopping_list(recipe, user)

    assert result["complete"] is True
    assert result["missing"] == []


def test_unknown_recipe_raises(app, user):
    with app.app_context():
        with pytest.raises(service.RecipeNotFoundError):
            service.generate_shopping_list(99999, user)


def test_saving_persists_only_the_missing_items(app, recipe, user):
    stock_pantry(app, user, ["pasta", "garlic"])

    with app.app_context():
        saved = service.save_shopping_list(user, recipe)
        stored = service.saved_list(saved.id, user)

        assert [item.ingredient_name for item in stored.items] == [
            "Tomatoes",
            "Olive Oil",
        ]
        assert stored.recipe_title == "Tomato Pasta"


def test_a_user_cannot_read_another_users_list(app, recipe, user):
    with app.app_context():
        other = User(email="someone.else@example.com", password_hash="x")
        db.session.add(other)
        db.session.commit()

        saved = service.save_shopping_list(user, recipe)

        assert service.saved_list(saved.id, other.id) is None


def test_removing_an_item_persists(app, recipe, user):
    with app.app_context():
        saved = service.save_shopping_list(user, recipe)
        item_id = saved.items[0].id

        assert service.remove_item(saved.id, item_id, user) is True

        remaining = service.saved_list(saved.id, user)
        assert item_id not in [item.id for item in remaining.items]


def test_removing_an_item_from_another_users_list_fails(app, recipe, user):
    with app.app_context():
        other = User(email="intruder@example.com", password_hash="x")
        db.session.add(other)
        db.session.commit()

        saved = service.save_shopping_list(user, recipe)

        assert service.remove_item(saved.id, saved.items[0].id, other.id) is False


def test_checking_an_item_persists(app, recipe, user):
    with app.app_context():
        saved = service.save_shopping_list(user, recipe)
        item_id = saved.items[0].id

        assert service.set_item_checked(saved.id, item_id, user, True) is True

        stored = service.saved_list(saved.id, user)
        checked = next(item for item in stored.items if item.id == item_id)
        assert checked.is_checked is True
