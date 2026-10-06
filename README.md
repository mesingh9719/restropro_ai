# RestroPro AI service

Stateless FastAPI service for Sarvam-powered drafts and intent interpretation. It has no database access and cannot create or change inventory, recipes, stock, or orders. The Node API authenticates requests with `INTERNAL_AI_SERVICE_TOKEN` and supplies only restaurant-scoped context.

Copy `.env.example` to `.env`, keep the existing `SARVAM_API_KEY` and `SARVAM_API_BASE_URL` values, and set the same strong `INTERNAL_AI_SERVICE_TOKEN` in both backend and AI service environments. The legacy `DATABASE_URL` and `FRONTEND_URL` values were removed from the local AI `.env`; do not supply them in deployment configuration.

Run with `uvicorn main:app --host 127.0.0.1 --port 8001` from this directory. Set `AI_SERVICE_URL=http://127.0.0.1:8001` in the Node backend. In production, restrict network access so only Node can reach the AI service; TLS is required if traffic crosses hosts.

## Flow before this change

The frontend ingredient dialog sent `{prompt}` to Node `/inventory/ai/ingredient/draft`; the recipe editor sent `{prompt}` to `/inventory/ai/recipes/:itemId/draft`. Node authenticated the user, loaded restaurant categories or ingredients, and sent a bearer-authenticated request to FastAPI. FastAPI requested structured JSON from Sarvam. Node matched names to current restaurant records and returned a preview. The frontend could copy that preview into its standard editable form, whose separate inventory POST or recipe PUT performed the final write. There were no follow-up questions, persisted draft references, or AI correction records. Inventory question and command endpoints use the same FastAPI intent service and remain separate from draft confirmation.

## Request and confirmation flow

1. The authenticated frontend sends a description to the Node `/inventory/ai/ingredient/draft` or `/inventory/ai/recipes/:itemId/draft` endpoint. Node supplies restaurant-scoped categories, units, inventory names and up to 20 recent corrections from that restaurant to this service over the shared bearer token. The AI service has no database credentials.
2. Node validates the provider output against current restaurant data. Ingredient stock and cost are included only when the same number appeared in the user description or follow-up answer. Missing category, unit, or recipe yield can return `status: needs_input` and `questions`; the frontend resends the prompt with `answers`.
3. A completed response contains `status: draft`, `draftId`, `draft`, and `uncertainFields`. Node stores the original suggestion with a 30-minute expiry in `ai_drafts`. This step does not change inventory or recipes.
4. The user applies the draft to the existing editable form, corrects values, and saves through the normal Node inventory or recipe endpoint with `aiDraftId`. That endpoint validates the record and atomically stores changed fields in `ai_corrections` with the original value, confirmed value, user, restaurant, prompt context, and timestamp. Reuse, expiry, or a draft from another user or restaurant is rejected. Regular manual saves remain supported without `aiDraftId`.
5. Later suggestions receive recent corrections filtered by `businessId`. They are hints to the model and cannot create IDs, stock or prices.

`npm run db:migrate` in `backend` creates the two tables before deploying the new backend. Keep the same token in both services. Run the AI service behind private networking and configure `SARVAM_TIMEOUT_SECONDS` (1–22 seconds). The provider retries a transient 429/502/503/504 once; Node caps the entire request at 25 seconds. The existing per-user, per-restaurant Node AI rate limit is 10 requests per minute.

## Central chat extraction

`POST /internal/ai/assistant/extract` returns nullable facts and an intent for each latest chat turn. Node supplies known task facts so follow-up answers are interpreted in context; Node still verifies that names and numeric values came from the user's message and resolves category and ingredient names against its own tenant-scoped data. `POST /internal/ai/assistant/respond` provides bounded guidance from the current module's permitted actions and field hints when no business mutation is supported. Both internal routes use the shared service bearer token and strict output validation. Conversation history, review forms, and final writes remain in Node. See [central assistant architecture](../docs/assistant-architecture.md).
