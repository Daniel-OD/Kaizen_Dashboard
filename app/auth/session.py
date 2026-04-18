"""Lightweight server-side session backed by a signed cookie.

We keep the session small (user claims only) so it fits comfortably in a
cookie without needing a server-side store.  ``itsdangerous`` handles
signing / expiry.
"""

from __future__ import annotations

import json
import time
from typing import Any

from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.auth.config import SESSION_SECRET_KEY

_COOKIE_NAME = "kz_session"
_MAX_AGE = 8 * 3600  # 8 hours

_serializer: URLSafeTimedSerializer | None = None


def _get_serializer() -> URLSafeTimedSerializer:
    global _serializer
    if _serializer is None:
        key = SESSION_SECRET_KEY
        if not key:
            # Import here to avoid circular dependency at module level
            from app.auth.config import SSO_ENABLED
            if SSO_ENABLED:
                raise RuntimeError(
                    "SESSION_SECRET_KEY must be set when SSO is enabled. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            key = "dev-fallback-key-not-for-production"
        _serializer = URLSafeTimedSerializer(key)
    return _serializer


# ── Write ────────────────────────────────────────────────────────────────────

def build_session_cookie(user: dict) -> tuple[str, str, int]:
    """Return ``(cookie_name, cookie_value, max_age)``."""
    payload = json.dumps(user, separators=(",", ":"))
    signed = _get_serializer().dumps(payload)
    return _COOKIE_NAME, signed, _MAX_AGE


# ── Read ─────────────────────────────────────────────────────────────────────

def read_session_cookie(cookie_value: str | None) -> dict | None:
    """Decode and verify the session cookie.  Returns user dict or None."""
    if not cookie_value:
        return None
    try:
        payload: str = _get_serializer().loads(cookie_value, max_age=_MAX_AGE)
        return json.loads(payload)
    except (BadSignature, json.JSONDecodeError, Exception):
        return None


# ── Cookie name accessor ─────────────────────────────────────────────────────

def cookie_name() -> str:
    return _COOKIE_NAME
