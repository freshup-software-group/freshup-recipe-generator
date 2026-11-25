import json
from pathlib import Path

import pytest

from app.recipes.search import (
    EMPTY_INPUT_MESSAGE,
    RecipeData,
    SearchResult,
    match_recipe,
    parse_ingredient_input,
    rank_recipes,
)
from app.themealdb import parse_meal

SAMPLE_PATH = Path(__file__).parent / "data" / "themealdb_sample.json"


def test_single_ingredient_is_normalized():
    assert parse_ingredient_input("  Tomatoes ") == ["tomato"]


def test_splits_on_commas_and_normalizes_each_name():
    assert parse_ingredient_input("Eggs,Milk, Cherry Tomatoes") == [
        "egg", "milk", "cherry tomato",
    ]


def test_keeps_the_order_the_user_typed():
    assert parse_ingredient_input("rice, garlic, butter") == ["rice", "garlic", "butter"]


def test_drops_blank_entries():
    assert parse_ingredient_input(",egg,, ,  ,onion,") == ["egg", "onion"]


def test_removes_duplicates_after_normalization():
    assert parse_ingredient_input("Tomatoes, tomato") == ["tomato"]


def test_duplicates_keep_first_seen_order():
    assert parse_ingredient_input("garlic, Eggs, GARLIC , egg, rice") == [
        "garlic", "egg", "rice",
    ]


@pytest.mark.parametrize("text", [None, "", "   ", ",", " , ,\t, "])
def test_no_ingredient_raises_clear_error(text):
    with pytest.raises(ValueError, match="Enter at least one ingredient"):
        parse_ingredient_input(text)


def test_error_message_is_exposed_for_the_route():
    with pytest.raises(ValueError) as error:
        parse_ingredient_input("")
    assert str(error.value) == EMPTY_INPUT_MESSAGE


OMELETTE = RecipeData(id=1, title="Omelette", ingredient_names=("egg", "milk", "butter", "salt"))


def test_match_recipe_splits_matched_and_missing_in_recipe_order():
    result = match_recipe(["salt", "egg"], OMELETTE)
    assert result == SearchResult(
        id=1,
        title="Omelette",
        matched=("egg", "salt"),
        missing=("milk", "butter"),
        score=0.5,
    )


def test_match_recipe_normalizes_both_sides():
    recipe = RecipeData(id=2, title="Salad", ingredient_names=("Cherry Tomatoes", " Olive Oil"))
    result = match_recipe(["cherry tomato", "OLIVE OIL "], recipe)
    assert result.matched == ("cherry tomato", "olive oil")
    assert result.missing == ()
    assert result.score == 1.0


def test_match_recipe_with_no_common_ingredient_scores_zero():
    result = match_recipe(["rice"], OMELETTE)
    assert result.matched == ()
    assert result.missing == ("egg", "milk", "butter", "salt")
    assert result.score == 0.0


def test_match_recipe_score_is_fraction_of_recipe_ingredients():
    assert match_recipe(["egg", "milk", "butter"], OMELETTE).score == pytest.approx(0.75)


def test_match_recipe_accepts_any_object_with_the_three_attributes():
    class FakeModel:  # stands in for the future Recipe model / get_recipe() result
        id = 7
        title = "Toast"
        ingredient_names = ["bread", "butter"]

    result = match_recipe(["butter"], FakeModel())
    assert (result.id, result.title, result.matched) == (7, "Toast", ("butter",))


def test_search_result_is_read_only():
    result = match_recipe(["egg"], OMELETTE)
    with pytest.raises(AttributeError):
        result.score = 1.0


def test_match_recipe_with_no_ingredients_scores_zero_without_crashing():
    recipe = RecipeData(id=3, title="Water", ingredient_names=())
    assert match_recipe(["egg"], recipe) == SearchResult(
        id=3, title="Water", matched=(), missing=(), score=0.0,
    )


def test_match_recipe_counts_duplicate_recipe_ingredients_once():
    recipe = RecipeData(id=4, title="Eggs", ingredient_names=("egg", "Eggs", "salt", "egg"))
    result = match_recipe(["egg"], recipe)
    assert result.matched == ("egg",)
    assert result.missing == ("salt",)
    assert result.score == 0.5


def test_match_recipe_duplicate_missing_ingredient_listed_once():
    recipe = RecipeData(id=5, title="Toast", ingredient_names=("butter", "bread", "Butter"))
    assert match_recipe(["bread"], recipe).missing == ("butter",)


def recipe(recipe_id, title, *names):
    return RecipeData(id=recipe_id, title=title, ingredient_names=names)


def titles(results):
    return [result.title for result in results]


def test_rank_recipes_sorts_by_score_descending():
    recipes = [
        recipe(1, "Half", "egg", "flour"),          # 1/2
        recipe(2, "Full", "egg"),                   # 1/1
        recipe(3, "Quarter", "egg", "a", "b", "c"),  # 1/4
    ]
    assert titles(rank_recipes(["egg"], recipes)) == ["Full", "Half", "Quarter"]


def test_rank_recipes_breaks_score_tie_by_matched_count():
    recipes = [
        recipe(1, "Small", "egg", "flour"),                  # 1/2
        recipe(2, "Big", "egg", "milk", "flour", "sugar"),   # 2/4
    ]
    assert titles(rank_recipes(["egg", "milk"], recipes)) == ["Big", "Small"]


def test_rank_recipes_breaks_full_tie_by_title_ignoring_case():
    recipes = [recipe(1, "omelette", "egg"), recipe(2, "Boiled egg", "egg"),
               recipe(3, "Coddled egg", "egg")]
    assert titles(rank_recipes(["egg"], recipes)) == ["Boiled egg", "Coddled egg", "omelette"]


def test_rank_recipes_excludes_recipes_with_zero_matches():
    recipes = [recipe(1, "Rice", "rice"), recipe(2, "Toast", "bread", "butter"),
               recipe(3, "Empty")]
    results = rank_recipes(["butter"], recipes)
    assert [result.id for result in results] == [2]


def test_rank_recipes_returns_search_results():
    [result] = rank_recipes(["Eggs"], [recipe(9, "Omelette", "egg", "milk")])
    assert result == SearchResult(
        id=9, title="Omelette", matched=("egg",), missing=("milk",), score=0.5,
    )


def test_rank_recipes_with_no_matches_at_all_returns_empty_list():
    recipes = [recipe(1, "Rice", "rice"), recipe(2, "Toast", "bread", "butter")]
    assert rank_recipes(["chocolate"], recipes) == []


@pytest.fixture
def sample_recipes():
    """The saved TheMealDB sample, run through the loader's parse_meal()."""
    with SAMPLE_PATH.open(encoding="utf-8") as f:
        meals = json.load(f)["meals"]
    return [
        RecipeData(
            id=int(data["external_id"]),
            title=data["title"],
            ingredient_names=tuple(name for name, _quantity in data["ingredients"]),
        )
        for data in map(parse_meal, meals)
    ]


def test_rank_recipes_on_saved_sample(sample_recipes):
    results = rank_recipes(parse_ingredient_input("Olive Oil, flour, Butter"), sample_recipes)
    # Padron peppers 1/2, Pancakes (edited copy) 1/7, Bakewell tart 1/10.
    assert [result.id for result in results] == [53150, 99990001, 52767]
    assert results[0].matched == ("olive oil",)
    assert results[0].missing == ("padron pepper",)
    assert results[2].score == pytest.approx(0.1)


def test_rank_recipes_on_saved_sample_with_no_matches(sample_recipes):
    assert rank_recipes(parse_ingredient_input("chocolate, coffee"), sample_recipes) == []
