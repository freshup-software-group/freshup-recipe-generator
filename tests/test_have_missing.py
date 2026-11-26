# Tests for splitting recipe ingredients into have and missing (FR-4.3, FR-4.4)
from app.recipes.service import split_have_missing


# Ingredients in the pantry go to have, the rest go to missing
def test_splits_have_and_missing():
    have, missing = split_have_missing(
        ["pasta", "garlic", "basil"], ["garlic", "pasta"])
    assert have == ["pasta", "garlic"]
    assert missing == ["basil"]


# Case and extra spaces do not matter when matching
def test_ignores_case_and_spaces():
    have, missing = split_have_missing(
        ["Olive Oil", "garlic"], ["  olive   oil "])
    assert have == ["Olive Oil"]
    assert missing == ["garlic"]


# With an empty pantry everything is missing
def test_empty_pantry_all_missing():
    have, missing = split_have_missing(["pasta", "garlic"], [])
    assert have == []
    assert missing == ["pasta", "garlic"]


# When the pantry has everything nothing is missing
def test_all_in_pantry_nothing_missing():
    have, missing = split_have_missing(["pasta"], ["pasta", "salt"])
    assert have == ["pasta"]
    assert missing == []


# A different normalize function can be passed in
# Here it treats scallion and green onion as the same thing
def test_custom_normalize_is_used():
    def same_onion(name):
        return name.replace("scallion", "green onion")

    have, missing = split_have_missing(
        ["scallion"], ["green onion"], normalize=same_onion)
    assert have == ["scallion"]
    assert missing == []


# Singular and plural count as the same ingredient (FR-3.4)
def test_singular_and_plural_match():
    have, missing = split_have_missing(["eggs", "garlic"], ["egg"])
    assert have == ["eggs"]
    assert missing == ["garlic"]
