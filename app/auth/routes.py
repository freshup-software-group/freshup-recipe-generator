"""Auth routes: UC-01 Register, UC-02 Log in, UC-03 Log out."""
from urllib.parse import urlparse

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from app.auth import bp
from app.auth.services import AuthError, authenticate, register_user


def _safe_next(target):
    """Only allow relative redirects, so ?next= can't send users off-site."""
    if not target or "\\" in target or target.startswith("//"):
        return None
    parts = urlparse(target)
    if parts.scheme or parts.netloc or not target.startswith("/"):
        return None
    return target


def _home():
    return url_for("recipes.search")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(_home())
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "")
        try:
            user = register_user(
                email,
                request.form.get("password", ""),
                request.form.get("confirm", ""),
            )
        except AuthError as err:
            flash(str(err), "error")
            return render_template("auth/register.html", email=email), 400
        login_user(user)
        flash("Account created. Welcome to Freshup!", "success")
        return redirect(_home())
    return render_template("auth/register.html", email=email)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_home())
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "")
        try:
            user = authenticate(email, request.form.get("password", ""))
        except AuthError as err:
            flash(str(err), "error")
            return render_template("auth/login.html", email=email), 401
        next_url = _safe_next(request.args.get("next"))
        session.clear()  # fresh session on login (prevents session fixation)
        login_user(user, remember=bool(request.form.get("remember")))
        flash("Logged in.", "success")
        return redirect(next_url or _home())
    return render_template("auth/login.html", email=email)


# GET is allowed because the shared nav bar (base.html) links to logout.
@bp.route("/logout", methods=["GET", "POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
