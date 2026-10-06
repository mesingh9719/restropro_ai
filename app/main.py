"""Private, stateless AI interpretation and drafting API."""
import logging
import re
import time
import uuid
from fastapi import FastAPI, Request
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_var
from app.api.routes import assistant, menu, operations

settings = get_settings()
if settings.environment == "production":
    if not settings.internal_ai_service_token or not settings.sarvam_api_key:
        raise RuntimeError("Missing required AI service credentials")
    if not settings.sarvam_api_base_url.startswith("https://"):
        raise RuntimeError("Production AI provider URL must use HTTPS")
configure_logging(settings.log_level)
logger = logging.getLogger("restropro_ai")
app = FastAPI(title="RestroPro AI", docs_url=None, redoc_url=None)
app.include_router(assistant.router)
app.include_router(menu.router)
app.include_router(operations.router)


@app.middleware("http")
async def log_request(request: Request, call_next):
    raw_id = request.headers.get("x-request-id", "")
    request_id = raw_id if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", raw_id) else str(uuid.uuid4())
    token = request_id_var.set(request_id)
    started = time.monotonic()
    try:
        response = await call_next(request)
        logger.info("request_complete path=%s method=%s status=%d duration_ms=%d", request.url.path, request.method, response.status_code, int((time.monotonic() - started) * 1000))
        response.headers["X-Request-Id"] = request_id
        return response
    except Exception:
        logger.exception("request_failed path=%s method=%s", request.url.path, request.method)
        raise
    finally:
        request_id_var.reset(token)


@app.get("/health")
def health():
    return {"status": "ok"}
