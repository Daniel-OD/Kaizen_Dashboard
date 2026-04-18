"""Kaizen Dashboard — FastAPI application entry point.

When Microsoft Entra ID SSO is configured (environment variables set) the app
uses server-side OIDC authentication.  Otherwise it falls back to the legacy
frontend-only password gate so that local development keeps working.
"""

import os
import secrets
import html as html_mod

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.auth.config import (
    ALLOWED_EMAIL_DOMAINS,
    ALLOWED_TENANT_IDS,
    SSO_ENABLED,
)
from app.auth.dependencies import get_current_user, require_user
from app.auth.session import build_session_cookie, cookie_name

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(title="Kaizen Dashboard API", version="2.0")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
STATIC_DIR = os.path.join(APP_DIR, "static")
INDEX_PATH = os.path.join(PROJECT_ROOT, "index.html")
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def _read_template(name: str, replacements: dict[str, str] | None = None) -> str:
    path = os.path.join(TEMPLATES_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for key, val in (replacements or {}).items():
        content = content.replace(key, val)
    return content


def render_dashboard_html(user: dict | None = None) -> HTMLResponse:
    if not os.path.exists(INDEX_PATH):
        raise HTTPException(status_code=500, detail=f"index.html not found at {INDEX_PATH}")

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Inject runtime fixes (clean approach instead of backend patching)
    inject = '<script src="/static/runtime-fixes.js"></script>'
    if inject not in html:
        if "</body>" in html:
            html = html.replace("</body>", inject + "\n</body>")
        else:
            html += inject

    # Inject bridge.js to connect frontend with Python API
    bridge = '<script src="/static/bridge.js"></script>'
    if bridge not in html:
        if "</body>" in html:
            html = html.replace("</body>", bridge + "\n</body>")
        else:
            html += bridge

    # When SSO is active, inject a small script that exposes the user identity
    # and hides the legacy password gate immediately.
    if SSO_ENABLED and user:
        import json as json_mod
        user_json = json_mod.dumps({"name": user.get("name", ""), "email": user.get("email", "")})
        user_script = (
            "<script>"
            "window.__ssoUser=" + user_json + ";"
            # Hide legacy login overlay
            "(function(){var el=document.getElementById('kzLogin');if(el)el.style.display='none';}());"
            "</script>"
        )
        if "</body>" in html:
            html = html.replace("</body>", user_script + "\n</body>")
        else:
            html += user_script

    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# Auth routes (only active when SSO_ENABLED)
# ---------------------------------------------------------------------------

@app.get("/login")
def login(request: Request):
    """Redirect to Microsoft sign-in."""
    if not SSO_ENABLED:
        return RedirectResponse("/")
    from app.auth.entra import get_auth_url
    state = secrets.token_urlsafe(32)
    url = get_auth_url(state=state)
    resp = RedirectResponse(url)
    # Store state in a short-lived cookie for CSRF validation
    resp.set_cookie(
        "_auth_state", state,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=600,
    )
    return resp


@app.get("/auth/callback")
def auth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    """Handle the redirect back from Microsoft after sign-in."""
    if not SSO_ENABLED:
        return RedirectResponse("/")

    if error:
        return HTMLResponse(f"<h3>Authentication error</h3><p>{html_mod.escape(error)}</p>", status_code=400)

    # Validate state (CSRF)
    expected_state = request.cookies.get("_auth_state", "")
    if not expected_state or state != expected_state:
        return HTMLResponse("<h3>Invalid auth state — please try again.</h3>", status_code=400)

    from app.auth.entra import exchange_code
    result = exchange_code(code)

    if "error" in result:
        detail = result.get("error_description", result.get("error", "unknown"))
        return HTMLResponse(f"<h3>Token error</h3><p>{html_mod.escape(str(detail))}</p>", status_code=400)

    claims = result.get("id_token_claims", {})

    email = (
        claims.get("preferred_username")
        or claims.get("email")
        or claims.get("upn")
        or ""
    )
    tid = claims.get("tid", "")
    name = claims.get("name", email)
    oid = claims.get("oid", "")

    # ── Tenant restriction ────────────────────────────────────────────────
    if ALLOWED_TENANT_IDS and tid.lower() not in ALLOWED_TENANT_IDS:
        return HTMLResponse(
            _read_template("access_denied.html", {
                "{{EMAIL}}": html_mod.escape(email),
                "{{DOMAINS}}": ", ".join(ALLOWED_EMAIL_DOMAINS),
            }),
            status_code=403,
        )

    # ── Email domain restriction ──────────────────────────────────────────
    domain = email.rsplit("@", 1)[-1].lower() if "@" in email else ""
    if ALLOWED_EMAIL_DOMAINS and domain not in ALLOWED_EMAIL_DOMAINS:
        return HTMLResponse(
            _read_template("access_denied.html", {
                "{{EMAIL}}": html_mod.escape(email),
                "{{DOMAINS}}": ", ".join(ALLOWED_EMAIL_DOMAINS),
            }),
            status_code=403,
        )

    # ── Build session cookie ──────────────────────────────────────────────
    user = {"name": name, "email": email, "tid": tid, "oid": oid}
    c_name, c_value, c_max_age = build_session_cookie(user)

    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(
        c_name, c_value,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=c_max_age,
        path="/",
    )
    resp.delete_cookie("_auth_state")
    return resp


@app.get("/logout")
def logout():
    resp = RedirectResponse("/login" if SSO_ENABLED else "/")
    resp.delete_cookie(cookie_name(), path="/")
    return resp


@app.get("/me")
def me(request: Request):
    """Return the current user as JSON (for frontend identity display)."""
    user = get_current_user(request)
    if user:
        return {"name": user.get("name"), "email": user.get("email")}
    if SSO_ENABLED:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"name": "Local User", "email": "local@dev"}


# ---------------------------------------------------------------------------
# Protected routes
# ---------------------------------------------------------------------------

# API router — protect /api/calculate and /api/import-excel
# but keep /api/health open
app.include_router(router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    if SSO_ENABLED:
        user = get_current_user(request)
        if not user:
            return RedirectResponse("/login")
        return render_dashboard_html(user)
    return render_dashboard_html()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": app.version,
        "sso_enabled": SSO_ENABLED,
        "index_exists": os.path.exists(INDEX_PATH),
        "static_exists": os.path.isdir(STATIC_DIR),
    }


@app.get("/{full_path:path}", response_class=HTMLResponse)
def spa_fallback(full_path: str, request: Request):
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not Found")
    if SSO_ENABLED:
        user = get_current_user(request)
        if not user:
            return RedirectResponse("/login")
        return render_dashboard_html(user)
    return render_dashboard_html()

