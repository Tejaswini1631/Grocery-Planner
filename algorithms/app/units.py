"""Unit conversion.

Every unit belongs to one family, and each family has a base unit:

    mass   -> grams (g)
    volume -> millilitres (ml)
    count  -> pieces (count)

Mass <-> volume conversion needs a density in g per ml and raises UnitError
without one. Everything else across families is not convertible.
"""
from __future__ import annotations

MASS_FACTORS: dict[str, float] = {
    "mg": 0.001,
    "g": 1.0,
    "kg": 1000.0,
    "oz": 28.3495,
    "lb": 453.592,
}

VOLUME_FACTORS: dict[str, float] = {
    "ml": 1.0,
    "l": 1000.0,
    "tsp": 5.0,
    "tbsp": 15.0,
    "cup": 240.0,
    "fl_oz": 29.5735,
}

COUNT_UNITS: set[str] = {"count", "pc", "pcs", "piece", "pieces", "clove", "cloves", "unit", "units"}

ALIASES: dict[str, str] = {
    "gram": "g",
    "grams": "g",
    "milligram": "mg",
    "milligrams": "mg",
    "kilogram": "kg",
    "kilograms": "kg",
    "ounce": "oz",
    "ounces": "oz",
    "pound": "lb",
    "pounds": "lb",
    "lbs": "lb",
    "millilitre": "ml",
    "millilitres": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
    "litre": "l",
    "litres": "l",
    "liter": "l",
    "liters": "l",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "cups": "cup",
    "floz": "fl_oz",
}

BASE_UNITS: dict[str, str] = {"mass": "g", "volume": "ml", "count": "count"}


class UnitError(ValueError):
    """Raised when a unit is unknown or two units cannot be converted."""


def normalize_unit(unit: str) -> str:
    """Return the canonical spelling of a unit (e.g. 'Tablespoons' -> 'tbsp')."""
    cleaned = unit.strip().lower().rstrip(".").replace(" ", "_")
    cleaned = ALIASES.get(cleaned, cleaned)
    if cleaned in MASS_FACTORS or cleaned in VOLUME_FACTORS:
        return cleaned
    if cleaned in COUNT_UNITS:
        return "count"
    raise UnitError(f"Unknown unit: {unit!r}")


def _factor(unit: str) -> tuple[str, float]:
    """Return (family, factor to the family's base unit)."""
    canonical = normalize_unit(unit)
    if canonical in MASS_FACTORS:
        return "mass", MASS_FACTORS[canonical]
    if canonical in VOLUME_FACTORS:
        return "volume", VOLUME_FACTORS[canonical]
    return "count", 1.0


def unit_family(unit: str) -> str:
    """Return 'mass', 'volume' or 'count'."""
    return _factor(unit)[0]


def to_base(quantity: float, unit: str) -> tuple[float, str]:
    """Convert a quantity to its family's base unit: returns (value, base_unit)."""
    family, factor = _factor(unit)
    return quantity * factor, BASE_UNITS[family]


def convert_quantity(
    quantity: float,
    from_unit: str,
    to_unit: str,
    density_g_per_ml: float | None = None,
) -> float:
    """Convert `quantity` from one unit to another.

    Units in the same family convert directly. Mass <-> volume needs
    `density_g_per_ml`. Anything else raises UnitError.
    """
    if quantity < 0:
        raise UnitError("Quantity cannot be negative")

    from_family, from_factor = _factor(from_unit)
    to_family, to_factor = _factor(to_unit)
    base = quantity * from_factor

    if from_family == to_family:
        return base / to_factor

    if {from_family, to_family} == {"mass", "volume"}:
        if density_g_per_ml is None or density_g_per_ml <= 0:
            raise UnitError(
                f"Converting {from_unit!r} to {to_unit!r} needs a density (g per ml)"
            )
        # base is in g (from mass) or ml (from volume)
        base = base * density_g_per_ml if from_family == "volume" else base / density_g_per_ml
        return base / to_factor

    raise UnitError(f"Cannot convert {from_unit!r} to {to_unit!r}")
