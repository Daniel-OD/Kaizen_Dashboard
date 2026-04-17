from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Kaizen Dashboard API", version="1.0")

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Kaizen Dashboard API running"}
