"""Auth blueprint: UC-01 Register, UC-02 Log in, UC-03 Log out."""
from flask import Blueprint

bp = Blueprint("auth", __name__)

from app.auth import routes  # noqa: E402,F401
