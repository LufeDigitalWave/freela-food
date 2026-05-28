"""Entrypoint FastAPI — middleware, exception handler, rotas."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.v1.applications.router import router as applications_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.health.router import router as health_router
from app.api.v1.jobs.router import router as jobs_router
from app.api.v1.me.router import router as me_router
from app.api.v1.notifications.router import router as notifications_router
from app.core.config import get_settings
from app.core.exceptions import DomainError
from app.core.logging import configure_logging, get_logger
from app.core.redis_client import close_redis
from app.utils.audit import request_ip, request_ua


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    log = get_logger("app.lifespan")
    log.info("api.startup", env=get_settings().env)
    yield
    await close_redis()
    log.info("api.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="freela-food API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _audit_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_ip.set(request.client.host if request.client else None)
        request_ua.set(request.headers.get("user-agent"))
        return await call_next(request)

    @app.exception_handler(DomainError)
    async def _domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
        log = get_logger("app.error")
        log.exception("unhandled_error", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Erro interno"},
        )

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/v1")
    app.include_router(me_router, prefix="/v1")
    app.include_router(jobs_router, prefix="/v1")
    app.include_router(notifications_router, prefix="/v1")
    app.include_router(applications_router, prefix="/v1")

    return app


app = create_app()
