"""Gemini decision-support endpoint. Secrets remain server-side."""
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/gemini", tags=["gemini"])

class GeminiRequest(BaseModel):
    project: dict[str, Any]
    prediction: dict[str, Any] | None = None
    shap_features: list[dict[str, Any]] | None = None

def _build_prompt(req: GeminiRequest) -> str:
    feature_summary = "\n".join(
        f"- {item.get('feature', 'unknown')}: {item.get('shap_value', 0)} ({item.get('direction', 'neutral')})"
        for item in (req.shap_features or [])[:8]
    ) or "- No SHAP features available."
    return (
        "You are a decision-support assistant for land-acquisition monitoring. "
        "Use ONLY supplied facts. Never invent project facts, scores, legal status, "
        "citations, or official decisions. State that your output is AI-generated "
        "decision support requiring human review.\n\n"
        f"Project data:\n{req.project}\n\n"
        f"ML prediction:\n{req.prediction or {}}\n\n"
        f"SHAP contributions:\n{feature_summary}\n\n"
        "Provide a concise risk-driver explanation and evidence-based actions."
    )

@router.post("/explain")
def explain_with_gemini(req: GeminiRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(503, "GEMINI_API_KEY is not configured.")
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=_build_prompt(req),
        )
        generated = getattr(response, "text", None) or str(response)
        return {
            "status": "ok",
            "label": "AI-generated decision support",
            "summary": generated,
            "source": "gemini",
        }
    except Exception as exc:
        raise HTTPException(502, "Gemini explanation service failed.") from exc
