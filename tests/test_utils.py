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
