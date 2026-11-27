"""Tests for the pure pantry search logic (UC-07, #2)."""
import pytest

from app.recipes.search import (
    PANTRY_STATUSES,
    STATUS_EMPTY_PANTRY,
    STATUS_NO_MATCHES,
    STATUS_OK,
    PantrySearchResult,
    SearchResult,
)

OMELETTE = SearchResult(id=1, title="Omelette", matched=("egg",), missing=("milk",), score=0.5)


def test_status_values_are_distinct_strings():
    assert (STATUS_OK, STATUS_EMPTY_PANTRY, STATUS_NO_MATCHES) == (
        "ok", "empty_pantry", "no_matches",
    )
    assert set(PANTRY_STATUSES) == {STATUS_OK, STATUS_EMPTY_PANTRY, STATUS_NO_MATCHES}


def test_holds_status_and_results():
    result = PantrySearchResult(STATUS_OK, (OMELETTE,))
    assert result.status == STATUS_OK
    assert result.results == (OMELETTE,)


def test_results_default_to_empty_tuple():
    assert PantrySearchResult(STATUS_EMPTY_PANTRY).results == ()


def test_list_of_results_is_stored_as_tuple():
    result = PantrySearchResult(STATUS_OK, [OMELETTE])
    assert result.results == (OMELETTE,)
    assert isinstance(result.results, tuple)


def test_is_read_only():
    result = PantrySearchResult(STATUS_NO_MATCHES)
    with pytest.raises(AttributeError):
        result.status = STATUS_OK


def test_equal_when_status_and_results_match():
    assert PantrySearchResult(STATUS_OK, [OMELETTE]) == PantrySearchResult(STATUS_OK, (OMELETTE,))


@pytest.mark.parametrize("status", ["", "OK", "error", None])
def test_unknown_status_is_rejected(status):
    with pytest.raises(ValueError, match="Unknown pantry search status"):
        PantrySearchResult(status)
