# RestroPro AI service

This is the private FastAPI interpretation and drafting service behind the authenticated Node API. It has **no database connection or application write tools**. React talks to Node; Node supplies bounded restaurant context to FastAPI, resolves names against its own tenant-scoped services, stores conversations and proposals, enforces permissions, confirms mutations, and audits writes. FastAPI calls Sarvam for typed intent/entity decisions and drafts.

## Architecture

```text
React assistant → Node /api/assistant + Socket.IO
                 ├─ auth, permissions, restaurant-scoped lookup, conversation state
                 ├─ proposal token → review → confirm → transaction + audit
                 └─ private FastAPI /internal/ai/* → typed LangGraph → Sarvam
```

A model response is **a proposal, never a tool call**. FastAPI cannot execute SQL, create a menu item, or trust a model-supplied record ID. Node registers supported actions in `backend/src/services/assistantActions.service.js`; `assistantMenu.service.js` and the existing inventory/recipe services are the controlled tools. They recheck tenant ownership, constraints, duplicates, and permissions at confirmation. Name resolution in `assistantEntityResolution.service.js` treats a fuzzy match as a suggestion and refuses ambiguous exact names.

The internal routes retain their existing paths and JSON contracts. The newer `requested_action`, `confidence`, and `secondary_intents` fields on `/internal/ai/assistant/route` add broad action recognition and ambiguity metadata; Node asks for clarification on multiple actions or low confidence. These fields never authorize execution.

## Source structure

```text
app/
  main.py                 FastAPI composition and request-ID logging
  api/routes/             Assistant, Menu, and existing operation endpoints
  core/                   Environment settings, service-token auth, JSON logging
  ai/                     Provider transport, strict output schemas, prompts,
                          intent catalog, assistant LangGraph
  modules/menu/           Menu LangGraph and typed menu request/decision schemas
  schemas/assistant.py    Typed assistant turn and intent decision
  schemas/                Existing ingredient, recipe, inventory, and draft contracts
tests/                    API, graph, schema, and provider boundary tests
```

Top-level `main.py`, `provider.py`, `assistant_graph.py`, and `menu_graph.py` are thin compatibility imports. Existing `uvicorn main:app` commands continue to work; new deployments should use `uvicorn app.main:app`.

The assistant graph normalizes the request, detects review-stage controls such as `yes`/`no`/`cancel`, recognizes unambiguous Menu item create commands locally, asks Sarvam for a structured decision when needed, validates the decision against Node-advertised action IDs, then applies module-specific menu refinement. The local create path still requires the same Node permission, database lookup, review, and confirmation; complex or multi-action requests continue through Sarvam. The menu graph has context, classification, validation, and read/write routing nodes. Neither graph executes a database operation. The graphs keep current module/page and recent conversation text as **context**, while Node holds the authoritative task and proposal state.

## Confirmation and missing data

Node's menu task uses `collecting` (draft), `review` (awaiting confirmation), and `done` stages. A review contains a single-use proposal token. The UI can confirm with the review button; saying `yes` in a review now uses the same Node transaction, token, tenant checks, and audit path. `no` or `cancel` discards the pending draft. A price or description correction replans the review before a write. Ingredient and recipe reviews continue through their existing confirmation forms.

For a missing menu description, Node passes only the item name and verified category/recipe ingredient names to `/internal/ai/menu/description`. The suggestion is kept out of the initial item insert. After the item is saved, chat shows a separate editable description review; confirming that review updates the item, while skipping it leaves the saved item unchanged. A category, menu schedule, price, inventory amount, or foreign key is never invented by the AI service.

## Internal API

