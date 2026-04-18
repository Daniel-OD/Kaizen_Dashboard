"""Configuration for Microsoft Entra ID authentication.

All secrets are read from environment variables — nothing is hardcoded.
"""

from __future__ import annotations

import os


def _csv(val: str) -> list[str]:
    """Split a comma-separated env var into a cleaned list."""
    return [v.strip().lower() for v in val.split(",") if v.strip()]


# ── Microsoft Entra ID / OIDC ────────────────────────────────────────────────

ENTRA_CLIENT_ID: str = os.environ.get("ENTRA_CLIENT_ID", "")
ENTRA_CLIENT_SECRET: str = os.environ.get("ENTRA_CLIENT_SECRET", "")
ENTRA_TENANT_ID: str = os.environ.get("ENTRA_TENANT_ID", "")
ENTRA_REDIRECT_URI: str = os.environ.get("ENTRA_REDIRECT_URI", "")

# Microsoft identity-platform endpoints
AUTHORITY: str = f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}" if ENTRA_TENANT_ID else ""

# ── Session ──────────────────────────────────────────────────────────────────

SESSION_SECRET_KEY: str = os.environ.get("SESSION_SECRET_KEY", "")

# ── Domain / tenant restriction ──────────────────────────────────────────────

ALLOWED_EMAIL_DOMAINS: list[str] = _csv(
    os.environ.get("ALLOWED_EMAIL_DOMAINS", "eon.com,delgaz-grid.ro")
)

ALLOWED_TENANT_IDS: list[str] = _csv(
    os.environ.get("ALLOWED_TENANT_IDS", ENTRA_TENANT_ID if ENTRA_TENANT_ID else "")
)

# ── Feature flag ─────────────────────────────────────────────────────────────
# SSO is disabled — the dashboard is served without Microsoft Entra ID login.
# The legacy frontend-only password gate remains as the only access control.

SSO_ENABLED: bool = False
