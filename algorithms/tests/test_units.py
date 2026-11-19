import pytest

from app.units import UnitError, convert_quantity, normalize_unit, to_base, unit_family


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("g", "g"),
        ("Grams", "g"),
        ("  KG ", "kg"),
        ("tablespoons", "tbsp"),
        ("fl oz", "fl_oz"),
        ("Cloves", "count"),
        ("pcs", "count"),
        ("Litres", "l"),
    ],
)
def test_normalize_unit(raw, expected):
    assert normalize_unit(raw) == expected


def test_normalize_unknown_unit_raises():
    with pytest.raises(UnitError):
        normalize_unit("bunch")


def test_unit_family_and_to_base():
    assert unit_family("kg") == "mass"
    assert unit_family("cup") == "volume"
    assert unit_family("pcs") == "count"
    assert to_base(2, "kg") == (2000.0, "g")
    assert to_base(1, "cup") == (240.0, "ml")
    assert to_base(3, "cloves") == (3.0, "count")


@pytest.mark.parametrize(
    "quantity, from_unit, to_unit, expected",
    [
        (1, "kg", "g", 1000),
        (500, "g", "kg", 0.5),
        (1, "cup", "ml", 240),
        (2, "tbsp", "tsp", 6),
        (1, "l", "tbsp", 1000 / 15),
        (2, "cloves", "pcs", 2),
        (1, "lb", "g", 453.592),
        (8, "oz", "lb", 8 * 28.3495 / 453.592),
        (5, "g", "g", 5),
    ],
)
def test_same_family_conversion(quantity, from_unit, to_unit, expected):
    assert convert_quantity(quantity, from_unit, to_unit) == pytest.approx(expected)


def test_volume_to_mass_uses_density():
    # 1 cup of flour at 0.53 g/ml
    assert convert_quantity(1, "cup", "g", density_g_per_ml=0.53) == pytest.approx(127.2)


def test_mass_to_volume_uses_density():
    assert convert_quantity(100, "g", "ml", density_g_per_ml=0.5) == pytest.approx(200)


def test_mass_to_volume_without_density_raises():
    with pytest.raises(UnitError):
        convert_quantity(100, "g", "ml")


@pytest.mark.parametrize("density", [0, -1.0])
def test_invalid_density_raises(density):
    with pytest.raises(UnitError):
        convert_quantity(100, "g", "ml", density_g_per_ml=density)


def test_count_cannot_convert_to_mass():
    with pytest.raises(UnitError):
        convert_quantity(2, "pcs", "g", density_g_per_ml=1.0)


def test_negative_quantity_raises():
    with pytest.raises(UnitError):
        convert_quantity(-1, "g", "kg")


def test_zero_quantity_is_fine():
    assert convert_quantity(0, "kg", "g") == 0
