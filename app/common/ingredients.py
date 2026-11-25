"""Ingredient-name normalization shared by the recipe loader, pantry and search."""

# Plurals the suffix rules below would get wrong.
_IRREGULAR_PLURALS = {
    "leaves": "leaf",
    "halves": "half",
    "loaves": "loaf",
    "cookies": "cookie",
    "brownies": "brownie",
    "pies": "pie",
}

# Words that end in "s" but are already singular (or uncountable).
_NEVER_SINGULARIZE = {"hummus", "couscous", "asparagus", "molasses", "swiss", "grass"}


def _singularize(word):
    """Return the singular form of one lowercase English word (best effort)."""
    if word in _IRREGULAR_PLURALS:
        return _IRREGULAR_PLURALS[word]
    if word in _NEVER_SINGULARIZE:
        return word
    if word.endswith("ies"):
        return word[:-3] + "y"  # berries -> berry
    if word.endswith("oes"):
        return word[:-2]  # tomatoes -> tomato
    if word.endswith(("ches", "shes", "xes", "sses")):
        return word[:-2]  # peaches -> peach
    if word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]  # peas -> pea
    return word


def normalize_ingredient(name):
    """Return a canonical form of an ingredient name for matching.

    The same function is applied to recipe ingredients (by the loader) and
    to pantry/search input, so that "  Cherry  Tomatoes " and "cherry tomato"
    compare as equal.
    """
    # split() with no argument drops leading/trailing whitespace and treats
    # any run of spaces, tabs or newlines as one separator.
    words = name.lower().split()
    if words:
        # Only the last word is the noun in names like "cherry tomatoes".
        words[-1] = _singularize(words[-1])
    return " ".join(words)
