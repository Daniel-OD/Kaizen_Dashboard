from fastapi import APIRouter, UploadFile
from app.core.calculations import compute_dashboard
from app.services.excel_import import parse_excel

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/calculate")
def calculate(payload: dict):
    return compute_dashboard(payload)

@router.post("/import-excel")
async def import_excel(file: UploadFile):
    data = await file.read()
    return parse_excel(data)
