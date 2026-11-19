# Meal & Grocery Planner: Contracts

This file defines every boundary between the parts of the system. Change a contract here in the same PR that changes the code. Each owner must approve changes to their own contracts.

## Global rules
- Dates are ISO strings: `YYYY-MM-DD`.
- Quantities are numbers in the stated unit. Python does unit conversion.
- Ingredient names are lowercase and singular (`tomato`, not `Tomatoes`).
- Errors return JSON: `{ "error": "message" }`.

---

## 1. Add a pantry item (React → Node)
- **Owner:** Person 2 (frontend) calls it, Person 3 (backend) implements it
- **Method and path:** `POST /households/{householdId}/pantry`
- **Request:**
  ```json
  { "name": "spinach", "quantity": 250, "unit": "g", "expires_on": "2026-11-21" }
  ```
  `name`, `quantity`, `unit`, and `expires_on` are required.
- **Response (201):**
  ```json
  { "id": 17, "name": "spinach", "quantity": 250, "unit": "g", "expires_on": "2026-11-21", "days_left": 2 }
  ```
- **Errors:**
  - `400` if a required field is missing or `expires_on` is not a valid date
  - `403` if the user is not in the household

## 2. List pantry items (React → Node)
- **Owner:** Person 3 (backend) implements, Person 2 (frontend) calls
- **Method and path:** `GET /households/{householdId}/pantry`
- **Response (200):** an array of item objects in the same shape as contract 1
- **Errors:** `403` if the user is not in the household

## 3. Get recipe matches (React → Node → Python)
- **Owner:** Person 3 (backend) owns the Node endpoint, Person 4 (algorithms) owns the Python endpoint
- **Node endpoint (React calls this):** `GET /households/{householdId}/matches`
  - **Response (200):**
    ```json
    [ { "recipe_id": 3, "name": "palak paneer", "score": 0.82, "missing": ["cream"] } ]
    ```
  - **Errors:** `503` if the Python service is unreachable (Node must not crash)
- **Python endpoint (Node calls this):** `POST /match`
  - **Request:**
    ```json
    { "pantry": [ { "name": "spinach", "quantity": 250, "unit": "g", "days_left": 2 } ] }
    ```
  - **Response (200):** same array shape as the Node endpoint above
  - **Scoring rule:** items with fewer `days_left` weigh more. Score is between 0 and 1.

## 4. Shopping list (React → Node)
- **Owner:** Person 3 (backend) implements, Person 2 (frontend) calls
- **Method and paths:**
  - `GET /households/{householdId}/shopping-list`
  - `POST /households/{householdId}/shopping-list` with `{ "name": "cream" }`
  - `PATCH /households/{householdId}/shopping-list/{itemId}` with `{ "checked": true }`
- **Item shape:** `{ "id": 5, "name": "cream", "checked": false }`
- **Errors:** `403` if the user is not in the household, `404` if the item does not exist

## 5. Database schema (Node → PostgreSQL)
- **Owner:** Person 1 (database)
- **Tables and key columns:**
  - `households (id, name)`
  - `users (id, name, household_id)`
  - `pantry_items (id, household_id, name, quantity, unit, expires_on)`
  - `recipes (id, name)`
  - `recipe_ingredients (recipe_id, ingredient_name, quantity, unit)`
  - `shopping_items (id, household_id, name, checked)`
- **Rule:** Node queries use these exact table and column names. Renaming one is a contract change.

---

## Changelog
- 2026-11-19: initial version, agreed by all owners