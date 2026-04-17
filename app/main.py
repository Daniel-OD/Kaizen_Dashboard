import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

app = FastAPI(title="Kaizen Dashboard API", version="2.0")
app.include_router(router, prefix="/api")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
STATIC_DIR = os.path.join(APP_DIR, "static")
INDEX_PATH = os.path.join(PROJECT_ROOT, "index.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def render_dashboard_html() -> HTMLResponse:
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

    return HTMLResponse(content=html)


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    return render_dashboard_html()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "index_exists": os.path.exists(INDEX_PATH),
    }


@app.get("/{full_path:path}", response_class=HTMLResponse)
def spa_fallback(full_path: str) -> HTMLResponse:
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not Found")
    return render_dashboard_html()
