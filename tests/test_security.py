"""Tests for HMAC request signing middleware."""

from __future__ import annotations

import hashlib
import hmac
import time
from unittest.mock import patch

from fastapi.testclient import TestClient


def _make_signature(secret: str, method: str, path: str, timestamp: int) -> str:
    message = f"{timestamp}{method}{path}"
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


@patch("api.security.HMAC_SECRET", "test-secret")
def test_valid_signature():
    from api import app

    client = TestClient(app, raise_server_exceptions=False)
    ts = int(time.time())
    sig = _make_signature("test-secret", "GET", "/api/trends", ts)
    resp = client.get("/api/trends", headers={"X-Timestamp": str(ts), "X-Signature": sig})
    assert resp.status_code != 401


@patch("api.security.HMAC_SECRET", "test-secret")
def test_invalid_signature():
    from api import app

    client = TestClient(app, raise_server_exceptions=False)
    ts = int(time.time())
    resp = client.get("/api/trends", headers={"X-Timestamp": str(ts), "X-Signature": "invalid"})
    assert resp.status_code == 401


@patch("api.security.HMAC_SECRET", "test-secret")
def test_expired_timestamp():
    from api import app

    client = TestClient(app, raise_server_exceptions=False)
    ts = int(time.time()) - 600  # 10 minutes ago
    sig = _make_signature("test-secret", "GET", "/api/trends", ts)
    resp = client.get("/api/trends", headers={"X-Timestamp": str(ts), "X-Signature": sig})
    assert resp.status_code == 401
