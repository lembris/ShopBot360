import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.api.admin.router import router as admin_router
from app.api.billing.router import router as billing_router
from app.api.health.router import router as health_router
from app.api.webhook.router import router as webhook_router
from app.core.config import get_settings
from app.core.exceptions import ShopBotError, to_http_exception
from app.core.logger import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.services.redis import close_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.app_debug)
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
    yield
    await close_redis()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="WhatsApp Shop Bot",
        version="1.0.0",
        debug=settings.app_debug,
        lifespan=lifespan,
    )
    app.add_middleware(RequestIDMiddleware)

    @app.exception_handler(ShopBotError)
    async def shopbot_error_handler(request: Request, exc: ShopBotError):
        return JSONResponse(
            status_code=to_http_exception(exc).status_code,
            content={"detail": exc.message, "code": exc.code},
        )

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(health_router)
    app.include_router(webhook_router)
    app.include_router(admin_router)
    app.include_router(billing_router)
    return app


app = create_app()
