"""Blueprint shell from the skeleton PR; the owner adds routes."""
from flask import Blueprint

bp = Blueprint("pantry", __name__)
from . import routes  # noqa: E402,F401
