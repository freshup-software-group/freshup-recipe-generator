"""Tests for the pure pantry search logic (UC-07, #2)."""
import pytest

from app.recipes.search import (
    PANTRY_STATUSES,
    STATUS_EMPTY_PANTRY,
    STATUS_NO_MATCHES,
    STATUS_OK,
    PantrySearchResult,
    RecipeData,
    SearchResult,
    rank_recipes,
    search_with_pantry,
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


# ---------- search_with_pantry ----------

def recipe(recipe_id, title, *names):
    return RecipeData(id=recipe_id, title=title, ingredient_names=names)


RECIPES = [
    recipe(1, "Omelette", "egg", "milk", "butter"),
    recipe(2, "Boiled egg", "egg"),
    recipe(3, "Plain rice", "rice"),
]


def never_read():
    """A recipes argument that fails the test if search_with_pantry reads it."""
    raise AssertionError("recipes were read for an empty pantry")
    yield  # makes this a generator, so the error only fires when iterated


@pytest.mark.parametrize("names", [[], [""], ["   "], [None, "", "\t"]])
def test_empty_pantry_skips_ranking(names):
    assert search_with_pantry(names, never_read()) == PantrySearchResult(STATUS_EMPTY_PANTRY)


def test_no_recipe_shares_an_ingredient():
    assert search_with_pantry(["chocolate"], RECIPES) == PantrySearchResult(STATUS_NO_MATCHES)


def test_pantry_items_but_no_recipes_at_all_is_no_matches():
    assert search_with_pantry(["egg"], []).status == STATUS_NO_MATCHES


def test_matches_are_ok_and_ranked_like_rank_recipes():
    result = search_with_pantry(["egg", "milk"], RECIPES)
    assert result.status == STATUS_OK
    assert result.results == tuple(rank_recipes(["egg", "milk"], RECIPES))
    assert [r.title for r in result.results] == ["Boiled egg", "Omelette"]


def test_name_with_a_comma_is_not_split():
    recipes = [recipe(1, "Seasoning", "salt, pepper"), recipe(2, "Salted", "salt")]
    result = search_with_pantry(["salt, pepper"], recipes)
    assert [r.title for r in result.results] == ["Seasoning"]


def test_repeated_and_blank_names_are_ignored():
    result = search_with_pantry(["egg", "", "egg", None], RECIPES)
    assert result.results == search_with_pantry(["egg"], RECIPES).results


def test_accepts_any_iterable_of_names():
    names = (item for item in ["rice"])  # e.g. a generator over pantry items
    assert [r.title for r in search_with_pantry(names, RECIPES).results] == ["Plain rice"]
