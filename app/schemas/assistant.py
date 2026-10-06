"""Typed assistant request and decision contracts."""
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.ai.intents import RequestedAction

AssistantAction = Literal[
    "menu.category.list", "menu.category.create", "menu.category.update", "menu.category.delete",
    "menu.item.list", "menu.item.create", "menu.item.update", "menu.item.availability", "menu.item.schedule", "menu.item.delete",
    "ingredient.create", "recipe.create", "inventory.command",
    "assistant.clarify", "assistant.confirm", "assistant.cancel", "assistant.help", "assistant.other",
]

class RecentMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(max_length=300)


class AssistantTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=1000)
    recent_messages: list[RecentMessage] = Field(default_factory=list, max_length=6)
    module: str = Field(max_length=40)
    page: str = Field(max_length=80)
    restaurant_name: str | None = Field(default=None, max_length=255)
    user_role: str = Field(max_length=40)
    known: dict = Field(default_factory=dict)
    available_actions: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("known")
    @classmethod
    def bound_known_context(cls, value: dict) -> dict:
        if len(json.dumps(value, ensure_ascii=False)) > 4000:
            raise ValueError("Known context is too large")
        return value

    @field_validator("available_actions")
    @classmethod
    def bound_action_ids(cls, value: list[str]) -> list[str]:
        if any(len(action) > 80 for action in value):
            raise ValueError("Action ID is too long")
        return value

class AssistantDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: AssistantAction
    switch_task: bool
    requested_action: RequestedAction
    confidence: float = Field(ge=0, le=1)
    secondary_intents: list[str] = Field(default_factory=list, max_length=3)
    requested_module: Literal["menu", "inventory", "recipes", "pos", "orders", "customers", "staff", "settings", "other"]
    name: str | None = Field(default=None, max_length=255)
    target_name: str | None = Field(default=None, max_length=255)
    category_name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    price: float | None = Field(default=None, ge=0, le=99999999)
    is_available: bool | None = None
    schedule_name: str | None = Field(default=None, max_length=255)
    generate_description: bool = False
    usage: str | None = Field(default=None, max_length=255)
    quantity: float | None = Field(default=None, ge=0, le=1e9)
    unit: str | None = Field(default=None, max_length=40)
    cost_per_unit: float | None = Field(default=None, ge=0, le=1e9)
    notes: str | None = Field(default=None, max_length=1000)
    yield_quantity: float | None = Field(default=None, gt=0, le=1e6)
    recipe_name: str | None = Field(default=None, max_length=120)

