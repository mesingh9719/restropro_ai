"""Provider-compatible strict JSON schemas for typed AI results."""

OUTPUT_SCHEMAS = {
    "AssistantDecision": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "intent": {"type": "string", "enum": [
                "menu.category.list", "menu.category.create", "menu.category.update", "menu.category.delete",
                "menu.item.list", "menu.item.create", "menu.item.update", "menu.item.availability", "menu.item.schedule", "menu.item.delete",
                "ingredient.create", "recipe.create", "inventory.command",
                "assistant.clarify", "assistant.confirm", "assistant.cancel", "assistant.help", "assistant.other"]},
            "switch_task": {"type": "boolean"},
            "requested_action": {"type": "string", "enum": ["create", "read", "update", "delete", "list", "search", "duplicate", "archive", "restore", "greeting", "help", "clarification", "confirmation", "rejection", "cancel", "undo", "follow_up", "unknown"]},
            "confidence": {"type": "number"},
            "secondary_intents": {"type": "array", "items": {"type": "string"}},
            "requested_module": {"type": "string", "enum": ["menu", "inventory", "recipes", "pos", "orders", "customers", "staff", "settings", "other"]},
            "name": {"type": ["string", "null"]},
            "target_name": {"type": ["string", "null"]},
            "category_name": {"type": ["string", "null"]},
            "description": {"type": ["string", "null"]},
            "price": {"type": ["number", "null"]},
            "is_available": {"type": ["boolean", "null"]},
            "schedule_name": {"type": ["string", "null"]},
            "generate_description": {"type": "boolean"},
            "usage": {"type": ["string", "null"]},
            "quantity": {"type": ["number", "null"]},
            "unit": {"type": ["string", "null"]},
            "cost_per_unit": {"type": ["number", "null"]},
            "notes": {"type": ["string", "null"]},
            "yield_quantity": {"type": ["number", "null"]},
            "recipe_name": {"type": ["string", "null"]},
        },
        "required": ["intent", "switch_task", "requested_action", "confidence", "secondary_intents", "requested_module", "name", "target_name", "category_name", "description", "price", "is_available", "schedule_name", "generate_description", "usage", "quantity", "unit", "cost_per_unit", "notes", "yield_quantity", "recipe_name"],
    },
    "MenuIntent": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "intent": {"type": "string", "enum": [
                "menu.category.list", "menu.category.create", "menu.category.update", "menu.category.delete",
                "menu.item.list", "menu.item.create", "menu.item.update", "menu.item.availability",
                "menu.item.schedule", "menu.item.delete", "menu.unsupported"]},
            "target_name": {"type": ["string", "null"]},
            "name": {"type": ["string", "null"]},
            "category_name": {"type": ["string", "null"]},
            "description": {"type": ["string", "null"]},
            "price": {"type": ["number", "null"]},
            "is_available": {"type": ["boolean", "null"]},
            "schedule_name": {"type": ["string", "null"]},
            "generate_description": {"type": "boolean"},
        },
        "required": ["intent", "target_name", "name", "category_name", "description", "price", "is_available", "schedule_name", "generate_description"],
    },
    "CommandIntent": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "intent": {"type": "string", "enum": [
                "inventory.add_missing_ingredients_for_recipe", "recipe.show_required_ingredients",
                "recipe.find_missing_ingredients", "recipe.add_ingredient", "recipe.remove_ingredient",
                "inventory.low_stock", "inventory.reorder", "inventory.check_stock",
                "inventory.find_duplicates", "inventory.update_reorder_level", "inventory.create",
                "recipe.using_ingredient", "recipe.affected_by_stockout", "unsupported"]},
            "recipe_name": {"type": ["string", "null"]},
            "ingredient_name": {"type": ["string", "null"]},
            "quantity": {"type": ["number", "null"]},
            "unit": {"type": ["string", "null"]},
        },
        "required": ["intent", "recipe_name", "ingredient_name", "quantity", "unit"],
    },
    "MatchSuggestions": {
        "type": "object", "additionalProperties": False,
        "properties": {"matches": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "requested_name": {"type": "string"}, "existing_name": {"type": "string"},
                "confidence": {"type": "number"}, "reason": {"type": "string"},
            },
            "required": ["requested_name", "existing_name", "confidence", "reason"],
        }}},
        "required": ["matches"],
    },
    "AssistantReply": {
        "type": "object", "additionalProperties": False,
        "properties": {"reply": {"type": "string"}},
        "required": ["reply"],
    },
    "AssistantFacts": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "intent": {"type": "string", "enum": ["ingredient", "recipe", "inventory_question", "other"]},
            "name": {"type": ["string", "null"]},
            "usage": {"type": ["string", "null"]},
            "recipe_name": {"type": ["string", "null"]},
            "quantity": {"type": ["number", "null"]},
            "unit": {"type": ["string", "null"]},
            "cost_per_unit": {"type": ["number", "null"]},
            "category": {"type": ["string", "null"]},
            "notes": {"type": ["string", "null"]},
            "yield_quantity": {"type": ["number", "null"]},
        },
        "required": ["intent", "name", "usage", "recipe_name", "quantity", "unit", "cost_per_unit", "category", "notes", "yield_quantity"],
    },
    "MenuDietarySuggestion": {
        "type": "object", "additionalProperties": False,
        "properties": {"dietary_type": {"type": ["string", "null"], "enum": ["veg", "non-veg", "egg", "vegan", None]}, "confidence": {"type": "number"}},
        "required": ["dietary_type", "confidence"],
    },
    "MenuDescription": {
        "type": "object", "additionalProperties": False,
        "properties": {"description": {"type": "string"}},
        "required": ["description"],
    },
    "IngredientDraft": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "name": {"type": "string"},
            "category": {"type": ["string", "null"]},
            "unit": {"type": ["string", "null"]},
            "quantity": {"type": ["number", "null"]},
            "cost_per_unit": {"type": ["number", "null"]},
            "description": {"type": ["string", "null"]},
        },
        "required": ["name", "category", "unit", "quantity", "cost_per_unit", "description"],
    },
    "RecipeDraft": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "recipe_name": {"type": "string"},
            "yield_quantity": {"type": "number"},
            "yield_unit": {"type": "string", "enum": ["portion"]},
            "ingredients": {"type": "array", "items": {
                "type": "object", "additionalProperties": False,
                "properties": {"ingredient_name": {"type": "string"}, "quantity": {"type": "number"}, "unit": {"type": "string"}},
                "required": ["ingredient_name", "quantity", "unit"],
            }},
        },
        "required": ["recipe_name", "yield_quantity", "yield_unit", "ingredients"],
    },
    "InventoryIntent": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "intent": {"type": "string", "enum": ["low", "out", "reorder", "stock", "highest_value", "unknown"]},
            "ingredient_name": {"type": ["string", "null"]},
        },
        "required": ["intent", "ingredient_name"],
    },
    "InventoryExplanation": {
        "type": "object", "additionalProperties": False,
        "properties": {"explanation": {"type": "string"}},
        "required": ["explanation"],
    },
}

