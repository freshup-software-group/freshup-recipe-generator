# Tests for get_recipe helpers (UC-09, #12)
from types import SimpleNamespace

from app.recipes.service import RecipeDetails, to_details


# Build a fake recipe row so tests do not need the database
# Pass any field to override the default
def make_recipe(**overrides):
    data = dict(
        id=1,
        title="Pasta",
        ingredients=[
            SimpleNamespace(ingredient_name="penne rigate"),
            SimpleNamespace(ingredient_name="olive oil"),
            SimpleNamespace(ingredient_name="garlic"),
        ],
        instructions="Boil the pasta",
        meal_type="dessert",
        diet_tags="vegan,vegetarian",
        cuisine="Italian",
        image_url="https://example.com/pasta.jpg",
    )
    data.update(overrides)
    return SimpleNamespace(**data)


# to_details gives back a RecipeDetails object
def test_returns_recipe_details():
    assert isinstance(to_details(make_recipe()), RecipeDetails)


# id and title are copied as they are
def test_copies_id_and_title():
    details = to_details(make_recipe(id=7, title="Soup"))
    assert details.id == 7
    assert details.title == "Soup"


# Ingredient names keep the recipe's order
def test_ingredient_names_in_order():
    details = to_details(make_recipe())
    assert details.ingredient_names == [
        "penne rigate", "olive oil", "garlic"]


# Instructions, meal type, cuisine and image are copied over
def test_copies_text_fields():
    details = to_details(make_recipe())
    assert details.instructions == "Boil the pasta"
    assert details.meal_type == "dessert"
    assert details.cuisine == "Italian"
    assert details.image_url == "https://example.com/pasta.jpg"


# diet_tags stored as text becomes a clean list
def test_diet_tags_text_becomes_list():
    details = to_details(make_recipe(diet_tags=" vegan , vegetarian "))
    assert details.diet_tags == ["vegan", "vegetarian"]


# diet_tags that is already a list stays the same
def test_diet_tags_list_is_kept():
    details = to_details(make_recipe(diet_tags=["vegan"]))
    assert details.diet_tags == ["vegan"]


# Empty database fields become "" or [] instead of None
def test_none_fields_become_empty():
    details = to_details(make_recipe(
        instructions=None,
        meal_type=None,
        diet_tags=None,
        cuisine=None,
        image_url=None,
    ))
    assert details.instructions == ""
    assert details.meal_type == ""
    assert details.diet_tags == []
    assert details.cuisine == ""
    assert details.image_url == ""


# A recipe with no ingredients gives an empty list
def test_no_ingredients_gives_empty_list():
    details = to_details(make_recipe(ingredients=[]))
    assert details.ingredient_names == []
