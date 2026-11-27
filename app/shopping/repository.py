from app.extensions import db
from app.models import PantryItem, Recipe, ShoppingList, ShoppingListItem


class ShoppingListRepository:
    """Isolates every database call the shopping module makes."""

    def __init__(self, session=None):
        self._session = session

    @property
    def session(self):
        return self._session or db.session

    def get_recipe(self, recipe_id):
        return self.session.get(Recipe, recipe_id)

    def pantry_normalized_names(self, user_id):
        if user_id is None:
            return set()
        rows = (
            self.session.query(PantryItem.normalized_name)
            .filter(PantryItem.user_id == user_id)
            .all()
        )
        return {row[0] for row in rows}

    def create(self, user_id, recipe, items):
        shopping_list = ShoppingList(
            user_id=user_id,
            recipe_id=recipe.id,
            recipe_title=recipe.title,
            name=f"Shopping list for {recipe.title}",
        )
        for item in items:
            shopping_list.items.append(
                ShoppingListItem(
                    ingredient_name=item["ingredient_name"],
                    quantity=item.get("quantity"),
                    unit=item.get("unit"),
                )
            )
        self.session.add(shopping_list)
        self.session.commit()
        return shopping_list

    def list_for_user(self, user_id):
        return (
            self.session.query(ShoppingList)
            .filter_by(user_id=user_id)
            .order_by(ShoppingList.created_at.desc())
            .all()
        )

    def get_for_user(self, list_id, user_id):
        return (
            self.session.query(ShoppingList)
            .filter_by(id=list_id, user_id=user_id)
            .one_or_none()
        )

    def delete_item(self, list_id, item_id, user_id):
        shopping_list = self.get_for_user(list_id, user_id)
        if shopping_list is None:
            return False
        item = next((i for i in shopping_list.items if i.id == item_id), None)
        if item is None:
            return False
        self.session.delete(item)
        self.session.commit()
        return True

    def set_item_checked(self, list_id, item_id, user_id, checked):
        shopping_list = self.get_for_user(list_id, user_id)
        if shopping_list is None:
            return False
        item = next((i for i in shopping_list.items if i.id == item_id), None)
        if item is None:
            return False
        item.is_checked = checked
        self.session.commit()
        return True
