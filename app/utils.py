"""Shared helpers used by the recipe loader, pantry and search modules."""


def normalize_ingredient(name):
    """Return a canonical form of an ingredient name for matching.

    The same function is applied to recipe ingredients (by the loader) and
    to pantry/search input, so that "  Olive  Oil " and "olive oil" compare
    as equal.
    """
    # split() with no argument drops leading/trailing whitespace and treats
    # any run of spaces, tabs or newlines as one separator.
    return " ".join(name.split()).lower()
