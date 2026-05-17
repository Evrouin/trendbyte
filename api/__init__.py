"""TrendByte API — FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import trends, predictions, categories, reports, stats

app = FastAPI(
    title="TrendByte API",
    description="Tech trend intelligence — tracks emerging technologies across developer communities.",
    version="0.1.0",
)

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


@app.get("/")
def root():
    return {"name": "TrendByte API", "version": "0.1.0", "docs": "/docs"}
