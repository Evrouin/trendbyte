"""TrendByte API — FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.routes import categories, news, predictions, reports, stats, trends

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="TrendByte API",
    description="Tech trend intelligence — tracks emerging technologies across developer communities.",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

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


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "TrendByte API", "version": "0.1.0", "docs": "/docs"}
