import pytest

from app.schemas import MatchRequest, PantryItem, Recipe, RecipeIngredient
from app.scoring import rank_recipes, urgency


def pantry(name, quantity, unit="g", days_left=None, density=None):
    return PantryItem(
        name=name, quantity=quantity, unit=unit, days_left=days_left, density_g_per_ml=density
    )


def line(name, quantity, unit="g", density=None):
    return RecipeIngredient(
        ingredient_name=name, quantity=quantity, unit=unit, density_g_per_ml=density
    )


def recipe(recipe_id, name, lines):
    return Recipe(id=recipe_id, name=name, ingredients=lines)


def run(pantry_items, recipes, **kwargs):
    return rank_recipes(MatchRequest(pantry=pantry_items, **kwargs), recipes)


# ------------------------------------------------------------- urgency ------

def test_urgency_values():
    assert urgency(0) == 1.0
    assert urgency(1) == 0.5
    assert urgency(9) == pytest.approx(0.1)


def test_urgency_never_exceeds_one_for_past_dates():
    assert urgency(-3) == 1.0


# ------------------------------------------------------- expiry weighting ---

def test_recipe_using_expiring_item_ranks_first():
    items = [pantry("spinach", 200, days_left=1), pantry("rice", 500, days_left=194)]
    recipes = [
        recipe(2, "Plain rice", [line("rice", 100)]),
        recipe(1, "Spinach saute", [line("spinach", 100)]),
    ]

    results = run(items, recipes)

    assert [r.recipe_id for r in results] == [1, 2]
    assert results[0].score == pytest.approx(0.85)  # 0.7 * 1 + 0.3 * (1 / 2)
    assert results[1].score == pytest.approx(0.7015, abs=1e-4)  # 0.7 * 1 + 0.3 * (1 / 195)


def test_item_expiring_today_gets_full_urgency():
    items = [pantry("milk", 500, "ml", days_left=0)]

    results = run(items, [recipe(1, "Porridge", [line("milk", 200, "ml")])])

    assert results[0].score == pytest.approx(1.0)


def test_expired_items_are_ignored():
    items = [pantry("milk", 500, "ml", days_left=-1)]

    result = run(items, [recipe(1, "Porridge", [line("milk", 200, "ml")])])[0]

    assert result.score == 0
    assert result.missing == ["milk"]


def test_item_without_expiry_gets_no_bonus():
    items = [pantry("rice", 500)]

    result = run(items, [recipe(1, "Plain rice", [line("rice", 100)])])[0]

    assert result.score == pytest.approx(0.7)
    assert result.missing == []


def test_soonest_expiring_lot_drives_the_urgency():
    items = [pantry("rice", 100, days_left=194), pantry("rice", 100, days_left=1)]

    result = run(items, [recipe(1, "Plain rice", [line("rice", 150)])])[0]

    assert result.score == pytest.approx(0.85)


def test_partial_amount_of_an_expiring_item_gets_partial_credit():
    items = [pantry("rice", 50, days_left=0)]

    result = run(items, [recipe(1, "Plain rice", [line("rice", 100)])])[0]

    assert result.score == pytest.approx(0.5)  # 0.7 * 0.5 + 0.3 * (0.5 * 1)


def test_score_stays_between_0_and_1():
    items = [pantry("rice", 500, days_left=0), pantry("lentils", 500, days_left=0)]
    recipes = [recipe(1, "Dal rice", [line("rice", 100), line("lentils", 100)])]

    assert 0 <= run(items, recipes)[0].score <= 1


# ------------------------------------------------------------- coverage -----

def test_partial_quantity_gives_partial_coverage():
    items = [pantry("rice", 50)]

    result = run(items, [recipe(1, "Plain rice", [line("rice", 100)])])[0]

    assert result.score == pytest.approx(0.35)
    assert result.missing == ["rice"]


def test_multiple_lots_are_summed_across_units():
    items = [pantry("rice", 60), pantry("rice", 0.04, "kg")]

    result = run(items, [recipe(1, "Plain rice", [line("rice", 100)])])[0]

    assert result.score == pytest.approx(0.7)
    assert result.missing == []


def test_coverage_is_the_average_over_recipe_lines():
    items = [pantry("rice", 500)]
    recipes = [recipe(1, "Dal rice", [line("rice", 100), line("lentils", 100)])]

    result = run(items, recipes)[0]

    assert result.score == pytest.approx(0.35)
    assert result.missing == ["lentils"]


def test_zero_quantity_pantry_item_counts_as_missing():
    items = [pantry("rice", 0)]

    result = run(items, [recipe(1, "Plain rice", [line("rice", 100)])])[0]

    assert result.score == 0
    assert result.missing == ["rice"]


def test_names_are_matched_ignoring_case_and_spaces():
    items = [pantry(" Spinach ", 200)]

    result = run(items, [recipe(1, "Saute", [line("spinach", 100)])])[0]

    assert result.missing == []


def test_pantry_unit_is_converted_to_the_recipe_unit():
    items = [pantry("flour", 1, "cup")]

    result = run(items, [recipe(1, "Roti", [line("flour", 120, "ml")])])[0]

    assert result.score == pytest.approx(0.7)
    assert result.missing == []


def test_unit_mismatch_without_density_gets_half_credit():
    items = [pantry("milk", 1, "l")]

    result = run(items, [recipe(1, "Porridge", [line("milk", 200, "g")])])[0]

    assert result.score == pytest.approx(0.35)
    assert result.missing == ["milk"]


def test_density_resolves_a_mass_volume_mismatch():
    items = [pantry("milk", 1, "l")]

    result = run(items, [recipe(1, "Porridge", [line("milk", 200, "g", density=1.03)])])[0]

    assert result.score == pytest.approx(0.7)
    assert result.missing == []


def test_unknown_pantry_unit_is_a_mismatch_not_a_crash():
    items = [pantry("spinach", 1, "bunch")]

    result = run(items, [recipe(1, "Saute", [line("spinach", 100)])])[0]

    assert result.score == pytest.approx(0.35)
    assert result.missing == ["spinach"]


# ----------------------------------------------- exclusions, ranking, limits

def test_recipe_with_excluded_ingredient_is_dropped():
    items = [pantry("rice", 500), pantry("peanut", 100)]
    recipes = [
        recipe(1, "Peanut rice", [line("rice", 100), line("peanut", 50)]),
        recipe(2, "Plain rice", [line("rice", 100)]),
    ]

    results = run(items, recipes, excluded_ingredients=["Peanut"])

    assert [r.recipe_id for r in results] == [2]


def test_min_coverage_and_limit():
    items = [pantry("rice", 500)]
    recipes = [
        recipe(1, "Full", [line("rice", 100)]),
        recipe(2, "Half", [line("rice", 100), line("lentils", 100)]),
        recipe(3, "None", [line("lentils", 100)]),
    ]

    assert [r.recipe_id for r in run(items, recipes, min_coverage=0.5)] == [1, 2]
    assert [r.recipe_id for r in run(items, recipes, limit=1)] == [1]


def test_equal_scores_are_ordered_by_name():
    items = [pantry("rice", 500)]
    recipes = [
        recipe(1, "Zucchini rice", [line("rice", 100)]),
        recipe(2, "Apple rice", [line("rice", 100)]),
    ]

    assert [r.name for r in run(items, recipes)] == ["Apple rice", "Zucchini rice"]


def test_empty_pantry_returns_all_recipes_with_zero_score():
    results = run([], [recipe(1, "Plain rice", [line("rice", 100)])])

    assert len(results) == 1
    assert results[0].score == 0
    assert results[0].missing == ["rice"]
