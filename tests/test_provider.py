"""Provider transport failures and strict output validation without network access."""
import json
import os
import unittest
from unittest.mock import patch
import httpx
from fastapi import HTTPException
from app.ai.provider import complete
from app.modules.menu.schemas import MenuDescription

RealAsyncClient = httpx.AsyncClient


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.env = patch.dict(os.environ, {"SARVAM_API_KEY": "test-key", "SARVAM_API_BASE_URL": "https://example.test", "SARVAM_TIMEOUT_SECONDS": "5"})
        self.env.start()

    async def asyncTearDown(self):
        self.env.stop()

    async def call_with(self, handler):
        transport = httpx.MockTransport(handler)
        with patch("httpx.AsyncClient", side_effect=lambda **kwargs: RealAsyncClient(transport=transport, **kwargs)):
            return await complete("menu.description", "Draft one description", {"name": "Dal Makhani"}, MenuDescription, "request-123")

    async def test_sends_bounded_typed_request_and_parses_valid_result(self):
        seen = []
        def handler(request):
            seen.append((request.headers, json.loads(request.content)))
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"description": "A rich and comforting dal dish."})}}]})
        result = await self.call_with(handler)
        self.assertEqual(result.description, "A rich and comforting dal dish.")
        self.assertEqual(seen[0][1]["max_tokens"], 220)
        self.assertEqual(seen[0][0]["api-subscription-key"], "test-key")
        self.assertEqual(seen[0][1]["response_format"]["json_schema"]["name"], "menudescription")

    async def test_retries_transient_provider_status_once(self):
        attempts = 0
        def handler(_request):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                return httpx.Response(503)
            return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"description": "A rich and comforting dal dish."})}}]})
        result = await self.call_with(handler)
        self.assertEqual(attempts, 2)
        self.assertTrue(result.description)

    async def test_malformed_output_fails_closed(self):
        def handler(_request):
            return httpx.Response(200, json={"choices": [{"message": {"content": '{"description": 3}'}}]})
        with self.assertRaises(HTTPException) as raised:
            await self.call_with(handler)
        self.assertEqual(raised.exception.status_code, 502)

    async def test_provider_timeout_is_reported_without_internal_details(self):
        def handler(request):
            raise httpx.ReadTimeout("private upstream detail", request=request)
        with self.assertRaises(HTTPException) as raised:
            await self.call_with(handler)
        self.assertEqual(raised.exception.status_code, 504)
        self.assertNotIn("private upstream detail", raised.exception.detail)
