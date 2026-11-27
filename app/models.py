
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

from .extensions import db


class User(UserMixin, db.Model):
    """Application user account."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pantry_items = db.relationship(
        "PantryItem",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    shopping_lists = db.relationship(
        "ShoppingList",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User {self.email}>"


class PantryItem(db.Model):
    """An ingredient belonging to a user's pantry."""

    __tablename__ = "pantry_items"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "normalized_name",
            name="uq_pantry_user_ingredient",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingredient_name = db.Column(db.String(150), nullable=False)
    normalized_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.String(50), nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="pantry_items")

    def __repr__(self):
        return f"<PantryItem {self.ingredient_name}>"


class Recipe(db.Model):
    """A recipe available in the application."""

    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(
        db.String(50),
        unique=True,
        nullable=True,
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    prep_time_minutes = db.Column(db.Integer, nullable=True)
    cook_time_minutes = db.Column(db.Integer, nullable=True)
    servings = db.Column(db.Integer, nullable=True)
    meal_type = db.Column(db.String(100), nullable=True)
    diet_tags = db.Column(db.Text, nullable=False, default="")
    cuisine = db.Column(db.String(100), nullable=True)
    source_url = db.Column(db.String(500), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)

    ingredients = db.relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

    shopping_lists = db.relationship(
        "ShoppingList",
        back_populates="recipe",
    )

    @property
    def ingredient_names(self):
        """Return normalized ingredient names for recipe search."""
        return [item.normalized_name for item in self.ingredients]

    def __repr__(self):
        return f"<Recipe {self.title}>"


class RecipeIngredient(db.Model):
    """An ingredient associated with a recipe."""

    __tablename__ = "recipe_ingredients"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingredient_name = db.Column(db.String(150), nullable=False)
    normalized_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.String(255), nullable=True)
    unit = db.Column(db.String(50), nullable=True)

    recipe = db.relationship("Recipe", back_populates="ingredients")

    def __repr__(self):
        return f"<RecipeIngredient {self.ingredient_name}>"


class ShoppingList(db.Model):
    """A shopping list belonging to a user."""

    __tablename__ = "shopping_lists"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipes.id", ondelete="SET NULL"),
        nullable=True,
    )
    recipe_title = db.Column(db.String(255), nullable=True)
    name = db.Column(
        db.String(150),
        nullable=False,
        default="My Shopping List",
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = db.relationship("User", back_populates="shopping_lists")

    recipe = db.relationship(
        "Recipe",
        back_populates="shopping_lists",
    )

    items = db.relationship(
        "ShoppingListItem",
        back_populates="shopping_list",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ShoppingList {self.name}>"


class ShoppingListItem(db.Model):
    """An ingredient inside a shopping list."""

    __tablename__ = "shopping_list_items"

    id = db.Column(db.Integer, primary_key=True)
    shopping_list_id = db.Column(
        db.Integer,
        db.ForeignKey("shopping_lists.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingredient_name = db.Column(db.String(150), nullable=False)
    # Matches RecipeIngredient.quantity; TheMealDB quantities exceed 50 chars.
    quantity = db.Column(db.String(255), nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    is_checked = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    shopping_list = db.relationship(
        "ShoppingList",
        back_populates="items",
    )

    def __repr__(self):
        return f"<ShoppingListItem {self.ingredient_name}>"
