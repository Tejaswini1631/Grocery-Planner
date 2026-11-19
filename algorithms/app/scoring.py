"""Expiry-weighted recipe matching (name-based, as in CONTRACTS.md contract 3).

For each recipe line we work out how much of the needed quantity the pantry
covers (the "ratio", 0..1). Then, per recipe:

    coverage      = average ratio over all lines of the recipe
    urgency(days) = 1 / (days_left + 1)          # today = 1.0, tomorrow = 0.5, ...
    urgency_share = average of (ratio * urgency) over all lines   (0 when no expiry)
    score         = 0.7 * coverage + 0.3 * urgency_share           # always 0..1

So a recipe that uses ingredients expiring soon is lifted above an otherwise
identical recipe that uses long-lived ones. Expired items are never used.
"""
from __future__ import annotations

from dataclasses import dataclass

from .schemas import MatchRequest, MatchResult, PantryItem, Recipe, RecipeIngredient
from .units import UnitError, convert_quantity

COVERAGE_WEIGHT = 0.7
URGENCY_WEIGHT = 0.3
# When a pantry unit cannot be converted to the recipe unit we know the item is
# in the kitchen but not how much, so we give it half credit.
UNKNOWN_UNIT_RATIO = 0.5


@dataclass
class Scored:
    recipe: Recipe
    score: float
    coverage: float
    missing: list[str]


def urgency(days_left: int) -> float:
    """1.0 for items expiring today, falling off as the expiry gets further away."""
    return 1.0 / (max(days_left, 0) + 1)


def normalize_name(name: str) -> str:
    return name.strip().lower()


def build_pantry_index(pantry: list[PantryItem]) -> dict[str, list[PantryItem]]:
    """Group usable pantry lots by ingredient name, dropping expired and empty ones."""
    index: dict[str, list[PantryItem]] = {}
    for item in pantry:
        if item.days_left is not None and item.days_left < 0:
            continue
        if item.quantity <= 0:
            continue
        index.setdefault(normalize_name(item.name), []).append(item)
    return index


def _match_line(line: RecipeIngredient, lots: list[PantryItem]) -> tuple[float, int | None]:
    """Return (ratio, days_left of the soonest-expiring lot)."""
    if not lots:
        return 0.0, None

    expiry_days = [lot.days_left for lot in lots if lot.days_left is not None]
    days_left = min(expiry_days) if expiry_days else None

    have = 0.0
    mismatch = False
    for lot in lots:
        density = line.density_g_per_ml or lot.density_g_per_ml
        try:
            have += convert_quantity(lot.quantity, lot.unit, line.unit, density)
        except UnitError:
            mismatch = True

    if have == 0.0 and mismatch:
        return UNKNOWN_UNIT_RATIO, days_left
    return min(1.0, have / line.quantity), days_left


def score_recipe(recipe: Recipe, index: dict[str, list[PantryItem]]) -> Scored:
    ratios: list[float] = []
    urgency_total = 0.0
    missing: list[str] = []

    for line in recipe.ingredients:
        lots = index.get(normalize_name(line.ingredient_name), [])
        ratio, days_left = _match_line(line, lots)
        ratios.append(ratio)
        if days_left is not None:
            urgency_total += ratio * urgency(days_left)
        if ratio < 1:
            missing.append(line.ingredient_name)

    count = len(ratios)
    coverage = sum(ratios) / count
    score = COVERAGE_WEIGHT * coverage + URGENCY_WEIGHT * (urgency_total / count)
    return Scored(recipe=recipe, score=round(score, 4), coverage=round(coverage, 4), missing=missing)


def rank_recipes(request: MatchRequest, recipes: list[Recipe]) -> list[MatchResult]:
    """Rank `recipes` for the pantry in `request`, best first."""
    index = build_pantry_index(request.pantry)
    excluded = {normalize_name(name) for name in request.excluded_ingredients}

    scored: list[Scored] = []
    for recipe in recipes:
        if any(normalize_name(line.ingredient_name) in excluded for line in recipe.ingredients):
            continue
        result = score_recipe(recipe, index)
        if result.coverage < request.min_coverage:
            continue
        scored.append(result)

    scored.sort(key=lambda s: (-s.score, -s.coverage, s.recipe.name.lower()))
    return [
        MatchResult(recipe_id=s.recipe.id, name=s.recipe.name, score=s.score, missing=s.missing)
        for s in scored[: request.limit]
    ]
