# Meal & Grocery Planner

A household app that tracks pantry items and expiry dates, suggests recipes that use expiring ingredients first, and builds a consolidated shopping list.

## Stack

- **Frontend:** React (`frontend/`)
- **Backend:** Node.js (`backend/`)
- **Algorithms:** Python (`algorithms/`), recipe matching, unit conversion, nutrition totals
- **Database:** PostgreSQL 16 (`database/`)
- **Tests:** end-to-end tests in `tests/e2e/`

## Repository layout

```
frontend/       React app
backend/        Node.js API
algorithms/     Python matching service
database/       Schema and seed files (run automatically on first database start)
tests/e2e/      End-to-end tests
CONTRACTS.md    Shared API and database contracts. Read before changing any boundary.
docker-compose.yml
```

## Getting started

Requirements: Git, Docker Desktop, and Node.js (for the frontend and backend).

1. Clone the repo and open a terminal in the repo root.
2. Make sure Docker Desktop is running.
3. Start the stack:
   ```
   docker compose up -d
   docker compose ps
   ```
   The `db` service should show as `healthy`.
4. Stop the stack when you're done:
   ```
   docker compose down
   ```
   To reset the database and reload the seed files, run `docker compose down -v`, then `docker compose up -d`.

## Working on the project

- Create a branch from an up-to-date `main`, for example `feature/backend`.
- Keep your changes inside your own folder.
- If you change a request or response shape, or a database table or column, update `CONTRACTS.md` in the same pull request.
- Open a pull request into `main`. It needs one approval before merging.

## Contracts

All boundaries between the frontend, backend, algorithms service, and database are defined in [CONTRACTS.md](CONTRACTS.md). Those are the source of truth. If the code and the contracts disagree, fix whichever one is wrong in the same pull request.

## Running tests

End-to-end tests live in `tests/e2e/`. With the stack running, run them from the repo root once the test setup is in place. Some tests are expected to fail until the matching feature is merged.

## Known gaps

Track unfinished work here as features merge. Update this section in the same pull request that closes or opens a gap.

- Recipe matching not yet connected to the backend
- Shopping list sync not yet built