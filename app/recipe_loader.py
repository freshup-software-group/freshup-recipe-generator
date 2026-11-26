"""Save TheMealDB meals into the Recipe and RecipeIngredient tables (F6, #14)."""
import click
from flask.cli import with_appcontext
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Recipe, RecipeIngredient
from app.themealdb import TheMealDBError, fetch_all_meals, map_category, parse_meal


def _skip_label(data):
    """How a skipped meal is reported: its idMeal, or its title if it has no id."""
    return data["external_id"] or f"(no id) {data['title'] or '(no title)'}"


def _apply_meal(recipe, data, category):
    """Copy parse_meal() data and the mapped category onto a Recipe."""
    tags = map_category(category)
    recipe.external_id = data["external_id"]
    recipe.title = data["title"]
    recipe.instructions = data["instructions"]
    recipe.meal_type = tags["meal_type"]
    recipe.diet_tags = ",".join(tags["diet_tags"])  # Text column: "vegan,vegetarian"
    recipe.cuisine = data["cuisine"]
    recipe.image_url = data["image_url"]
    recipe.source_url = data["source_url"]
    # Replacing the list deletes the old ingredient rows (delete-orphan cascade).
    # Nothing references them; the Recipe row itself and its id are kept.
    recipe.ingredients = [
        RecipeIngredient(
            ingredient_name=item.ingredient_name,
            normalized_name=item.normalized_name,
            quantity=item.quantity or None,
        )
        for item in data["ingredients"]
    ]


def save_meals(meals):
    """Insert or update the given raw API meals and return a summary dict.

    A meal whose idMeal is already stored updates that Recipe in place (same
    id, so saved shopping lists keep pointing at it); new meals are inserted.
    Recipes are never deleted. A meal is skipped (and reported) if it has no
    idMeal, title or instructions. Everything is committed in one transaction:
    on a database error nothing is saved and the error is raised.

    Returns {"created": int, "updated": int, "skipped": [labels]}.
    """
    summary = {"created": 0, "updated": 0, "skipped": []}
    try:
        # One query up front instead of one per meal.
        existing = {
            recipe.external_id: recipe
            for recipe in Recipe.query.filter(Recipe.external_id.isnot(None))
        }
        for meal in meals:
            data = parse_meal(meal)
            if not (data["external_id"] and data["title"] and data["instructions"]):
                summary["skipped"].append(_skip_label(data))
                continue
            recipe = existing.get(data["external_id"])
            if recipe is None:
                recipe = Recipe()
                db.session.add(recipe)
                # Remember it, so a repeated idMeal in the same batch updates it.
                existing[data["external_id"]] = recipe
                summary["created"] += 1
            else:
                summary["updated"] += 1
            _apply_meal(recipe, data, meal.get("strCategory"))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return summary


def format_summary(summary):
    """Return the lines the CLI prints after a load."""
    lines = [
        f"Created:   {summary['created']}",
        # "refreshed" = already stored and overwritten with the latest API data,
        # whether or not anything in it actually changed.
        f"Refreshed: {summary['updated']}",
        f"Skipped:   {len(summary['skipped'])}",
    ]
    if summary["skipped"]:
        lines.append("Skipped (missing id, title or instructions): "
                     + ", ".join(summary["skipped"]))
    return lines


@click.command("load-recipes")
@with_appcontext
def load_recipes_command():
    """Import recipes from TheMealDB (adds and refreshes, never deletes)."""
    click.echo("Fetching recipes from TheMealDB...")
    try:
        meals = fetch_all_meals()
    except TheMealDBError as error:
        # ClickException prints "Error: <message>" and exits with code 1.
        raise click.ClickException(f"{error}\nNo changes were made to the database.")
    click.echo(f"Fetched {len(meals)} meals. Saving...")
    try:
        summary = save_meals(meals)
    except SQLAlchemyError as error:
        raise click.ClickException(
            f"Database error: {error}\nNo changes were made to the database."
        )
    for line in format_summary(summary):
        click.echo(line)
