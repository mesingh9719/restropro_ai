"""Capabilities recognized by FastAPI; Node remains the execution authority.

Adding a callable intent also requires registering its permission and handler in Node.
Unimplemented application actions are represented as assistant.other, never executable IDs.
"""
from dataclasses import dataclass
from typing import Literal

RequestedAction = Literal[
    "create", "read", "update", "delete", "list", "search", "duplicate",
    "archive", "restore", "greeting", "help", "clarification", "confirmation",
    "rejection", "cancel", "undo", "follow_up", "unknown",
]


@dataclass(frozen=True)
class IntentSpec:
    module: str
    operation: str
    mutates: bool = False


INTENTS: dict[str, IntentSpec] = {
    "menu.category.list": IntentSpec("menu", "list"),
    "menu.category.create": IntentSpec("menu", "create", True),
    "menu.category.update": IntentSpec("menu", "update", True),
    "menu.category.delete": IntentSpec("menu", "delete", True),
    "menu.item.list": IntentSpec("menu", "list"),
    "menu.item.create": IntentSpec("menu", "create", True),
    "menu.item.update": IntentSpec("menu", "update", True),
    "menu.item.availability": IntentSpec("menu", "update", True),
    "menu.item.schedule": IntentSpec("menu", "update", True),
    "menu.item.delete": IntentSpec("menu", "delete", True),
    "ingredient.create": IntentSpec("inventory", "create", True),
    "recipe.create": IntentSpec("recipes", "create", True),
    "inventory.command": IntentSpec("inventory", "follow_up"),
    "assistant.clarify": IntentSpec("other", "clarification"),
    "assistant.confirm": IntentSpec("other", "confirmation"),
    "assistant.cancel": IntentSpec("other", "cancel"),
    "assistant.help": IntentSpec("other", "help"),
    "assistant.other": IntentSpec("other", "unknown"),
}

CONTROL_INTENTS = frozenset(intent for intent in INTENTS if intent.startswith("assistant."))


def permitted(intent: str, available_actions: list[str]) -> bool:
    return intent in CONTROL_INTENTS or (intent in INTENTS and intent in available_actions)


def requires_confirmation(intent: str) -> bool:
    return INTENTS.get(intent, IntentSpec("other", "unknown")).mutates
