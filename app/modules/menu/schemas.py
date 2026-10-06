"""Typed menu interpretation and description contracts."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

MenuAction = Literal[
    "menu.category.list", "menu.category.create", "menu.category.update", "menu.category.delete",
    "menu.item.list", "menu.item.create", "menu.item.update", "menu.item.availability",
    "menu.item.schedule", "menu.item.delete", "menu.unsupported",
]

class MenuRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=1000)
    known: dict = Field(default_factory=dict)

    @field_validator("known")
    @classmethod
    def bound_known_context(cls, value: dict) -> dict:
        if len(str(value)) > 4000:
            raise ValueError("Known context is too large")
        return value

class MenuIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: MenuAction
    target_name: str | None = Field(default=None, max_length=255)
    name: str | None = Field(default=None, max_length=255)
    category_name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    price: float | None = Field(default=None, ge=0, le=99999999)
    is_available: bool | None = None
    schedule_name: str | None = Field(default=None, max_length=255)
    generate_description: bool = False


class MenuDescriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=255)
    dietary_type: str | None = Field(default=None, max_length=40)
    ingredient_names: list[str] = Field(default_factory=list, max_length=30)
    current_description: str | None = Field(default=None, max_length=500)


class MenuDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=12, max_length=500)




class MenuDietaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ingredient_names: list[str] = Field(min_length=1, max_length=30)
    complete_recipe: bool = False

class MenuDietarySuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dietary_type: Literal['veg', 'non-veg', 'egg', 'vegan'] | None = None
    confidence: float = Field(ge=0, le=1)
