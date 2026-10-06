"""Graph decisions and capability boundaries, with the provider mocked."""
import unittest
from unittest.mock import AsyncMock, patch
from typing import get_args

from app.ai.assistant_graph import AssistantTurn, AssistantDecision, interpret_turn
from app.ai.intents import INTENTS, RequestedAction
from app.ai.output_schemas import OUTPUT_SCHEMAS
from app.modules.menu.graph import MenuRequest, MenuIntent, run_menu_graph
from app.modules.menu.schemas import MenuDescription
from app.schemas.operations import (AssistantReply, AssistantFacts, IngredientDraft, RecipeDraft, InventoryIntent, InventoryExplanation, CommandIntent, MatchSuggestions)


def turn(message, **overrides):
    values = dict(message=message, module="menu", page="Menu Items", restaurant_name="Test Cafe",
                  user_role="owner", known={}, recent_messages=[], available_actions=["menu.item.create", "menu.item.update"])
    values.update(overrides)
    return AssistantTurn(**values)


def decision(intent, **overrides):
    values = dict(intent=intent, switch_task=True, requested_action="create", confidence=0.9,
                  secondary_intents=[], requested_module="menu")
    values.update(overrides)
    return AssistantDecision(**values)


class AssistantGraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_explicit_menu_create_survives_provider_failure(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock, side_effect=RuntimeError("provider unavailable")) as provider:
            result = await interpret_turn(turn("add menu item mexican tacos"), "req-fast")
        provider.assert_not_called()
        self.assertEqual(result.intent, "menu.item.create")
        self.assertEqual(result.name, "mexican tacos")
        self.assertEqual(result.requested_module, "menu")

    async def test_generic_menu_create_asks_for_name_without_provider(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock) as provider:
            result = await interpret_turn(turn("create a new menu item"), "req-generic")
        provider.assert_not_called()
        self.assertEqual(result.intent, "menu.item.create")
        self.assertIsNone(result.name)

    async def test_fast_path_still_respects_node_advertised_permissions(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock) as provider:
            result = await interpret_turn(turn("add menu item mexican tacos", available_actions=[]), "req-denied")
        provider.assert_not_called()
        self.assertEqual(result.intent, "assistant.other")

    async def test_multi_action_menu_message_uses_model_instead_of_fast_path(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock, return_value=decision("menu.item.create", name="Mexican Tacos", secondary_intents=["menu.item.update"])) as provider:
            result = await interpret_turn(turn("add menu item Mexican Tacos and change price to 250"), "req-multi")
        provider.assert_awaited_once()
        self.assertEqual(result.intent, "assistant.clarify")

    async def test_category_create_still_uses_intent_model(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock, return_value=decision("menu.category.create", name="Sides")) as provider:
            result = await interpret_turn(turn("add category Sides", available_actions=["menu.category.create"]), "req-category")
        provider.assert_awaited_once()
        self.assertEqual(result.intent, "menu.category.create")

    async def test_review_yes_and_no_do_not_call_provider(self):
        known = {"kind": "menu", "stage": "review", "intent": "menu.item.create"}
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock) as provider:
            yes = await interpret_turn(turn("yes", known=known), "req-1")
            no = await interpret_turn(turn("no", known=known), "req-2")
        provider.assert_not_called()
        self.assertEqual(yes.intent, "assistant.confirm")
        self.assertEqual(no.intent, "assistant.cancel")
        self.assertFalse(yes.switch_task)

    async def test_unapproved_action_is_not_returned_as_executable(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock, return_value=decision("menu.item.delete", requested_action="delete")):
            result = await interpret_turn(turn("delete it", available_actions=["menu.item.create"]), "req-3")
        self.assertEqual(result.intent, "assistant.other")
        self.assertEqual(result.requested_action, "unknown")

    async def test_recent_item_resolves_pronoun_without_database_id(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock, return_value=decision("menu.item.update", requested_action="update", target_name=None)):
            result = await interpret_turn(turn("change its price to 250", known={"recentEntity": {"type": "item", "name": "Dal Makhani", "id": "not-for-model"}}), "req-4")
        self.assertEqual(result.target_name, "Dal Makhani")

    async def test_explicit_cross_module_request_is_not_blocked_by_current_page(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock, return_value=decision("ingredient.create", requested_action="create", requested_module="inventory", name="Tomato")):
            result = await interpret_turn(turn("add tomato to inventory", available_actions=["ingredient.create"]), "req-cross")
        self.assertEqual(result.intent, "ingredient.create")
        self.assertEqual(result.requested_module, "inventory")

    async def test_unimplemented_archive_request_has_no_write_intent(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock, return_value=decision("assistant.other", requested_action="archive", requested_module="menu")):
            result = await interpret_turn(turn("archive this item", available_actions=[]), "req-archive")
        self.assertEqual(result.intent, "assistant.other")
        self.assertEqual(result.requested_action, "archive")

    async def test_multiple_actions_require_clarification(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock, return_value=decision("menu.item.create", secondary_intents=["menu.item.update"])):
            result = await interpret_turn(turn("add dal and update coffee", available_actions=["menu.item.create", "menu.item.update"]), "req-5")
        self.assertEqual(result.intent, "assistant.clarify")

    async def test_generic_menu_name_is_not_a_created_item(self):
        with patch("app.ai.assistant_graph.complete", new_callable=AsyncMock, return_value=decision("menu.item.create", name="menu item")):
            result = await interpret_turn(turn("add a menu item"), "req-6")
        self.assertIsNone(result.name)


class MenuGraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_menu_context_keeps_reference_and_suppresses_generic_name(self):
        parsed = MenuIntent(intent="menu.item.create", name="new menu item")
        with patch("app.modules.menu.graph.complete", new_callable=AsyncMock, return_value=parsed) as provider:
            result = await run_menu_graph(MenuRequest(message="add new menu item", known={"recentEntity": {"type": "item", "name": "Coffee", "id": "secret"}}), "req-7")
        self.assertIsNone(result.name)
        self.assertEqual(provider.await_args.args[2]["known"]["recentEntity"], {"type": "item", "name": "Coffee"})


class SchemaContractTests(unittest.TestCase):
    def test_strict_provider_contract_matches_typed_models(self):
        for model in (AssistantDecision, MenuIntent, AssistantReply, AssistantFacts, MenuDescription, IngredientDraft, RecipeDraft, InventoryIntent, InventoryExplanation, CommandIntent, MatchSuggestions):
            with self.subTest(model=model.__name__):
                schema = OUTPUT_SCHEMAS[model.__name__]
                self.assertEqual(set(schema["properties"]), set(model.model_fields))
                self.assertEqual(set(schema["required"]), set(model.model_fields))
        self.assertEqual(set(OUTPUT_SCHEMAS["AssistantDecision"]["properties"]["intent"]["enum"]), set(INTENTS))
        self.assertEqual(set(OUTPUT_SCHEMAS["AssistantDecision"]["properties"]["requested_action"]["enum"]), set(get_args(RequestedAction)))
