from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.auth import router as auth_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.investigations import router as investigations_router
from app.api.v1.rbac import router as rbac_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.knowledge_documents import (
    router as knowledge_documents_router,
)
from app.api.v1.incident_intelligence import (
    router as incident_intelligence_router,
)
from app.api.v1.remediations import (
    router as remediations_router,
)
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.chat import router as chat_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.exceptions import AppError
from app.core.sanitizer import redact_sensitive_data
from app.db.session import engine, get_db
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import request_observability_middleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.observability.logging import configure_logging
from app.observability.tracing import configure_tracing

app = FastAPI(
    title="OpsPilot API",
    description="AI-powered IT Operations and Incident Response Copilot",
    version="0.1.0",
)

cors_allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://opspilot.dev",
    "https://app.opspilot.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

configure_logging()
configure_tracing(
    app,
    engine=engine,
)
app.middleware("http")(request_observability_middleware)
metrics_app = make_asgi_app()
app.mount(
    "/metrics",
    metrics_app,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(investigations_router, prefix="/api/v1")
app.include_router(rbac_router, prefix="/api/v1")
app.include_router(knowledge_documents_router, prefix="/api/v1")
app.include_router(knowledge_documents_router)
app.include_router(incident_intelligence_router, prefix="/api/v1")
app.include_router(incident_intelligence_router)
app.include_router(remediations_router, prefix="/api/v1")
app.include_router(remediations_router)
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(audit_logs_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(chat_router)

import os
from fastapi.staticfiles import StaticFiles

_frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(_frontend_dist):
    app.mount("/ui", StaticFiles(directory=_frontend_dist, html=True), name="ui")


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "detail": redact_sensitive_data(exc.detail)},
        headers={"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import logging
    logger = logging.getLogger("opspilot.unhandled_exception")
    sanitized_msg = redact_sensitive_data(str(exc))
    logger.error(
        "Unhandled server exception on %s %s: %s",
        request.method,
        request.url.path,
        sanitized_msg,
        exc_info=exc,
    )
    req_id = request.headers.get("X-Request-ID")
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "An internal server error occurred.",
            "request_id": req_id,
        },
    )


@app.get("/")
def root(): return {"message":"OpsPilot API is running","version":"0.1.0"}
@app.get("/health")
def health_check(): return {"status":"healthy"}
@app.get("/db-health")
def database_health_check(db:Session=Depends(get_db)):
    try: return {"status":"healthy","database":"postgresql","result":db.execute(text("SELECT 1")).scalar_one()}
    except Exception as exc: raise HTTPException(status_code=503,detail="Database connection is unavailable") from exc

