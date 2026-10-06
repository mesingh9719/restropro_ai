"""Contract checks without a live Sarvam account."""
import os
import unittest
from fastapi.testclient import TestClient
import main


class AssistantContractTest(unittest.TestCase):
    def setUp(self):
        self.previous = os.environ.get('INTERNAL_AI_SERVICE_TOKEN')
        os.environ['INTERNAL_AI_SERVICE_TOKEN'] = 'test-internal-token'
        self.original = main.complete
        self.client = TestClient(main.app)

    def tearDown(self):
        main.complete = self.original
        if self.previous is None:
            os.environ.pop('INTERNAL_AI_SERVICE_TOKEN', None)
        else:
            os.environ['INTERNAL_AI_SERVICE_TOKEN'] = self.previous

    def test_private_extraction_and_nullable_missing_facts(self):
        async def fake_complete(operation, _system, user, schema, _request_id):
            self.assertEqual(operation, 'assistant.extract')
            self.assertEqual(user['module'], 'inventory')
            return schema(intent='ingredient', name=None, usage=None, quantity=None, unit=None,
                          cost_per_unit=None, category=None, notes=None, yield_quantity=None,
                          recipe_name=None)
        main.complete = fake_complete
        body = {'message': 'Add an ingredient', 'module': 'inventory', 'known': {}, 'categories': [], 'units': ['kg']}
        path = '/internal/ai/assistant/extract'
        self.assertEqual(self.client.post(path, json=body).status_code, 401)
        response = self.client.post(path, json=body, headers={'Authorization': 'Bearer test-internal-token'})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()['name'])
        self.assertIsNone(response.json()['cost_per_unit'])

    def test_unknown_fields_are_rejected(self):
        response = self.client.post('/internal/ai/assistant/extract', json={
            'message': 'rice', 'module': 'inventory', 'known': {}, 'categories': [], 'units': [], 'secret': 'no'
        }, headers={'Authorization': 'Bearer test-internal-token'})
        self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()
