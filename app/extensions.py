"""Extension objects, created here and bound to the app in create_app()."""
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access that page."
login_manager.login_message_category = "warning"
login_manager.session_protection = "strong"


@login_manager.user_loader
def load_user(user_id):
    """Return the logged-in User for current_user (model from F5, #20)."""
    from .models import User

    return db.session.get(User, int(user_id))
