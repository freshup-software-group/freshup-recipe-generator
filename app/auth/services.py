"""Auth service layer (UC-01 to UC-03). Routes call these; tests call them too."""
import re
import time

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(Exception):
    """Raised with a message that is safe to show the user."""


def normalize_email(email):
    return (email or "").strip().lower()


def validate_password(password):
    """Return a list of problems with the password (empty list = OK).

    Stretch item: at least PASSWORD_MIN_LENGTH characters, with at least
    one letter and one number.
    """
    password = password or ""
    min_len = current_app.config.get("PASSWORD_MIN_LENGTH", 8)
    problems = []
    if len(password) < min_len:
        problems.append(f"Password must be at least {min_len} characters.")
    if not re.search(r"[A-Za-z]", password):
        problems.append("Password must contain at least one letter.")
    if not re.search(r"\d", password):
        problems.append("Password must contain at least one number.")
    return problems


def register_user(email, password, confirm):
    """UC-01: create a user, or raise AuthError explaining why not."""
    email = normalize_email(email)
    if not EMAIL_RE.match(email):
        raise AuthError("Enter a valid email address.")
    if password != confirm:
        raise AuthError("Passwords do not match.")
    problems = validate_password(password)
    if problems:
        raise AuthError(" ".join(problems))
    if User.query.filter_by(email=email).first():
        raise AuthError("An account with that email already exists.")

    method = current_app.config.get("PASSWORD_HASH_METHOD", "scrypt")
    user = User(
        email=email,
        password_hash=generate_password_hash(password, method=method),
    )
    db.session.add(user)
    db.session.commit()
    return user


# --- Login attempt limit (stretch item) ---------------------------------
# Failed attempts per email, kept in memory: {email: [timestamps]}.
# Resets on restart and is per-process (see Limitations in the report).
_failed_attempts = {}


def _recent_failures(email, now):
    window = current_app.config.get("LOGIN_LOCKOUT_SECONDS", 900)
    stamps = [t for t in _failed_attempts.get(email, []) if now - t < window]
    _failed_attempts[email] = stamps
    return stamps


def is_locked_out(email, now=None):
    now = time.time() if now is None else now
    limit = current_app.config.get("LOGIN_MAX_ATTEMPTS", 5)
    return len(_recent_failures(normalize_email(email), now)) >= limit


def record_failure(email, now=None):
    now = time.time() if now is None else now
    _failed_attempts.setdefault(normalize_email(email), []).append(now)


def clear_failures(email):
    _failed_attempts.pop(normalize_email(email), None)


def reset_all_failures():
    """Used by tests so one test's failed logins don't leak into the next."""
    _failed_attempts.clear()


def authenticate(email, password, now=None):
    """UC-02: return the User if the credentials are valid, else AuthError.

    Unknown email and wrong password give the same message, so the form
    does not reveal which accounts exist.
    """
    email = normalize_email(email)
    if is_locked_out(email, now):
        raise AuthError(
            "Too many failed login attempts. Try again in a few minutes."
        )
    user = User.query.filter_by(email=email).first()
    if user is None or not check_password_hash(user.password_hash, password or ""):
        record_failure(email, now)
        raise AuthError("Invalid email or password.")
    clear_failures(email)
    return user
