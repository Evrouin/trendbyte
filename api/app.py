from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.database import close_pool, init_pool
from api.errors import global_exception_handler
from api.middleware import CacheMiddleware, RequestSizeLimitMiddleware, SecurityHeadersMiddleware
from api.routes import categories, content, news, predictions, reports, stats, trends
from api.security import HMACMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_pool()
    yield
    await close_pool()


def create_app() -> FastAPI:
    app = FastAPI(
        title="TrendByte API",
        description="Tech trend intelligence — tracks emerging technologies across developer communities.",
        version="0.1.0",
        lifespan=lifespan,
    )

    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, global_exception_handler)  # type: ignore[arg-type]

    app.add_middleware(HMACMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CacheMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    app.include_router(trends.router, prefix="/api")
    app.include_router(predictions.router, prefix="/api")
    app.include_router(categories.router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    app.include_router(news.router, prefix="/api")
    app.include_router(content.router, prefix="/api")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"name": "TrendByte API", "version": "0.1.0", "docs": "/docs"}

    return app
