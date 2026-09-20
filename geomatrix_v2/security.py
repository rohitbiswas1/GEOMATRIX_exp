"""Shared signed-session verification for the FastAPI backend."""
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

def _b64decode(value: str) -> bytes:
    padded = value.replace("-", "+").replace("_", "/")
    padded += "=" * ((4 - len(padded) % 4) % 4)
    return base64.b64decode(padded)

def verify_session_token(token: str | None) -> dict[str, Any] | None:
    secret = (os.getenv("AUTH_SECRET") or os.getenv("NEXTAUTH_SECRET") or "").encode()
    if not secret or not token:
        return None
    try:
        body, signature = token.split(".", 1)
        expected = base64.urlsafe_b64encode(hmac.new(secret, body.encode(), hashlib.sha256).digest()).decode().rstrip("=")
        if not hmac.compare_digest(expected, signature):
            return None
        payload = json.loads(_b64decode(body).decode("utf-8"))
        issued_at = float(payload.get("iat", 0))
        if issued_at < 1_000_000_000_000 or time.time() * 1000 - issued_at > 8 * 60 * 60 * 1000:
            return None
        return payload
    except Exception:
        return None

def is_production() -> bool:
    return os.getenv("APP_ENV", "development").lower() == "production"
