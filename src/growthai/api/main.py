"""FastAPI application factory (feature #12).

Wires routers, CORS, exception handling and OpenAPI metadata. Run with:

    uvicorn growthai.api.main:app --reload

Swagger UI is served at ``/docs`` and ReDoc at ``/redoc``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from growthai import __version__
from growthai.api.routers import analysis, analytics, auth, chat, patients, reports
from growthai.config import get_settings
from growthai.core.exceptions import GrowthAIError
from growthai.db.base import init_db
from growthai.logging_conf import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("GrowthAI API %s started (env=%s)", __version__, settings.env)
    yield
    logger.info("GrowthAI API shutting down")


app = FastAPI(
    title="GrowthAI API",
    version=__version__,
    description=(
        "AI-powered growth, nutrition, risk and forecasting platform for children "
        "and young adults. Educational decision-support - not a medical device."
    ),
    lifespan=lifespan,
    contact={"name": "GrowthAI", "url": "https://github.com/prajwal3244"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(GrowthAIError)
async def domain_error_handler(request: Request, exc: GrowthAIError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/", tags=["meta"], summary="Service metadata")
def root() -> dict:
    return {
        "name": "GrowthAI",
        "version": __version__,
        "docs": "/docs",
        "status": "ok",
    }


@app.get("/health", tags=["meta"], summary="Health check")
def health() -> dict:
    return {"status": "healthy"}


for r in (auth.router, patients.router, analysis.router, reports.router, chat.router, analytics.router):
    app.include_router(r)
