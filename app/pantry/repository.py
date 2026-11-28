
from app.extensions import db
from app.models import PantryItem


class PantryRepository:
    """Handles database operations for pantry items."""

    def __init__(self, session=None):
        self._session = session

    @property
    def session(self):
        return self._session or db.session

    def get_by_normalized_name(self, user_id, normalized_name):
        return (
            self.session.query(PantryItem)
            .filter_by(
                user_id=user_id,
                normalized_name=normalized_name,
            )
            .one_or_none()
        )

    def add(self, user_id, ingredient_name, normalized_name):
        item = PantryItem(
            user_id=user_id,
            ingredient_name=ingredient_name,
            normalized_name=normalized_name,
        )
        self.session.add(item)
        self.session.commit()
        return item

    def list_for_user(self, user_id):
        return (
            self.session.query(PantryItem)
            .filter_by(user_id=user_id)
            .order_by(PantryItem.ingredient_name.asc())
            .all()
        )

    def delete(self, item_id, user_id):
        item = (
            self.session.query(PantryItem)
            .filter_by(id=item_id, user_id=user_id)
            .one_or_none()
        )
        if item is None:
            return False

        self.session.delete(item)
        self.session.commit()
        return True
