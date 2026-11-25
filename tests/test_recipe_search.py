import pytest

from app.recipes.search import (
    EMPTY_INPUT_MESSAGE,
    RecipeData,
    SearchResult,
    match_recipe,
    parse_ingredient_input,
)


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
