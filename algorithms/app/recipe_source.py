"""Where recipes come from when the /match request does not include them.

The contract sends only the pantry, so the service reads recipes from the
database tables defined in CONTRACTS.md (contract 5):

    recipes(id, name)
    recipe_ingredients(recipe_id, ingredient_name, quantity, unit)

Set DATABASE_URL (e.g. postgresql://user:password@db:5432/mealplanner) to enable it.
The service only reads these two tables.
"""
from __future__ import annotations

import os
from typing import Protocol

from .schemas import Recipe, RecipeIngredient


class RecipeSource(Protocol):
    def load(self) -> list[Recipe]: ...


class PostgresRecipeSource:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def load(self) -> list[Recipe]:
        # Imported here so tests and tooling do not need a database driver.
        import psycopg

        with psycopg.connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute("SELECT id, name FROM recipes ORDER BY id")
            names = dict(cur.fetchall())

            cur.execute(
                "SELECT recipe_id, ingredient_name, quantity, unit "
                "FROM recipe_ingredients ORDER BY recipe_id"
            )
            lines: dict[int, list[RecipeIngredient]] = {}
            for recipe_id, ingredient_name, quantity, unit in cur.fetchall():
                if recipe_id not in names or quantity is None or float(quantity) <= 0:
                    continue
                lines.setdefault(recipe_id, []).append(
                    RecipeIngredient(
                        ingredient_name=ingredient_name, quantity=float(quantity), unit=unit
                    )
                )

        return [Recipe(id=rid, name=names[rid], ingredients=ings) for rid, ings in lines.items()]


def get_recipe_source() -> RecipeSource | None:
    """FastAPI dependency. None when DATABASE_URL is not set."""
    dsn = os.getenv("DATABASE_URL")
    return PostgresRecipeSource(dsn) if dsn else None
