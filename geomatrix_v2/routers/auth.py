"""Authentication endpoints for the GEOMATRIX application.

Password login uses credentials stored only in server-side environment variables.
Google login remains available through the Next.js Google Identity Services flow.
"""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str


def _create_session(email: str, name: str) -> str:
    secret = (os.getenv("AUTH_SECRET") or os.getenv("NEXTAUTH_SECRET") or "").encode()
    if not secret:
        raise RuntimeError("AUTH_SECRET is not configured.")

    payload = {
        "email": email,
        "name": name,
        "iat": int(time.time() * 1000),
    }
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(
        hmac.new(secret, body.encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    return f"{body}.{signature}"


@router.post("/login")
def login(request: LoginRequest, response: Response):
    configured_email = (os.getenv("AUTH_EMAIL") or "").strip().lower()
    configured_password = os.getenv("AUTH_PASSWORD") or ""

    if not configured_email or not configured_password:
        raise HTTPException(
            503,
            "Password login is not configured. Set AUTH_EMAIL and AUTH_PASSWORD in the deployment environment.",
        )

    supplied_email = request.email.strip().lower()
    if (
        not hmac.compare_digest(supplied_email, configured_email)
        or not hmac.compare_digest(request.password, configured_password)
    ):
        raise HTTPException(401, "Invalid email or password.")

    try:
        session = _create_session(request.email.strip(), request.email.strip())
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc

    response.set_cookie(
        key="geomatrix_session",
        value=session,
        httponly=True,
        secure=os.getenv("APP_ENV", "development").lower() == "production",
        samesite="lax",
        path="/",
        max_age=8 * 60 * 60,
    )
    return {"email": request.email.strip(), "name": request.email.strip()}


@router.post("/google")
def google_login(_: GoogleLoginRequest):
    raise HTTPException(403, "Google authentication is handled by the frontend identity-provider flow.")


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("geomatrix_session", path="/")
    return {"success": True}


@router.get("/google/callback")
def google_callback(error: str | None = None):
    if error:
        raise HTTPException(400, f"Google OAuth callback error: {error}")
    return {
        "success": True,
        "message": "Use Google Identity Services sign-in; this callback is compatibility-only.",
    }


@router.get("/health")
def health():
    return {"status": "ok"}
