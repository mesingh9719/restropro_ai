"""Existing strict request and response contracts for drafting endpoints."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class IngredientRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=3, max_length=500)
    answers: str = Field(default='', max_length=500)
    corrections: list[dict] = Field(default_factory=list, max_length=20)
    categories: list[str] = Field(max_length=100)
    units: list[str] = Field(max_length=20)


class IngredientDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    unit: str | None = Field(default=None, max_length=40)
    quantity: float | None = Field(default=None, ge=0, le=1e9)
    cost_per_unit: float | None = Field(default=None, ge=0, le=1e9)
    description: str | None = Field(default=None, max_length=1000)


class AssistantExtractRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=1000)
    module: str = Field(max_length=40)
    known: dict = Field(default_factory=dict)
    categories: list[str] = Field(default_factory=list, max_length=100)
    units: list[str] = Field(default_factory=list, max_length=20)


class AssistantFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal["ingredient", "recipe", "inventory_question", "other"]
    name: str | None = Field(default=None, max_length=255)
    usage: str | None = Field(default=None, max_length=255)
    recipe_name: str | None = Field(default=None, max_length=120)
    quantity: float | None = Field(default=None, ge=0, le=1e9)
    unit: str | None = Field(default=None, max_length=40)
    cost_per_unit: float | None = Field(default=None, ge=0, le=1e9)
    category: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=1000)
    yield_quantity: float | None = Field(default=None, gt=0, le=1e6)


class AssistantReplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=1000)
    module: str = Field(max_length=40)
    hint: str = Field(max_length=500)
    available_actions: list[str] = Field(max_length=20)


class AssistantReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reply: str = Field(min_length=1, max_length=700)


class InventoryContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=255)
    unit: str = Field(max_length=40)
    current_stock: float
    minimum: float
    reorder_level: float
    target: float
    cost_per_unit: float


class InventoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=500)
    ingredient_names: list[str] = Field(max_length=100)


class InventoryIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal["low", "out", "reorder", "stock", "highest_value", "unknown"]
    ingredient_name: str | None = Field(default=None, max_length=255)


class InventoryExplanationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=3, max_length=500)
    intent: Literal["low", "out", "reorder", "stock", "highest_value", "unknown"]
    items: list[InventoryContext] = Field(max_length=100)


class InventoryExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    explanation: str = Field(min_length=1, max_length=500)


class RecipeIngredient(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ingredient_name: str = Field(min_length=1, max_length=255)
    quantity: float = Field(gt=0, le=1e9)
    unit: str = Field(min_length=1, max_length=40)


class RecipeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipe_name: str = Field(min_length=1, max_length=120)
    yield_quantity: float = Field(gt=0, le=1e6)
    yield_unit: Literal["portion"]
    ingredients: list[RecipeIngredient] = Field(min_length=1, max_length=100)


class RecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=3, max_length=500)
    answers: str = Field(default='', max_length=500)
    corrections: list[dict] = Field(default_factory=list, max_length=20)
    menu_name: str = Field(min_length=1, max_length=120)
    existing_recipe: RecipeDraft | None = None
    available_ingredients: list[str] = Field(max_length=100)


CommandName = Literal[
    "inventory.add_missing_ingredients_for_recipe",
    "recipe.show_required_ingredients",
    "recipe.find_missing_ingredients",
    "recipe.add_ingredient",
    "recipe.remove_ingredient",
    "inventory.low_stock",
    "inventory.reorder",
    "inventory.check_stock",
    "inventory.find_duplicates",
    "inventory.update_reorder_level",
    "inventory.create",
    "recipe.using_ingredient",
    "recipe.affected_by_stockout",
    "unsupported",
]


class CommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=3, max_length=500)


class CommandIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: CommandName
    recipe_name: str | None = Field(default=None, max_length=120)
    ingredient_name: str | None = Field(default=None, max_length=255)
    quantity: float | None = Field(default=None, gt=0, le=1e9)
    unit: str | None = Field(default=None, max_length=40)


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requested_names: list[str] = Field(min_length=1, max_length=30)
    inventory_names: list[str] = Field(min_length=1, max_length=100)


class MatchCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requested_name: str = Field(min_length=1, max_length=255)
    existing_name: str = Field(min_length=1, max_length=255)
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(max_length=160)


class MatchSuggestions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    matches: list[MatchCandidate] = Field(max_length=30)
