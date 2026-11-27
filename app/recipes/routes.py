"""Routes for recipe search (UC-08)."""
from flask import abort, flash, render_template, request

from app.recipes import bp
from app.recipes.service import get_recipe, search_recipes

# Ranking puts the best matches first; pagination is future work.
MAX_RESULTS = 20


@bp.route("/")
def search():
    """Show the search form; with ?ingredients=..., also the best matches."""
    text = request.args.get("ingredients")
    if text is None:  # first visit: no search submitted yet
        return render_template("recipes/search.html", query="", results=None, total=0)
    try:
        results = search_recipes(text)
    except ValueError as error:
        # UC-08 alternative flow: nothing usable entered. The message is
        # EMPTY_INPUT_MESSAGE, written to be shown to the user as-is.
        flash(str(error), "error")
        return render_template("recipes/search.html", query=text, results=None, total=0)
    return render_template(
        "recipes/search.html",
        query=text,
        results=results[:MAX_RESULTS],
        total=len(results),
    )


# Recipe details page (UC-09)
@bp.route("/<int:recipe_id>")
def detail(recipe_id):
    recipe = get_recipe(recipe_id)
    if recipe is None:
        abort(404)
    return render_template("recipes/detail.html", recipe=recipe)
