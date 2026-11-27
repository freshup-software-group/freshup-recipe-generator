"""Blueprint shell from the skeleton PR; the owner adds routes."""
from flask import Blueprint

bp = Blueprint("shopping", __name__)

from app.shopping import routes  # noqa: E402,F401
