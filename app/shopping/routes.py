from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.shopping import bp
from app.shopping.service import (
    RecipeNotFoundError,
    generate_shopping_list,
    remove_item,
    save_shopping_list,
    saved_list,
    saved_lists,
    set_item_checked,
)


def _current_user_id():
    return current_user.id if current_user.is_authenticated else None


@bp.route("/generate/<int:recipe_id>")
def generate(recipe_id):
    try:
        result = generate_shopping_list(recipe_id, _current_user_id())
    except RecipeNotFoundError:
        abort(404)
    return render_template("shopping/generated.html", result=result)


@bp.route("/save/<int:recipe_id>", methods=["POST"])
@login_required
def save(recipe_id):
    try:
        shopping_list = save_shopping_list(current_user.id, recipe_id)
    except RecipeNotFoundError:
        abort(404)
    flash("Shopping list saved.", "success")
    return redirect(url_for("shopping.detail", list_id=shopping_list.id))


@bp.route("/lists")
@login_required
def index():
    return render_template(
        "shopping/index.html", lists=saved_lists(current_user.id)
    )


@bp.route("/lists/<int:list_id>")
@login_required
def detail(list_id):
    shopping_list = saved_list(list_id, current_user.id)
    if shopping_list is None:
        abort(404)
    return render_template("shopping/detail.html", shopping_list=shopping_list)


@bp.route("/lists/<int:list_id>/items/<int:item_id>/remove", methods=["POST"])
@login_required
def delete_item(list_id, item_id):
    if not remove_item(list_id, item_id, current_user.id):
        abort(404)
    flash("Item removed.", "success")
    return redirect(url_for("shopping.detail", list_id=list_id))


@bp.route("/lists/<int:list_id>/items/<int:item_id>/check", methods=["POST"])
@login_required
def check_item(list_id, item_id):
    if not set_item_checked(list_id, item_id, current_user.id, True):
        abort(404)
    return redirect(url_for("shopping.detail", list_id=list_id))
