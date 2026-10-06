"""Private assistant interpretation and response routes."""
from fastapi import APIRouter, Depends, Header
from app.core.security import authorize
from app.ai.provider import complete
from app.ai.prompts import PROMPTS
from app.ai.assistant_graph import AssistantTurn, AssistantDecision, interpret_turn
from app.schemas.operations import AssistantReplyRequest, AssistantReply, AssistantExtractRequest, AssistantFacts

router = APIRouter()

@router.post("/internal/ai/assistant/respond", response_model=AssistantReply, dependencies=[Depends(authorize)])
async def respond_assistant(request: AssistantReplyRequest, x_request_id: str | None = Header(default=None)):
    system = PROMPTS["assistant.respond"]
    return await complete("assistant.respond", system, request.model_dump(), AssistantReply, x_request_id)


@router.post("/internal/ai/assistant/extract", response_model=AssistantFacts, dependencies=[Depends(authorize)])
async def extract_assistant_facts(request: AssistantExtractRequest, x_request_id: str | None = Header(default=None)):
    system = PROMPTS["assistant.extract"]
    return await complete("assistant.extract", system, request.model_dump(), AssistantFacts, x_request_id)


@router.post("/internal/ai/assistant/route", response_model=AssistantDecision, dependencies=[Depends(authorize)])
async def route_assistant(request: AssistantTurn, x_request_id: str | None = Header(default=None)):
    return await interpret_turn(request, x_request_id)
