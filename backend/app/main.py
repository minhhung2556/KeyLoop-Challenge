from contextlib import asynccontextmanager
from pathlib import Path

import logging
import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.leads import router as leads_router
from app.config import settings
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.repositories.lead_repository import SQLiteLeadRepository
from app.seed import seed_demo_leads


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level, logging.INFO)
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    if settings.log_format == "json":
        processors = shared_processors + [structlog.processors.JSONRenderer()]
    else:
        processors = shared_processors + [structlog.dev.ConsoleRenderer(colors=True)]
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging_config = {
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "level": log_level,
        "force": True,
    }
    if settings.LOG_FILE:
        log_file = Path(settings.LOG_FILE)
        if not log_file.is_absolute():
            log_file = Path(__file__).resolve().parents[2] / log_file
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logging_config.update(filename=str(log_file), filemode="a")
    logging.basicConfig(**logging_config)


setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    repo = SQLiteLeadRepository(settings.database_path)
    seed_demo_leads(repo)
    logger.info("application_started", database=str(settings.database_path))
    yield
    logger.info("shutting_down_application")


app = FastAPI(
    title="Keyloop Sales Lead API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    RequestLoggingMiddleware,
    log_request_body=settings.log_request_body,
    log_response_body=settings.log_response_body,
    max_body_length=settings.log_max_body_length,
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

app.include_router(leads_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": request_id},
        headers=dict(exc.headers or {}),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        errors.append({"field": field, "message": error.get("msg", "Invalid value")})
    return JSONResponse(
        status_code=422,
        content={
            "detail": {"error_code": "LEAD_VALIDATION_ERROR", "message": "Validation error"},
            "errors": errors,
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "global_exception",
        exc_type=type(exc).__name__,
        request_id=request_id,
        path=request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": {"error_code": "INTERNAL_SERVER_ERROR", "message": "Internal server error"},
            "request_id": request_id,
        },
    )
