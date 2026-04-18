"""MSAL helpers for the Microsoft Entra ID authorization-code flow."""

from __future__ import annotations

import msal

from app.auth.config import AUTHORITY, ENTRA_CLIENT_ID, ENTRA_CLIENT_SECRET, ENTRA_REDIRECT_URI

# Scopes: openid + profile + email give us an id_token with the claims we need.
_SCOPES: list[str] = ["openid", "profile", "email"]


def _build_app() -> msal.ConfidentialClientApplication:
    """Create a new MSAL ConfidentialClientApplication."""
    return msal.ConfidentialClientApplication(
        client_id=ENTRA_CLIENT_ID,
        client_credential=ENTRA_CLIENT_SECRET,
        authority=AUTHORITY,
    )


def get_auth_url(state: str) -> str:
    """Return the Microsoft sign-in URL the browser should be redirected to."""
    app = _build_app()
    result = app.get_authorization_request_url(
        scopes=_SCOPES,
        state=state,
        redirect_uri=ENTRA_REDIRECT_URI,
    )
    return result


def exchange_code(code: str) -> dict:
    """Exchange the authorization code for tokens.

    Returns the full MSAL result dict which contains ``id_token_claims``.
    """
    app = _build_app()
    return app.acquire_token_by_authorization_code(
        code=code,
        scopes=_SCOPES,
        redirect_uri=ENTRA_REDIRECT_URI,
    )
