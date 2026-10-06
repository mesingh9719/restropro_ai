"""Typed LangGraph for menu intent extraction."""
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from app.ai.provider import complete
from app.ai.prompts import PROMPTS
from app.modules.menu.schemas import MenuRequest, MenuIntent

class MenuState(TypedDict, total=False):
    request: MenuRequest
    request_id: str | None
    parsed: MenuIntent
    context: dict
    result: MenuIntent
    route: str

def contextualize(state: MenuState) -> dict:
    known = state["request"].known
    safe = {}
    if isinstance(known, dict):
        for field in ("intent", "pendingField", "recentEntity"):
            value = known.get(field)
            if field == "recentEntity" and isinstance(value, dict):
                safe[field] = {key: value.get(key) for key in ("type", "name") if isinstance(value.get(key), str)}
            elif isinstance(value, str):
                safe[field] = value[:255]
    return {"context": safe}


async def classify(state: MenuState) -> dict:
    system = PROMPTS["menu.interpret"]
    parsed = await complete("menu.interpret", system, {"message": state["request"].message, "known": state["context"]}, MenuIntent, state.get("request_id"))
    return {"parsed": parsed}


def validate(state: MenuState) -> dict:
    parsed = state["parsed"]
    if parsed.intent == "menu.item.create" and parsed.name and parsed.name.casefold().strip() in {"menu", "menu item", "new item", "new menu item"}:
        return {"parsed": parsed.model_copy(update={"name": None})}
    return {}

def route_intent(state: MenuState) -> str:
    intent = state["parsed"].intent
    if intent == "menu.unsupported":
        return "unsupported"
    if intent.endswith(".list"):
        return "read"
    return "write"

def finish(state: MenuState) -> dict:
    return {"result": state["parsed"]}

builder = StateGraph(MenuState)
builder.add_node("contextualize", contextualize)
builder.add_node("classify", classify)
builder.add_node("validate", validate)
for branch in ("read", "write", "unsupported"):
    builder.add_node(branch, finish)
builder.add_edge(START, "contextualize")
builder.add_edge("contextualize", "classify")
builder.add_edge("classify", "validate")
builder.add_conditional_edges("validate", route_intent, {name: name for name in ("read", "write", "unsupported")})
for branch in ("read", "write", "unsupported"):
    builder.add_edge(branch, END)
menu_graph = builder.compile()

async def run_menu_graph(request: MenuRequest, request_id: str | None) -> MenuIntent:
    state = await menu_graph.ainvoke({"request": request, "request_id": request_id})
    return state["result"]
