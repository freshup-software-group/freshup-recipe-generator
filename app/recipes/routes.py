"""Routes for recipe search (UC-08)."""
from flask import render_template, request

from app.recipes import bp
from app.recipes.service import search_recipes

# Ranking puts the best matches first; pagination is future work.
MAX_RESULTS = 20


@bp.route("/")
def search():
    """Show the search form; with ?ingredients=..., also the best matches."""
    text = request.args.get("ingredients")
    if text is None:  # first visit: no search submitted yet
        return render_template("recipes/search.html", query="", results=None, total=0)
    results = search_recipes(text)
    return render_template(
        "recipes/search.html",
        query=text,
        results=results[:MAX_RESULTS],
        total=len(results),
    )
