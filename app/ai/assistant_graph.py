"""One structured interpretation pass for central assistant messages."""
import re
from typing import TypedDict
from langgraph.graph import START, END, StateGraph
from app.ai.provider import complete
from app.ai.prompts import PROMPTS
from app.ai.intents import permitted
from app.schemas.assistant import AssistantTurn, AssistantDecision

class AssistantState(TypedDict, total=False):
    turn: AssistantTurn
    request_id: str | None
    decision: AssistantDecision
    normalized_message: str

def normalize_request(state: AssistantState) -> dict:
    return {"normalized_message": " ".join(state["turn"].message.casefold().split())}


def detect_control(state: AssistantState) -> dict:
    message = state["normalized_message"]
    known = state["turn"].known
    stage = known.get("stage") if isinstance(known, dict) else None
    intent = None
    action = "unknown"
    if message in {"cancel", "stop", "never mind", "never mind.", "नहीं", "मत करो"} and stage in {"collecting", "review"}:
        intent, action = "assistant.cancel", "cancel"
    elif stage == "review" and message in {"yes", "yes.", "confirm", "do it", "go ahead", "create it", "save it", "हाँ", "haan"}:
        intent, action = "assistant.confirm", "confirmation"
    elif stage == "review" and message in {"no", "no.", "don't do it", "do not do it", "cancel it", "नहीं", "nahin"}:
        intent, action = "assistant.cancel", "rejection"
    elif message in {"help", "help me", "what can you do", "hi", "hello", "namaste"} and not stage:
        intent, action = "assistant.help", "help"
    if not intent:
        return {}
    module = state["turn"].module
    if module not in {"menu", "inventory", "recipes", "pos", "orders", "customers", "staff", "settings"}:
        module = "other"
    return {"decision": AssistantDecision(intent=intent, switch_task=False, requested_action=action,
        confidence=1.0, secondary_intents=[], requested_module=module)}


def detect_explicit_menu_create(state: AssistantState) -> dict:
    """Handle an unambiguous create command without a provider round trip."""
    if state.get("decision"):
        return {}
    message = state["turn"].message.strip()
    match = re.fullmatch(
        r"(?:please\s+)?(?:add|create|make)\s+(?:(?:a|an)\s+)?(?:(?:new)\s+)?"
        r"(?:menu\s+item|menu\s+dish|item|dish)(?:\s+(?:for|named|called))?"
        r"(?:\s+(.+))?",
        message,
        flags=re.IGNORECASE,
    )
    if not match:
        return {}
    name = match.group(1)
    name = name.strip(" .,!?") if name else None
    if name and (len(name) > 255 or re.search(r"\b(?:and|then)\s+(?:add|create|update|delete|change|remove)\b|\b(?:with|for)\s+(?:price|category)\b", name, flags=re.IGNORECASE)):
        return {}
    return {"decision": AssistantDecision(
        intent="menu.item.create", switch_task=True, requested_action="create",
        confidence=1.0, secondary_intents=[], requested_module="menu", name=name or None,
    )}


async def classify(state: AssistantState) -> dict:
    if state.get("decision"):
        return {}

    system = PROMPTS["assistant.route"]
    decision = await complete("assistant.route", system, state["turn"].model_dump(), AssistantDecision, state.get("request_id"))
    return {"decision": decision}

def validate_decision(state: AssistantState) -> dict:
    decision = state["decision"]
    if not permitted(decision.intent, state["turn"].available_actions):
        return {"decision": decision.model_copy(update={"intent": "assistant.other", "requested_action": "unknown", "secondary_intents": []})}
    if decision.secondary_intents and decision.intent != "assistant.clarify":
        return {"decision": decision.model_copy(update={"intent": "assistant.clarify", "requested_action": "clarification"})}
    return {}


def route(state: AssistantState) -> str:
    intent = state["decision"].intent
    if intent.startswith("menu."):
        return "menu"
    if intent in ("ingredient.create", "recipe.create", "inventory.command"):
        return "module"
    return "conversation"

def refine_menu(state: AssistantState) -> dict:
    decision = state["decision"]
    updates = {}
    if decision.intent == "menu.item.create" and decision.name and decision.name.casefold().strip() in {"menu", "menu item", "new item", "new menu item"}:
        updates["name"] = None
    if decision.intent == "menu.item.availability" and decision.schedule_name:
        updates["intent"] = "menu.item.schedule"
    recent = state["turn"].known.get("recentEntity")
    if (isinstance(recent, dict) and recent.get("type") == "item" and isinstance(recent.get("name"), str)
            and decision.intent in ("menu.item.update", "menu.item.availability", "menu.item.schedule")
            and not decision.target_name):
        updates["target_name"] = recent["name"][:255]
    return {"decision": decision.model_copy(update=updates)} if updates else {}


def finish(state: AssistantState) -> dict:
    return {}

builder = StateGraph(AssistantState)
builder.add_node("normalize_request", normalize_request)
builder.add_node("detect_control", detect_control)
builder.add_node("detect_explicit_menu_create", detect_explicit_menu_create)
builder.add_node("classify", classify)
builder.add_node("validate_decision", validate_decision)
builder.add_node("menu", refine_menu)
builder.add_node("revalidate_decision", validate_decision)
for branch in ("module", "conversation"):
    builder.add_node(branch, finish)
builder.add_edge(START, "normalize_request")
builder.add_edge("normalize_request", "detect_control")
builder.add_edge("detect_control", "detect_explicit_menu_create")
builder.add_edge("detect_explicit_menu_create", "classify")
builder.add_edge("classify", "validate_decision")
builder.add_conditional_edges("validate_decision", route, {branch: branch for branch in ("menu", "module", "conversation")})
builder.add_edge("menu", "revalidate_decision")
builder.add_edge("revalidate_decision", END)
for branch in ("module", "conversation"):
    builder.add_edge(branch, END)
assistant_graph = builder.compile()

async def interpret_turn(turn: AssistantTurn, request_id: str | None) -> AssistantDecision:
    state = await assistant_graph.ainvoke({"turn": turn, "request_id": request_id})
    return state["decision"]
