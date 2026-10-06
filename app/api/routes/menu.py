"""Private menu interpretation and description drafting routes."""
from fastapi import APIRouter, Depends, Header
from app.core.security import authorize
from app.ai.provider import complete
from app.ai.prompts import PROMPTS
from app.modules.menu.graph import run_menu_graph
from app.modules.menu.schemas import MenuRequest, MenuIntent, MenuDescriptionRequest, MenuDescription, MenuDietaryRequest, MenuDietarySuggestion

router = APIRouter()

@router.post("/internal/ai/menu/interpret", response_model=MenuIntent, dependencies=[Depends(authorize)])
async def interpret_menu(request: MenuRequest, x_request_id: str | None = Header(default=None)):
    return await run_menu_graph(request, x_request_id)



@router.post("/internal/ai/menu/description", response_model=MenuDescription, dependencies=[Depends(authorize)])
async def draft_menu_description(request: MenuDescriptionRequest, x_request_id: str | None = Header(default=None)):
    system = PROMPTS["menu.description"]
    return await complete("menu.description", system, request.model_dump(exclude={'current_description'} if request.current_description is None else set()), MenuDescription, x_request_id)



@router.post("/internal/ai/menu/dietary", response_model=MenuDietarySuggestion, dependencies=[Depends(authorize)])
async def suggest_dietary_profile(request: MenuDietaryRequest, x_request_id: str | None = Header(default=None)):
    if not request.complete_recipe:
        return MenuDietarySuggestion(dietary_type=None, confidence=0)
    return await complete("menu.dietary", PROMPTS["menu.dietary"], request.model_dump(), MenuDietarySuggestion, x_request_id)
