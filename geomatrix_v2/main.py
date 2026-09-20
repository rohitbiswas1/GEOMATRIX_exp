from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text

from .database import init_db, engine, DATABASE_URL
from .routers.alerts import router as alerts_router
from .routers.analytics import router as analytics_router
from .routers.auth import router as auth_router
from .routers.gemini import router as gemini_router
from .routers.ingest import router as ingest_router
from .routers.map import router as map_router
from .routers.ml import router as ml_router
from .routers.projects import router as projects_router

app = FastAPI(
    title="GEOMATRIX Land Acquisition Risk Intelligence API",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

allowed_origins = [
    origin.strip()
    for origin in __import__("os").getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID", "X-Admin-Token"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        host.strip()
        for host in __import__("os").getenv("ALLOWED_HOSTS", "*").split(",")
        if host.strip()
    ],
)

app.include_router(auth_router)
app.include_router(gemini_router)
app.include_router(projects_router)
app.include_router(alerts_router)
app.include_router(ingest_router)
app.include_router(map_router)
app.include_router(ml_router)
app.include_router(analytics_router)

init_db()


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "geomatrix-api", "version": app.version}


@app.get("/health/ready")
def readiness():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok", "database_url_configured": bool(DATABASE_URL)}
    except Exception:
        return {"status": "not_ready", "database": "error", "database_url_configured": bool(DATABASE_URL)}
