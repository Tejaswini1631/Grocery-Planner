"""Nutrition / macro totals for recipes and meal plans."""
from __future__ import annotations

from datetime import date

from .schemas import (
    DayNutrition,
    EntryNutrition,
    NutritionIngredient,
    NutritionRecipe,
    NutritionRequest,
    NutritionResponse,
    Nutrients,
)
from .units import convert_quantity

ROUND_DIGITS = 1


def _add(a: Nutrients, b: Nutrients) -> Nutrients:
    return Nutrients(
        calories=a.calories + b.calories,
        protein_g=a.protein_g + b.protein_g,
        carbs_g=a.carbs_g + b.carbs_g,
        fat_g=a.fat_g + b.fat_g,
    )


def _scale(n: Nutrients, factor: float) -> Nutrients:
    return Nutrients(
        calories=n.calories * factor,
        protein_g=n.protein_g * factor,
        carbs_g=n.carbs_g * factor,
        fat_g=n.fat_g * factor,
    )


def _rounded(n: Nutrients) -> Nutrients:
    return Nutrients(
        calories=round(n.calories, ROUND_DIGITS),
        protein_g=round(n.protein_g, ROUND_DIGITS),
        carbs_g=round(n.carbs_g, ROUND_DIGITS),
        fat_g=round(n.fat_g, ROUND_DIGITS),
    )


def ingredient_nutrients(ingredient: NutritionIngredient) -> Nutrients:
    """Nutrients in one recipe line, after converting its quantity to the base unit.

    Raises UnitError if the unit cannot be converted to the ingredient's base unit.
    """
    amount = convert_quantity(
        ingredient.quantity,
        ingredient.unit,
        ingredient.base_unit,
        ingredient.density_g_per_ml,
    )
    return _scale(ingredient.nutrition_per_100, amount / 100.0)


def recipe_total(recipe: NutritionRecipe) -> Nutrients:
    """Nutrients in the whole recipe (all servings)."""
    total = Nutrients()
    for ingredient in recipe.ingredients:
        total = _add(total, ingredient_nutrients(ingredient))
    return total


def summarize(request: NutritionRequest) -> NutritionResponse:
    """Per-entry, per-day and grand totals for a list of planned meals."""
    entries: list[EntryNutrition] = []
    by_day: dict[date | None, Nutrients] = {}
    total = Nutrients()

    for entry in request.entries:
        eaten = _scale(recipe_total(entry.recipe), entry.servings / entry.recipe.servings)
        entries.append(EntryNutrition(day=entry.day, slot=entry.slot, nutrients=_rounded(eaten)))
        by_day[entry.day] = _add(by_day.get(entry.day, Nutrients()), eaten)
        total = _add(total, eaten)

    ordered_days = sorted(by_day.items(), key=lambda item: (item[0] is None, item[0] or date.min))
    return NutritionResponse(
        entries=entries,
        by_day=[DayNutrition(day=day, nutrients=_rounded(n)) for day, n in ordered_days],
        total=_rounded(total),
    )
