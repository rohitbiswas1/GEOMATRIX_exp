"""Vercel service entrypoint for GEOMATRIX FastAPI.

Loads the packaged FastAPI app and, during a bootstrap failure, keeps a tiny
diagnostic health endpoint alive so deployment failures are observable.
"""
import importlib
import sys
import types
import traceback
from importlib.machinery import ModuleSpec
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

SERVICE_ROOT = Path(__file__).resolve().parent

package = sys.modules.get("geomatrix_v2")
if package is None:
    package = types.ModuleType("geomatrix_v2")
    package.__path__ = [str(SERVICE_ROOT)]
    package.__package__ = "geomatrix_v2"
    package.__spec__ = ModuleSpec("geomatrix_v2", loader=None, is_package=True)
    sys.modules["geomatrix_v2"] = package

_bootstrap_error = None
try:
    loaded_app = importlib.import_module("geomatrix_v2.main").app
except Exception as exc:
    _bootstrap_error = {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc()[-6000:],
    }
    loaded_app = FastAPI(title="GEOMATRIX bootstrap diagnostics", version="diagnostic")

    @loaded_app.get("/health")
    def bootstrap_health(response: Response):
        response.status_code = 503
        return JSONResponse(
            status_code=503,
            content={
                "status": "bootstrap_error",
                "service": "geomatrix-api",
                "error": _bootstrap_error,
            },
        )

    @loaded_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    def bootstrap_fallback(path: str):
        return JSONResponse(
            status_code=503,
            content={
                "status": "bootstrap_error",
                "message": "GEOMATRIX backend failed to initialise.",
                "path": path,
            },
        )
else:
    loaded_app.get("/health")(loaded_app.router.routes[-1].endpoint) if False else None

app = loaded_app
