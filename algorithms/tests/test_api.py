import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.recipe_source import get_recipe_source
from app.schemas import Recipe, RecipeIngredient

client = TestClient(app)

PANTRY = [
    {"name": "spinach", "quantity": 200, "unit": "g", "days_left": 1},
    {"name": "rice", "quantity": 500, "unit": "g", "days_left": 194},
]

RECIPES = [
    Recipe(
        id=2,
        name="Plain rice",
        ingredients=[RecipeIngredient(ingredient_name="rice", quantity=100, unit="g")],
    ),
    Recipe(
        id=1,
        name="Spinach saute",
        ingredients=[RecipeIngredient(ingredient_name="spinach", quantity=100, unit="g")],
    ),
]


class FakeSource:
    def __init__(self, recipes):
        self.recipes = recipes

    def load(self):
        return self.recipes


class BrokenSource:
    def load(self):
        raise RuntimeError("database is down")


@pytest.fixture(autouse=True)
def reset_overrides():
    yield
    app.dependency_overrides.clear()


def use_source(source):
    app.dependency_overrides[get_recipe_source] = lambda: source


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------- /match ----

def test_match_with_pantry_only_loads_recipes_from_the_source():
    use_source(FakeSource(RECIPES))

    response = client.post("/match", json={"pantry": PANTRY})

    assert response.status_code == 200
    assert response.json() == [
        {"recipe_id": 1, "name": "Spinach saute", "score": 0.85, "missing": []},
        {"recipe_id": 2, "name": "Plain rice", "score": 0.7015, "missing": []},
    ]


def test_match_response_has_exactly_the_contract_fields():
    use_source(FakeSource(RECIPES))

    results = client.post("/match", json={"pantry": PANTRY}).json()

    for item in results:
        assert set(item) == {"recipe_id", "name", "score", "missing"}


def test_match_reports_missing_ingredients():
    use_source(FakeSource(RECIPES))

    results = client.post("/match", json={"pantry": []}).json()

    assert all(r["score"] == 0 for r in results)
    assert {r["name"]: r["missing"] for r in results} == {
        "Plain rice": ["rice"],
        "Spinach saute": ["spinach"],
    }


def test_match_uses_recipes_sent_in_the_request_without_touching_the_source():
    use_source(BrokenSource())
    payload = {
        "pantry": PANTRY,
        "recipes": [
            {
                "id": 1,
                "name": "Spinach saute",
                "ingredients": [{"ingredient_name": "spinach", "quantity": 100, "unit": "g"}],
            }
        ],
    }

    response = client.post("/match", json=payload)

    assert response.status_code == 200
    assert [r["recipe_id"] for r in response.json()] == [1]


def test_match_without_a_recipe_source_returns_503():
    use_source(None)

    response = client.post("/match", json={"pantry": PANTRY})

    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["error"]


def test_match_returns_503_when_loading_recipes_fails():
    use_source(BrokenSource())

    response = client.post("/match", json={"pantry": PANTRY})

    assert response.status_code == 503
    assert response.json() == {"error": "Could not load recipes"}


# ---------------------------------------------------------- error format ----

def test_missing_required_field_is_400_with_error_message():
    response = client.post("/match", json={})

    assert response.status_code == 400
    assert "pantry" in response.json()["error"]


def test_invalid_value_is_400_with_error_message():
    bad = {"pantry": [{"name": "rice", "quantity": -1, "unit": "g"}]}

    response = client.post("/match", json=bad)

    assert response.status_code == 400
    assert set(response.json()) == {"error"}


def test_unknown_route_uses_the_same_error_shape():
    response = client.get("/nope")

    assert response.status_code == 404
    assert set(response.json()) == {"error"}


# -------------------------------------------------------------- /convert ----

def test_convert():
    response = client.post("/convert", json={"quantity": 1, "from_unit": "cup", "to_unit": "ml"})

    assert response.status_code == 200
    assert response.json() == {"quantity": 240.0, "unit": "ml"}


def test_convert_with_density():
    body = {"quantity": 1, "from_unit": "cup", "to_unit": "g", "density_g_per_ml": 0.53}

    assert client.post("/convert", json=body).json() == {"quantity": 127.2, "unit": "g"}


def test_convert_incompatible_units_is_400():
    response = client.post("/convert", json={"quantity": 1, "from_unit": "g", "to_unit": "ml"})

    assert response.status_code == 400
    assert "density" in response.json()["error"]


# ------------------------------------------------------------ /nutrition ----

def test_nutrition():
    body = {
        "entries": [
            {
                "day": "2026-11-20",
                "slot": "dinner",
                "servings": 1,
                "recipe": {
                    "servings": 2,
                    "ingredients": [
                        {
                            "quantity": 200,
                            "unit": "g",
                            "base_unit": "g",
                            "nutrition_per_100": {
                                "calories": 130,
                                "protein_g": 2.7,
                                "carbs_g": 28,
                                "fat_g": 0.3,
                            },
                        }
                    ],
                },
            }
        ]
    }

    response = client.post("/nutrition", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == {"calories": 130.0, "protein_g": 2.7, "carbs_g": 28.0, "fat_g": 0.3}
    assert data["by_day"][0]["day"] == "2026-11-20"


def test_nutrition_unit_error_is_400():
    body = {
        "entries": [
            {
                "recipe": {
                    "ingredients": [
                        {
                            "quantity": 100,
                            "unit": "g",
                            "base_unit": "ml",
                            "nutrition_per_100": {"calories": 884},
                        }
                    ]
                }
            }
        ]
    }

    response = client.post("/nutrition", json=body)

    assert response.status_code == 400
    assert "error" in response.json()
