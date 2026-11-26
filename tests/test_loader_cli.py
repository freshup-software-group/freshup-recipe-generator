"""CLI tests for load-recipes. fetch_all_meals is mocked, so no network is used."""
import json
from pathlib import Path
from unittest import mock

import pytest
from sqlalchemy.exc import OperationalError

from app import create_app
from app.extensions import db
from app.models import Recipe
from app.recipe_loader import load_recipes_command
from app.themealdb import TheMealDBError

SAMPLE_PATH = Path(__file__).parent / "data" / "themealdb_sample.json"


@pytest.fixture
def app():
    """A fresh app with an empty in-memory database for each test."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_meals():
    with SAMPLE_PATH.open(encoding="utf-8") as f:
        return json.load(f)["meals"]


def run_load(app, fetch):
    """Run the command with fetch_all_meals replaced by the given mock settings."""
    with mock.patch("app.recipe_loader.fetch_all_meals", **fetch):
        return app.test_cli_runner().invoke(load_recipes_command)


def test_load_prints_summary_and_saves_recipes(app, sample_meals):
    result = run_load(app, {"return_value": sample_meals})
    assert result.exit_code == 0, result.output
    assert "Fetched 3 meals" in result.output
    assert "Created:   2" in result.output
    assert "Refreshed: 0" in result.output
    assert "Skipped:   1" in result.output
    assert "Skipped (missing id, title or instructions): 99990001" in result.output
    assert Recipe.query.count() == 2


def test_second_load_reports_refreshed(app, sample_meals):
    run_load(app, {"return_value": sample_meals})
    result = run_load(app, {"return_value": sample_meals})
    assert "Created:   0" in result.output
    assert "Refreshed: 2" in result.output
    assert Recipe.query.count() == 2


def test_no_skipped_line_when_nothing_skipped(app, sample_meals):
    result = run_load(app, {"return_value": sample_meals[:2]})
    assert "Skipped:   0" in result.output
    assert "missing id" not in result.output


def test_unreachable_api_gives_clear_error_and_changes_nothing(app, sample_meals):
    run_load(app, {"return_value": sample_meals[:1]})  # one recipe already stored
    error = TheMealDBError("Could not reach TheMealDB (https://...f=a): timed out")

    result = run_load(app, {"side_effect": error})

    assert result.exit_code == 1
    assert "Error: Could not reach TheMealDB" in result.output
    assert "No changes were made to the database." in result.output
    assert [r.external_id for r in Recipe.query.all()] == ["52767"]


def test_database_error_gives_clear_error_and_changes_nothing(app, sample_meals):
    error = OperationalError("COMMIT", {}, Exception("disk full"))
    with mock.patch.object(db.session, "commit", side_effect=error):
        result = run_load(app, {"return_value": sample_meals})
    assert result.exit_code == 1
    assert "Error: Database error" in result.output
    assert "No changes were made to the database." in result.output
    assert Recipe.query.count() == 0
