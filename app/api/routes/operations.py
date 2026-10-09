"""Existing ingredient, recipe, inventory, and command contracts."""
from fastapi import APIRouter, Depends, Header
from app.core.security import authorize
from app.ai.provider import complete
from app.ai.prompts import PROMPTS
from app.schemas.operations import (IngredientRequest, IngredientDraft, RecipeRequest, RecipeDraft, InventoryRequest, InventoryIntent, InventoryExplanationRequest, InventoryExplanation, CommandRequest, CommandIntent, MatchRequest, MatchSuggestions)

router = APIRouter()

@router.post("/internal/ai/ingredient/parse", response_model=IngredientDraft, dependencies=[Depends(authorize)])
async def parse_ingredient(request: IngredientRequest, x_request_id: str | None = Header(default=None)):
    system = PROMPTS["ingredient.parse"]
    return await complete("ingredient.parse", system, request.model_dump(), IngredientDraft, x_request_id)


@router.post("/internal/ai/recipe/generate", response_model=RecipeDraft, dependencies=[Depends(authorize)])
async def generate_recipe(request: RecipeRequest, x_request_id: str | None = Header(default=None)):
    system = PROMPTS["recipe.generate"]
    return await complete("recipe.generate", system, request.model_dump(), RecipeDraft, x_request_id)


@router.post("/internal/ai/inventory/interpret", response_model=InventoryIntent, dependencies=[Depends(authorize)])
async def interpret_inventory(request: InventoryRequest, x_request_id: str | None = Header(default=None)):
    system = PROMPTS["inventory.interpret"]
    return await complete("inventory.interpret", system, request.model_dump(), InventoryIntent, x_request_id)


@router.post("/internal/ai/inventory/explain", response_model=InventoryExplanation, dependencies=[Depends(authorize)])
async def explain_inventory(request: InventoryExplanationRequest, x_request_id: str | None = Header(default=None)):
    system = PROMPTS["inventory.explain"]
    return await complete("inventory.explain", system, request.model_dump(), InventoryExplanation, x_request_id)


@router.post("/internal/ai/command/interpret", response_model=CommandIntent, dependencies=[Depends(authorize)])
async def interpret_command(request: CommandRequest, x_request_id: str | None = Header(default=None)):
    system = PROMPTS["command.interpret"]
    return await complete("command.interpret", system, request.model_dump(), CommandIntent, x_request_id)


@router.post("/internal/ai/ingredient/match", response_model=MatchSuggestions, dependencies=[Depends(authorize)])
async def match_ingredients(request: MatchRequest, x_request_id: str | None = Header(default=None)):
    system = PROMPTS["ingredient.match"]
    return await complete("ingredient.match", system, request.model_dump(), MatchSuggestions, x_request_id)

from app.schemas.operations import RecipeReadRequest, RecipeReadIntent

@router.post('/internal/ai/recipe/interpret', response_model=RecipeReadIntent, dependencies=[Depends(authorize)])
async def interpret_recipe_read(request: RecipeReadRequest, x_request_id: str | None = Header(default=None)):
    # Classification only. No restaurant records or data access are provided to the model.
    system = ('Classify this saved recipe read request as get_recipe, get_ingredients, ingredient_usage '
              '(dishes using an ingredient), get_recipe_cost, list_recipes, or unknown. '
              'Extract only the stated dish or ingredient name into entity. Support Hinglish and typos. '
              'Create, edit, delete, and generated recipe requests are unknown. Never return ingredients, '
              'instructions, quantities, costs, IDs, or SQL. Return exactly {intent, entity}.')
    from fastapi import HTTPException
    for attempt in range(2):
        try:
            return await complete('recipe.interpret', system, request.model_dump(), RecipeReadIntent, x_request_id)
        except HTTPException as error:
            if attempt or error.status_code != 502 or error.detail != 'AI returned an unusable draft':
                raise
