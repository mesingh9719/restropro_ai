"""Authenticate Node-to-FastAPI calls without accepting client identity claims."""
import secrets
from fastapi import Header, HTTPException
from app.core.config import get_settings


def authorize(authorization: str | None = Header(default=None)) -> None:
    expected = get_settings().internal_ai_service_token
    supplied = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
    if not expected or not secrets.compare_digest(supplied.encode('utf-8'), expected.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Unauthorized")
