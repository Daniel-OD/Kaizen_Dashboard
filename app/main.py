import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

app = FastAPI(title="Kaizen Dashboard API", version="1.3")
app.include_router(router, prefix="/api")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
STATIC_DIR = os.path.join(APP_DIR, "static")
INDEX_PATH = os.path.join(PROJECT_ROOT, "index.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def patch_broken_login_logo(html: str) -> str:
    replacement = (
        '<div class="kzLogo">'
        '<div style="display:flex;align-items:center;justify-content:center;gap:10px;'
        'height:60px;padding:0 12px;border-radius:12px;background:linear-gradient(135deg,#eff6ff,#dbeafe);'
        'border:1px solid rgba(37,99,235,.15);color:#1d4ed8;font-weight:700;font-size:18px;">'
        '<span style="display:inline-flex;width:14px;height:14px;border-radius:4px;background:#1d4ed8;"></span>'
        '<span>Delgaz Grid</span>'
        '</div>'
        '</div>'
    )

    html = html.replace(
        '<div class="kzLogo"><img src="data:image/png;base64,[truncated due to size]" alt="Delgaz Grid"></div>',
        replacement,
    )

    html = re.sub(
        r'<div class="kzLogo">\s*<img[^>]*src="data:image/png;base64,[^"]*"[^>]*>\s*</div>',
        replacement,
        html,
        count=1,
    )
    return html


def render_dashboard_html() -> HTMLResponse:
    if not os.path.exists(INDEX_PATH):
        raise HTTPException(status_code=500, detail=f"index.html not found at {INDEX_PATH}")

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    html = patch_broken_login_logo(html)

    inject = '<script src="/static/bridge.js"></script>'
    if inject not in html:
        if "</body>" in html:
            html = html.replace("</body>", inject + "\n</body>")
        else:
            html += inject

    return HTMLResponse(content=html)


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    return render_dashboard_html()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "index_exists": os.path.exists(INDEX_PATH),
        "index_path": INDEX_PATH,
        "static_path": STATIC_DIR,
    }


@app.get("/{full_path:path}", response_class=HTMLResponse)
def spa_fallback(full_path: str) -> HTMLResponse:
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not Found")
    return render_dashboard_html()
