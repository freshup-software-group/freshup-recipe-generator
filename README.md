# Freshup Recipe Generator

Find recipes you can cook from the ingredients you already have, see what you are
missing, and turn the missing items into a shopping list.

Built for CIS 553 (Software Engineering), Fall 2026 — University of Michigan-Dearborn.
**Freshup Software Group, Group 4.**

## Team

| Member | Module |
|---|---|
| Percy Fowler | Authentication (UC-01 – UC-03) |
| Hamza Massar (Team Lead) | Shopping lists and delivery (UC-11 – UC-12) |
| Fatima Saad | Pantry management (UC-04 – UC-06) |
| Roberto Parraguez Salamanca | Recipe search and ranking (UC-07 – UC-08) |
| Feride Skender | Recipe details and filtering (UC-09 – UC-10) |

## Technology

Python 3.12 · Flask · SQLAlchemy · PostgreSQL 16 · Flask-Login · Docker ·
pytest · Flake8 · GitHub Actions

## Running the application

The only prerequisite is Docker Desktop.

```bash
git clone https://github.com/freshup-software-group/freshup-recipe-generator.git
cd freshup-recipe-generator
cp .env.example .env
docker compose up --build
```

The application is then available at <http://localhost:5000>.

To load the recipe dataset into the database, create the tables and then run the
loader:

```bash
docker compose exec web flask init-db
docker compose exec web flask load-recipes
```

Without Docker, from the project folder:

```bash
flask --app wsgi.py init-db
flask --app wsgi.py load-recipes
```

The loader needs internet access to TheMealDB and imports about 790 recipes; it
prints how many were created, refreshed and skipped. Re-running it is safe: it
creates new recipes, refreshes existing ones, and never deletes any.

## Data source

Recipes come from the free [TheMealDB](https://www.themealdb.com) API, using its
public test key `1`. It is used for educational and development purposes under
TheMealDB's terms, through the official API only (no scraping).

From each meal we use:

- **Title** and **instructions**
- **Category**, mapped to a meal type (Breakfast, Dessert, Starter, Side; "main" for
  Beef, Chicken, Seafood, Pork, Lamb, Goat and Pasta) or a diet tag (Vegetarian,
  Vegan; vegan recipes are also tagged vegetarian)
- Up to **20 ingredients** with their measures

Ingredient names are normalized (lowercase, trimmed, singular) so they match pantry
items. Text after a comma is kept in the quantity: "egg, beaten" with measure "1" is
stored as ingredient "egg", quantity "1, beaten".

Recipe data provided by TheMealDB.

## Running the tests

```bash
docker compose exec web pytest --cov=app --cov-report=term-missing
```

## Running static analysis

```bash
docker compose exec web flake8 .
```

## Continuous integration

Every pull request to `main` runs the pipeline in `.github/workflows/ci.yml`:

1. Install dependencies
2. Flake8 static analysis — the build fails on any error
3. pytest with a coverage report
4. Docker image build

A pull request cannot be merged unless the pipeline passes and one other team
member has approved it.

## Contributing

1. Pick an issue from the project board and assign yourself.
2. Branch from `main` using `feature/<issue-number>-<short-name>`.
3. Commit in small, meaningful steps, referencing the issue number.
4. Open a pull request that closes the issue and describes the tests you added.
5. Request a review. Merge once CI is green and the review is approved.

## Project documentation

The Phase I and Phase II report, including requirements, use cases, and the
project plan, is submitted separately through Canvas.
