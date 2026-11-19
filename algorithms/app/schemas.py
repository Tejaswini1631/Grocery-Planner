"""Request and response shapes of the algorithms service.

The /match shapes follow the root CONTRACTS.md (contract 3). The recipe shapes
mirror the database tables in contract 5 (recipes, recipe_ingredients).
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------- /match ----

class PantryItem(BaseModel):
    name: str
    quantity: float = Field(ge=0)
    unit: str
    # Days until expiry. Omit/null = never expires; negative = already expired.
    days_left: int | None = None
    # Optional extra: only needed to compare a mass with a volume.
    density_g_per_ml: float | None = Field(default=None, gt=0)


class RecipeIngredient(BaseModel):
    ingredient_name: str  # same name as recipe_ingredients.ingredient_name
    quantity: float = Field(gt=0)
    unit: str
    density_g_per_ml: float | None = Field(default=None, gt=0)


class Recipe(BaseModel):
    id: int
    name: str
    ingredients: list[RecipeIngredient] = Field(min_length=1)


class MatchRequest(BaseModel):
    pantry: list[PantryItem]
    # Optional. The contract sends only the pantry, and the service then loads
    # recipes from the database. Sending recipes here skips the database.
    recipes: list[Recipe] | None = None
    # Optional extras (allergies / dislikes by ingredient name, result limits).
    excluded_ingredients: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=100)
    min_coverage: float = Field(default=0.0, ge=0.0, le=1.0)


class MatchResult(BaseModel):
    recipe_id: int
    name: str
    score: float  # 0..1
    missing: list[str]  # ingredient names still needed (not in the pantry, or not enough)


# -------------------------------------------------------------- /convert ----

class ConvertRequest(BaseModel):
    quantity: float = Field(ge=0)
    from_unit: str
    to_unit: str
    density_g_per_ml: float | None = Field(default=None, gt=0)


class ConvertResponse(BaseModel):
    quantity: float
    unit: str


# ------------------------------------------------------------ /nutrition ----

class Nutrients(BaseModel):
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0


class NutritionIngredient(BaseModel):
    quantity: float = Field(gt=0)
    unit: str
    # The ingredient's base unit; nutrition_per_100 is per 100 of this unit
    # (per 100 g, per 100 ml, or per 100 pieces).
    base_unit: Literal["g", "ml", "count"]
    nutrition_per_100: Nutrients
    density_g_per_ml: float | None = Field(default=None, gt=0)


class NutritionRecipe(BaseModel):
    servings: int = Field(default=1, ge=1)
    ingredients: list[NutritionIngredient]


class MealEntry(BaseModel):
    day: date | None = None
    slot: str | None = None  # breakfast / lunch / dinner
    servings: float = Field(default=1.0, gt=0)  # servings eaten
    recipe: NutritionRecipe


class NutritionRequest(BaseModel):
    entries: list[MealEntry]


class EntryNutrition(BaseModel):
    day: date | None = None
    slot: str | None = None
    nutrients: Nutrients


class DayNutrition(BaseModel):
    day: date | None = None
    nutrients: Nutrients


class NutritionResponse(BaseModel):
    entries: list[EntryNutrition]
    by_day: list[DayNutrition]
    total: Nutrients
