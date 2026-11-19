"""FastAPI app for the algorithms service.

Called only by the Node backend. All errors are JSON: {"error": "message"}
(see "Global rules" in CONTRACTS.md).
"""
import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .nutrition import summarize
from .recipe_source import RecipeSource, get_recipe_source
from .schemas import (
    ConvertRequest,
    ConvertResponse,
    MatchRequest,
    MatchResult,
    NutritionRequest,
    NutritionResponse,
)
from .scoring import rank_recipes
from .units import UnitError, convert_quantity, normalize_unit

logger = logging.getLogger("algorithms")

app = FastAPI(title="Meal Planner Algorithms Service", version="0.2.0")


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0]
    field = ".".join(str(part) for part in first["loc"] if part != "body")
    message = f"{field}: {first['msg']}" if field else first["msg"]
    return JSONResponse(status_code=400, content={"error": message})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/match", response_model=list[MatchResult])
def match(
    request: MatchRequest, source: RecipeSource | None = Depends(get_recipe_source)
) -> list[MatchResult]:
    """Rank recipes by pantry coverage, favouring ingredients that expire soon."""
    recipes = request.recipes
    if recipes is None:
        if source is None:
            raise HTTPException(
                status_code=503, detail="No recipe source configured (set DATABASE_URL)"
            )
        try:
            recipes = source.load()
        except Exception as exc:  # database down, bad credentials, missing table...
            logger.exception("Could not load recipes")
            raise HTTPException(status_code=503, detail="Could not load recipes") from exc
    return rank_recipes(request, recipes)


@app.post("/convert", response_model=ConvertResponse)
def convert(request: ConvertRequest) -> ConvertResponse:
    """Convert a quantity between units (mass <-> volume needs a density)."""
    try:
        value = convert_quantity(
            request.quantity, request.from_unit, request.to_unit, request.density_g_per_ml
        )
        unit = normalize_unit(request.to_unit)
    except UnitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ConvertResponse(quantity=round(value, 4), unit=unit)


@app.post("/nutrition", response_model=NutritionResponse)
def nutrition(request: NutritionRequest) -> NutritionResponse:
    """Calories and macros per meal, per day and in total."""
    try:
        return summarize(request)
    except UnitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
