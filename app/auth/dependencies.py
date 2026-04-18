"""FastAPI dependencies for authentication.

Usage in routes::

    @app.get("/protected")
    def protected(user: dict = Depends(require_user)):
        ...
"""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from app.auth.config import SSO_ENABLED
from app.auth.session import cookie_name, read_session_cookie


def get_current_user(request: Request) -> dict | None:
    """Return the authenticated user dict or ``None``."""
    if not SSO_ENABLED:
        return None  # SSO disabled — no user context
    cookie_val = request.cookies.get(cookie_name())
    return read_session_cookie(cookie_val)


def require_user(request: Request) -> dict:
    """Dependency that ensures the request comes from an authenticated user.

    When SSO is disabled the dependency is a no-op (returns a stub user).
    When SSO is enabled, API requests get 401 and browser requests get 401
    (the page-level routes handle redirects themselves).
    """
    if not SSO_ENABLED:
        return {"name": "Local User", "email": "local@dev", "tid": "", "oid": ""}

    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
