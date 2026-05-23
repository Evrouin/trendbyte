"""HMAC request signing verification."""

from __future__ import annotations

import hashlib
import hmac
import time
from os import environ

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

HMAC_SECRET = environ.get("HMAC_SECRET", "")
MAX_AGE_SECONDS = 300  # 5 minutes

SKIP_PATHS = ("/", "/docs", "/openapi.json", "/redoc", "/health")


class HMACMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if not HMAC_SECRET or request.url.path in SKIP_PATHS:
            return await call_next(request)

        timestamp = request.headers.get("X-Timestamp", "")
        signature = request.headers.get("X-Signature", "")

        if not timestamp or not signature:
            return JSONResponse({"error": "Missing signature headers"}, status_code=401)

        try:
            ts = int(timestamp)
        except ValueError:
            return JSONResponse({"error": "Invalid timestamp"}, status_code=401)

        if abs(time.time() - ts) > MAX_AGE_SECONDS:
            return JSONResponse({"error": "Request expired"}, status_code=401)

        message = f"{timestamp}{request.method}{request.url.path}"
        expected = hmac.new(HMAC_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected):
            return JSONResponse({"error": "Invalid signature"}, status_code=401)

        return await call_next(request)
