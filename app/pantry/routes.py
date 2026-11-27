
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.pantry import bp
from app.pantry.service import (
    DuplicateIngredientError,
    InvalidIngredientError,
    add_ingredient,
    get_pantry_items,
)


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Display the user's pantry and handle adding ingredients."""
    if request.method == "POST":
        ingredient_name = request.form.get("ingredient_name", "")

        try:
            add_ingredient(current_user.id, ingredient_name)
            flash("Ingredient added to your pantry.", "success")
        except (DuplicateIngredientError, InvalidIngredientError) as error:
            flash(str(error), "error")

        return redirect(url_for("pantry.index"))

    items = get_pantry_items(current_user.id)
    return render_template("pantry/add.html", items=items)
