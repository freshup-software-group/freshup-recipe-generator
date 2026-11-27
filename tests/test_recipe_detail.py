# Tests for the recipe details page (UC-09, #12)


# A recipe that does not exist shows the 404 page
def test_missing_recipe_shows_404(client):
    response = client.get("/recipes/99999")
    assert response.status_code == 404
    assert b"Page not found" in response.data
