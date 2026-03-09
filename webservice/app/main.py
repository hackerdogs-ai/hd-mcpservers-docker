"""
Tools Web Service - FastAPI app. PRD: strict compliance on logging, exception handling, resiliency.
API cannot crash: all exceptions are caught and converted to JSON responses.
"""
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.exceptions import (
    AppException,
    CatalogLoadError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolTimeoutError,
    ValidationError,
)
from app.logging_config import configure_logging, get_logger
from app.routers import tools

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: configure logging. Shutdown: nothing."""
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("tools_webservice_starting", extra={"api_prefix": settings.api_v1_prefix})
    yield
    logger.info("tools_webservice_stopping")


app = FastAPI(
    title="Tools Web Service",
    description="PRD-compliant API for MCP tools catalog, search, get_tool_info, and run_tool (OCSF output).",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(tools.router, prefix=get_settings().api_v1_prefix)


def _error_body(message: str, details: dict[str, Any], error_code: str) -> dict[str, Any]:
    return {"error": error_code, "message": message, "details": details}


@app.exception_handler(ToolNotFoundError)
async def tool_not_found_handler(request: Request, exc: ToolNotFoundError) -> JSONResponse:
    logger.warning("http_404_tool_not_found", extra={"path": request.url.path, "error_message": exc.message})
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=_error_body(exc.message, exc.details, "tool_not_found"),
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    logger.warning("http_400_validation", extra={"path": request.url.path, "error_message": exc.message})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=_error_body(exc.message, exc.details, "validation_error"),
    )


@app.exception_handler(ToolExecutionError)
async def tool_execution_error_handler(request: Request, exc: ToolExecutionError) -> JSONResponse:
    logger.warning("http_502_tool_execution", extra={"path": request.url.path, "error_message": exc.message})
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=_error_body(exc.message, exc.details, "tool_execution_error"),
    )


@app.exception_handler(ToolTimeoutError)
async def tool_timeout_error_handler(request: Request, exc: ToolTimeoutError) -> JSONResponse:
    logger.warning("http_504_tool_timeout", extra={"path": request.url.path, "error_message": exc.message})
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content=_error_body(exc.message, exc.details, "tool_timeout"),
    )


@app.exception_handler(CatalogLoadError)
async def catalog_load_error_handler(request: Request, exc: CatalogLoadError) -> JSONResponse:
    logger.warning("http_503_catalog_load", extra={"path": request.url.path, "error_message": exc.message})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=_error_body(exc.message, exc.details, "catalog_load_error"),
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("http_app_exception", extra={"path": request.url.path, "error_message": exc.message})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(exc.message, exc.details, "application_error"),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: API cannot crash. Log full context to stderr, return safe 500."""
    logger.exception(
        "http_500_unhandled",
        extra={"path": request.url.path, "method": request.method, "error": str(exc)},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(
            "An unexpected error occurred. The incident has been logged.",
            {},
            "internal_error",
        ),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness: service is running."""
    return {"status": "ok"}


@app.get("/ready", response_model=None)
async def ready() -> dict[str, Any] | JSONResponse:
    try:
        from app.catalog import get_catalog
        catalog = get_catalog()
        return {"status": "ok", "tools_count": len(catalog.get("tools") or [])}
    except Exception as e:
        logger.warning("ready_check_failed", extra={"error": str(e)})
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "error": str(e)},
        )
