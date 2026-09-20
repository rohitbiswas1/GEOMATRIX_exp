"""Authentication compatibility endpoints.

Production authentication is handled by the Next.js identity-provider flow.
This backend router never decodes or trusts an unsigned Google payload.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    credential: str

@router.post("/login")
def login(_: LoginRequest):
    raise HTTPException(403, "Password authentication is disabled. Use the configured identity provider.")

@router.post("/google")
def google_login(_: GoogleLoginRequest):
    raise HTTPException(403, "Google authentication is handled by the frontend identity-provider flow.")

@router.post("/logout")
def logout():
    return {"success": True, "message": "Frontend session cookie should be cleared by the Next.js auth route."}

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
