"""Simple password/Google compatibility endpoints for GEOMATRIX.

Password credentials are configured via server-side AUTH_EMAIL/AUTH_PASSWORD.
Google Identity Services remains available through the frontend route.
"""
import os

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr

from security import create_signed_session_cookie

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str


@router.post("/login")
def login(body: LoginRequest, response: Response):
    configured_email = os.getenv("AUTH_EMAIL", "").strip().lower()
    configured_password = os.getenv("AUTH_PASSWORD", "")

    if not configured_email or not configured_password:
        raise HTTPException(
            503,
            "Password sign-in is not configured. Set AUTH_EMAIL and AUTH_PASSWORD.",
        )

    if body.email.strip().lower() != configured_email or body.password != configured_password:
        raise HTTPException(401, "Invalid email or password.")

    response.set_cookie(
        key="geomatrix_session",
        value=create_signed_session_cookie({"email": configured_email, "name": configured_email.split("@")[0]}),
        httponly=True,
        secure=os.getenv("APP_ENV", "development").lower() == "production",
        samesite="lax",
        max_age=8 * 60 * 60,
        path="/",
    )
    return {"success": True, "email": configured_email, "name": configured_email.split("@")[0]}


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
