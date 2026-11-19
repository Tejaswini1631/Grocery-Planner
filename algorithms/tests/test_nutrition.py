from datetime import date

import pytest

from app.nutrition import ingredient_nutrients, recipe_total, summarize
from app.schemas import (
    MealEntry,
    Nutrients,
    NutritionIngredient,
    NutritionRecipe,
    NutritionRequest,
)
from app.units import UnitError

RICE_PER_100 = Nutrients(calories=130, protein_g=2.7, carbs_g=28, fat_g=0.3)
OIL_PER_100 = Nutrients(calories=884, protein_g=0, carbs_g=0, fat_g=100)


def rice(quantity=200, unit="g"):
    return NutritionIngredient(quantity=quantity, unit=unit, base_unit="g", nutrition_per_100=RICE_PER_100)


def oil(quantity=1, unit="tbsp"):
    return NutritionIngredient(quantity=quantity, unit=unit, base_unit="ml", nutrition_per_100=OIL_PER_100)


def meal(recipe_ingredients, servings_in_recipe=2):
    return NutritionRecipe(servings=servings_in_recipe, ingredients=recipe_ingredients)


def test_ingredient_nutrients_scale_by_quantity():
    n = ingredient_nutrients(rice(200))

    assert n.calories == pytest.approx(260)
    assert n.protein_g == pytest.approx(5.4)
    assert n.carbs_g == pytest.approx(56)
    assert n.fat_g == pytest.approx(0.6)


def test_units_are_converted_to_the_base_unit_first():
    # 2 tbsp = 30 ml
    assert ingredient_nutrients(oil(2, "tbsp")).calories == pytest.approx(265.2)


def test_count_based_ingredient():
    egg = NutritionIngredient(
        quantity=2,
        unit="pcs",
        base_unit="count",
        nutrition_per_100=Nutrients(calories=7800, protein_g=630, carbs_g=60, fat_g=530),
    )

    assert ingredient_nutrients(egg).calories == pytest.approx(156)


def test_density_bridges_mass_and_volume():
    ing = NutritionIngredient(
        quantity=92, unit="g", base_unit="ml", nutrition_per_100=OIL_PER_100, density_g_per_ml=0.92
    )

    # 92 g at 0.92 g/ml = 100 ml
    assert ingredient_nutrients(ing).calories == pytest.approx(884)


def test_incompatible_units_raise():
    ing = NutritionIngredient(quantity=100, unit="g", base_unit="ml", nutrition_per_100=OIL_PER_100)

    with pytest.raises(UnitError):
        ingredient_nutrients(ing)


def test_recipe_total_sums_all_ingredients():
    total = recipe_total(meal([rice(200), oil(1, "tbsp")]))

    assert total.calories == pytest.approx(392.6)
    assert total.protein_g == pytest.approx(5.4)
    assert total.carbs_g == pytest.approx(56)
    assert total.fat_g == pytest.approx(15.6)


def test_summarize_scales_by_servings_eaten_and_groups_by_day():
    recipe = meal([rice(200), oil(1, "tbsp")], servings_in_recipe=2)
    request = NutritionRequest(
        entries=[
            MealEntry(day=date(2026, 11, 20), slot="lunch", servings=1, recipe=recipe),
            MealEntry(day=date(2026, 11, 20), slot="dinner", servings=2, recipe=recipe),
            MealEntry(day=date(2026, 11, 21), slot="dinner", servings=1, recipe=recipe),
        ]
    )

    result = summarize(request)

    assert [e.nutrients.calories for e in result.entries] == [196.3, 392.6, 196.3]
    assert [(d.day, d.nutrients.calories) for d in result.by_day] == [
        (date(2026, 11, 20), 588.9),
        (date(2026, 11, 21), 196.3),
    ]
    assert result.total.calories == 785.2
    assert result.total.protein_g == 10.8
    assert result.total.carbs_g == 112.0
    assert result.total.fat_g == 31.2


def test_entries_without_a_day_are_grouped_last():
    recipe = meal([rice(100)], servings_in_recipe=1)
    request = NutritionRequest(
        entries=[
            MealEntry(day=None, recipe=recipe),
            MealEntry(day=date(2026, 11, 20), recipe=recipe),
        ]
    )

    assert [d.day for d in summarize(request).by_day] == [date(2026, 11, 20), None]


def test_empty_request_returns_zero_totals():
    result = summarize(NutritionRequest(entries=[]))

    assert result.entries == []
    assert result.by_day == []
    assert result.total == Nutrients()
