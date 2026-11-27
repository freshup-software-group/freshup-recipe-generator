"""Tests for UC-01 Register, UC-02 Log in, UC-03 Log out (#6, #7, #8).

Test names follow the acceptance criteria (main + alternative flows).
Fixtures app, client and logged_in_client come from tests/conftest.py.
"""
import pytest

from app.auth import services
from app.models import User

EMAIL = "percy@example.com"
PASSWORD = "Pantry2026"
PROTECTED = "/shopping/lists"


@pytest.fixture(autouse=True)
def reset_login_attempts():
    """Failed-login counts live in memory; start every test clean."""
    services.reset_all_failures()
    yield
    services.reset_all_failures()


def register(client, email=EMAIL, password=PASSWORD, confirm=None):
    return client.post(
        "/auth/register",
        data={
            "email": email,
            "password": password,
            "confirm": password if confirm is None else confirm,
        },
    )


def login(client, email=EMAIL, password=PASSWORD, next_url=None):
    url = "/auth/login" + (f"?next={next_url}" if next_url else "")
    return client.post(url, data={"email": email, "password": password})


def logout(client):
    return client.get("/auth/logout")


# --- UC-01 Register ------------------------------------------------------

def test_uc01_register_page_loads(client):
    response = client.get("/auth/register")
    assert response.status_code == 200
    assert b"Create an account" in response.data


def test_uc01_register_creates_account_and_logs_in(client):
    response = register(client)
    assert response.status_code == 302
    assert User.query.filter_by(email=EMAIL).count() == 1
    assert client.get(PROTECTED).status_code == 200


def test_uc01_email_is_normalized(client):
    register(client, email="  Percy@Example.COM ")
    assert User.query.filter_by(email=EMAIL).count() == 1


def test_uc01_duplicate_email_rejected(client):
    register(client)
    logout(client)
    response = register(client, email="PERCY@example.com")
    assert response.status_code == 400
    assert b"already exists" in response.data
    assert User.query.count() == 1


def test_uc01_password_stored_hashed(client):
    register(client)
    user = User.query.filter_by(email=EMAIL).one()
    assert user.password_hash != PASSWORD
    assert PASSWORD not in user.password_hash
    assert user.password_hash.startswith(("pbkdf2:", "scrypt:"))


def test_uc01_invalid_email_rejected(client):
    response = register(client, email="not-an-email")
    assert response.status_code == 400
    assert User.query.count() == 0


def test_uc01_password_mismatch_rejected(client):
    response = register(client, confirm="Different123")
    assert response.status_code == 400
    assert b"do not match" in response.data
    assert User.query.count() == 0


@pytest.mark.parametrize(
    "weak, message",
    [
        ("Ab1", b"at least 8 characters"),
        ("abcdefgh", b"at least one number"),
        ("12345678", b"at least one letter"),
    ],
)
def test_uc01_weak_password_rejected(client, weak, message):
    response = register(client, password=weak)
    assert response.status_code == 400
    assert message in response.data
    assert User.query.count() == 0


def test_uc01_validate_password_accepts_strong(app):
    assert services.validate_password(PASSWORD) == []


# --- UC-02 Log in --------------------------------------------------------

def test_uc02_login_page_loads(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Log in" in response.data


def test_uc02_login_with_valid_credentials(client):
    register(client)
    logout(client)
    response = login(client)
    assert response.status_code == 302
    assert client.get(PROTECTED).status_code == 200


def test_uc02_wrong_password_rejected(client):
    register(client)
    logout(client)
    response = login(client, password="WrongPass99")
    assert response.status_code == 401
    assert b"Invalid email or password" in response.data


def test_uc02_unknown_email_gives_same_error(client):
    response = login(client, email="nobody@example.com")
    assert response.status_code == 401
    assert b"Invalid email or password" in response.data


def test_uc02_protected_route_redirects_to_login(client):
    response = client.get(PROTECTED)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_uc02_login_returns_to_next_page(client):
    register(client)
    logout(client)
    response = login(client, next_url=PROTECTED)
    assert response.headers["Location"].endswith(PROTECTED)


def test_uc02_login_ignores_offsite_next(client):
    register(client)
    logout(client)
    response = login(client, next_url="https://evil.example.com/")
    assert "evil.example.com" not in response.headers["Location"]


def test_uc02_guest_can_still_search_recipes(client):
    assert client.get("/recipes/").status_code == 200


# --- Login attempt limit (stretch) ---------------------------------------

def test_uc02_lockout_after_max_failed_attempts(app, client):
    register(client)
    logout(client)
    for _ in range(app.config["LOGIN_MAX_ATTEMPTS"]):
        login(client, password="WrongPass99")
    response = login(client)  # right password, but locked out
    assert response.status_code == 401
    assert b"Too many failed login attempts" in response.data


def test_uc02_lockout_expires_after_window(app):
    window = app.config["LOGIN_LOCKOUT_SECONDS"]
    for _ in range(app.config["LOGIN_MAX_ATTEMPTS"]):
        services.record_failure(EMAIL, now=1000.0)
    assert services.is_locked_out(EMAIL, now=1000.0)
    assert not services.is_locked_out(EMAIL, now=1000.0 + window + 1)


def test_uc02_successful_login_resets_failures(app, client):
    register(client)
    logout(client)
    for _ in range(app.config["LOGIN_MAX_ATTEMPTS"] - 1):
        login(client, password="WrongPass99")
    login(client)
    logout(client)
    login(client, password="WrongPass99")
    assert not services.is_locked_out(EMAIL)


# --- UC-03 Log out -------------------------------------------------------

def test_uc03_logout_ends_session(logged_in_client):
    assert logged_in_client.get(PROTECTED).status_code == 200
    response = logout(logged_in_client)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
    assert logged_in_client.get(PROTECTED).status_code == 302
    with logged_in_client.session_transaction() as session:
        assert "_user_id" not in session


def test_uc03_logout_by_post_also_works(logged_in_client):
    response = logged_in_client.post("/auth/logout")
    assert response.status_code == 302
    assert logged_in_client.get(PROTECTED).status_code == 302


def test_uc03_logout_when_logged_out_redirects_to_login(client):
    response = logout(client)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
