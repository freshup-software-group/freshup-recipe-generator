import pytest

from app.utils import normalize_ingredient


def test_lowercases_name():
    assert normalize_ingredient("Chicken Breast") == "chicken breast"


def test_trims_surrounding_whitespace():
    assert normalize_ingredient("  garlic \t\n") == "garlic"


def test_collapses_inner_whitespace():
    assert normalize_ingredient("olive   oil") == "olive oil"


def test_already_normalized_name_is_unchanged():
    assert normalize_ingredient("salt") == "salt"


def test_blank_name_becomes_empty_string():
    assert normalize_ingredient("   ") == ""


@pytest.mark.parametrize("plural, singular", [
    ("cloves", "clove"),        # plain "s"
    ("cheeses", "cheese"),      # "-ses" that is not "-sses"
    ("chickpeas", "chickpea"),  # plain "s"
    ("berries", "berry"),       # "-ies" -> "-y"
    ("anchovies", "anchovy"),   # "-ies" -> "-y"
    ("potatoes", "potato"),     # "-oes" -> "-o"
    ("peaches", "peach"),       # "-ches"
    ("radishes", "radish"),     # "-shes"
    ("boxes", "box"),           # "-xes"
    ("leaves", "leaf"),         # irregular
    ("cookies", "cookie"),      # irregular ("-ies" rule would give "cooky")
    ("pies", "pie"),            # irregular ("-ies" rule would give "py")
])
def test_plural_becomes_singular(plural, singular):
    assert normalize_ingredient(plural) == singular


@pytest.mark.parametrize("plural, singular", [
    ("Cloves", "clove"),
    ("Cheeses", "cheese"),
    ("Potatoes", "potato"),
    ("Anchovies", "anchovy"),
    ("Chickpeas", "chickpea"),
])
def test_plural_and_singular_normalize_to_same_value(plural, singular):
    # What matters for matching: pantry "chickpea" must equal recipe "Chickpeas".
    assert normalize_ingredient(plural) == normalize_ingredient(singular)


@pytest.mark.parametrize("word", [
    "hummus", "couscous", "asparagus", "molasses", "swiss",  # never-change list
    "hibiscus", "glass",                                     # "-us" / "-ss" endings
    "tomato", "berry", "peach", "cheese",                    # already singular
])
def test_singular_or_uncountable_word_is_unchanged(word):
    assert normalize_ingredient(word) == word


def test_only_last_word_is_singularized():
    assert normalize_ingredient("  Cherry  Tomatoes ") == "cherry tomato"
    assert normalize_ingredient("Brussels Sprouts") == "brussels sprout"
