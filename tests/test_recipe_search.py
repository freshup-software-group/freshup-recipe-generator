from app.recipes.search import parse_ingredient_input


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
