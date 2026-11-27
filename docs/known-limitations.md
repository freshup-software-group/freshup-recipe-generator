# Known limitations

## Recipe search: exact ingredient matching

**What it is.** Recipe search (UC-07, UC-08) compares ingredient names exactly,
after `normalize_ingredient()` has lowercased, trimmed and singularized them. A
recipe ingredient matches only if its normalized name is identical to one the user
has.

**User-visible example.** A user who enters `onion` does not match a recipe that
lists `chopped onion` or `red onion`. That ingredient shows as missing, and the
recipe ranks lower than it should, or not at all.

### Live-data analysis (2026-11-25)

Run on the full TheMealDB dataset: **790 recipes, 8,152 ingredient rows.** For each
pantry word, the table compares recipes found by exact match with the extra
recipes that matching on the *last word* of the name would add.

| Word | Recipes, exact match | Extra recipes, last word only | Main last-word-only names (rows) |
|---|---|---|---|
| egg | 218 | +4 | free-range egg (3), flax egg (1) |
| tomato | 67 | +64 | cherry (17), tinned (14), plum (12), chopped (12) tomato |
| onion | 251 | +90 | spring onion (66), red onion (39), chopped onion (3) |
| garlic | 237 | +5 | minced garlic (4), pickled garlic (1) |
| chicken | 21 | +0 | (none) |
| butter | 177 | +52 | unsalted (32), melted (15), peanut (8), salted (5) butter |
| milk | 120 | +61 | coconut (40), condensed (11), whole (7) milk |
| rice | 35 | +32 | basmati (11), jasmine (9), paella (5), sushi (3) rice |

Exact matching misses many recipes: for tomato and rice it finds only about half.

### Why last-word matching was rejected

- **False positives.** Different ingredients would match: coconut milk (40 rows)
  and condensed milk (11) for milk, peanut butter (8) and vegan butter (1) for
  butter, flax egg (1) for egg.
- **It still misses the real problem cases**, where the ingredient is not the last
  word: garlic clove (56 rows) is garlic, and chicken breast (27), chicken thigh
  (24) and chicken leg (6) are chicken. Last-word matching finds no extra chicken
  recipes at all.

### Possible future work

Most misses are preparation or variety words, not different ingredients. A
better fix is to extend the shared `normalize_ingredient()`, with the team's
agreement:

- strip a tested list of preparation words: chopped, diced, minced, melted,
  tinned, salted/unsalted, free-range;
- add a few aliases, such as garlic clove → garlic.

Changing the shared function, rather than search alone, keeps recipe search, the
pantry and shopping lists consistent. The recipe data would then need to be
loaded again so stored names are re-normalized.
