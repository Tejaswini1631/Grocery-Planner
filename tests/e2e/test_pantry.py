import os

import pytest
import requests

# Backend address and a test household. Override with environment variables if needed.
BASE_URL = os.environ.get("PLANNER_API_URL", "http://localhost:5000")#change the port name to the one used in the backend
HOUSEHOLD_ID = os.environ.get("PLANNER_TEST_HOUSEHOLD", "1")#change the household id to the one used in the backend


@pytest.mark.xfail(reason="backend endpoint not merged yet", strict=False)
def test_add_pantry_item_returns_201():
    payload = {"name": "spinach", "quantity": 250, "unit": "g", "expires_on": "2026-11-21"}
    response = requests.post(
        f"{BASE_URL}/households/{HOUSEHOLD_ID}/pantry", json=payload, timeout=5
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "spinach"
    assert body["expires_on"] == "2026-11-21"
    assert "days_left" in body


@pytest.mark.xfail(reason="backend endpoint not merged yet", strict=False)
def test_missing_field_returns_400():
    payload = {"name": "spinach"}  # quantity, unit, and expires_on are missing
    response = requests.post(
        f"{BASE_URL}/households/{HOUSEHOLD_ID}/pantry", json=payload, timeout=5
    )
    assert response.status_code == 400