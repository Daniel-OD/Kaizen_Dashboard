from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
import os

app = FastAPI(title="Kaizen Dashboard API", version="1.1")

app.include_router(router, prefix="/api")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/", response_class=HTMLResponse)
def root():
    index_path = os.path.join(ROOT_DIR, "index.html")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()
    except:
        return "index.html not found"

    inject = '<script src="/static/bridge.js"></script>'

    if "</body>" in html:
        html = html.replace("</body>", inject + "\n</body>")
    else:
        html += inject

    return HTMLResponse(content=html)

@app.get("/health")
def health():
    return {"status": "ok"}