| Route | Purpose |
|---|---|
| `GET /health` | Process health; no secrets |
| `POST /internal/ai/assistant/route` | Typed intent and entity decision |
| `POST /internal/ai/assistant/respond` | Grounded guidance for unsupported requests |
| `POST /internal/ai/assistant/extract` | Legacy ingredient/recipe extraction contract |
| `POST /internal/ai/menu/interpret` | Menu-specific graph contract |
| `POST /internal/ai/menu/description` | Bounded description suggestion |
| `POST /internal/ai/ingredient/parse`, `/ingredient/match` | Ingredient draft and candidate suggestions |
| `POST /internal/ai/recipe/generate` | Recipe draft |
| `POST /internal/ai/inventory/interpret`, `/inventory/explain` | Inventory question interpretation |
| `POST /internal/ai/command/interpret` | Existing inventory/recipe command decision |

All POST routes require the shared `INTERNAL_AI_SERVICE_TOKEN` bearer token. FastAPI validates unknown fields, bounds provider output with strict JSON schemas and Pydantic, and returns 502/504 for invalid or timed-out provider responses. Logs contain operation, duration, outcome, and a request ID, not message text or keys. Node sends the current message ID as the provider request ID for route and menu draft calls; the same ID appears in FastAPI logs and menu audit data.

## Setup and run

From the repository root, in separate terminals:

```bash
cd restropro_ai
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

```bash
cd backend
npm install
npm run dev
```

```bash
cd frontend
npm install
npm run dev
```

For a fresh installation, create `restropro_ai/.env` from `.env.example` and fill in the private values; keep any existing `.env` intact. Set `AI_SERVICE_URL=http://127.0.0.1:8001` and the **same** `INTERNAL_AI_SERVICE_TOKEN` in the Node environment. Keep the actual `.env` private. `.env.example` contains placeholders only. Existing database migrations belong to Node; this FastAPI refactor adds none.

| Variable | Purpose |
|---|---|
| `INTERNAL_AI_SERVICE_TOKEN` | Required private Node-to-FastAPI bearer token |
| `SARVAM_API_KEY` | Required provider credential |
| `SARVAM_API_BASE_URL` | Sarvam endpoint base; defaults to `https://api.sarvam.ai` |
| `SARVAM_MODEL` | Defaults to `sarvam-105b` |
| `SARVAM_TIMEOUT_SECONDS` | Total provider budget, 5–40 seconds; defaults to 32 |
| `AI_PROVIDER` | Currently `sarvam` |
| `APP_ENV` | `development`, `test`, or `production`; production requires both credentials and an HTTPS provider URL |
| `LOG_LEVEL` | JSON application log level; defaults to `INFO` |

For production, expose FastAPI only on a private network, use TLS between hosts, manage both secrets outside the repository, and supervise all three processes. Run Node migrations using the existing deployment process, not from this service. Use separate staging restaurants for end-to-end validation. Avoid logging prompt bodies or customer information.

## Extending the assistant

1. Define the business action, permission, tenant-scoped resolver, validator, proposal, confirmation transaction, and audit entry in **Node**. Register its ID in `assistantActions.service.js`. Do not send arbitrary model-selected function names to Node.
2. Add the supported intent to `app/ai/intents.py`, the assistant decision type and strict provider schema, and a short module-specific prompt. The schema-parity test catches mismatches. Unsupported actions can still be recognized as `requested_action` and answered with `assistant.other` until the Node tool exists.
3. Add a FastAPI route or module graph only if that module needs a distinct typed drafting contract. Reuse the shared provider, settings, logging, and auth. No empty directories or duplicate database layer are needed.
4. Add mocked graph/API tests and Node resolver/confirmation tests; then manually verify the real provider and a staging tenant. In particular, test wrong-restaurant IDs, duplicate names, stale proposals, missing fields, cancellation, and failed provider calls.

## Tests

These tests use mocked provider responses or in-memory models; they do not contact Sarvam or a database.

```bash
cd restropro_ai
venv/bin/python -m unittest discover -s tests -v
```

```bash
cd backend
node --test test/assistant-entity-resolution.test.js test/assistant-menu-confirm.test.js
```

A live provider call and real database/socket workflow still need staging validation. Text chunks are emitted after a complete typed provider response, so they are not token-by-token Sarvam streaming. Multi-instance Socket.IO fanout and cancellation of a request already executing in the provider remain deployment concerns.
