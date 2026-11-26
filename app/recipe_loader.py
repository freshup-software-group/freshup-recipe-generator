"""Save TheMealDB meals into the Recipe and RecipeIngredient tables (F6, #14)."""
from app.extensions import db
from app.models import Recipe, RecipeIngredient
from app.themealdb import map_category, parse_meal


def _skip_label(data):
    """How a skipped meal is reported: its idMeal, or its title if it has no id."""
    return data["external_id"] or f"(no id) {data['title'] or '(no title)'}"


def _build_recipe(data, category):
    """Create an unsaved Recipe (with its ingredients) from parse_meal() data."""
    tags = map_category(category)
    return Recipe(
        external_id=data["external_id"],
        title=data["title"],
        instructions=data["instructions"],
        meal_type=tags["meal_type"],
        diet_tags=",".join(tags["diet_tags"]),  # Text column: "vegan,vegetarian"
        cuisine=data["cuisine"],
        image_url=data["image_url"],
        source_url=data["source_url"],
        ingredients=[
            RecipeIngredient(
                ingredient_name=item.ingredient_name,
                normalized_name=item.normalized_name,
                quantity=item.quantity or None,
            )
            for item in data["ingredients"]
        ],
    )


def save_meals(meals):
    """Insert the given raw API meals and return a summary dict.

    A meal is skipped (and reported) if it has no idMeal, title or instructions.
    Everything is committed in one transaction: on a database error nothing is
    saved and the error is raised.

    Returns {"created": int, "updated": int, "skipped": [labels]}.
    """
    summary = {"created": 0, "updated": 0, "skipped": []}
    try:
        for meal in meals:
            data = parse_meal(meal)
            if not (data["external_id"] and data["title"] and data["instructions"]):
                summary["skipped"].append(_skip_label(data))
                continue
            db.session.add(_build_recipe(data, meal.get("strCategory")))
            summary["created"] += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return summary
