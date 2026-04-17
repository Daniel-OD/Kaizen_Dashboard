from fastapi import APIRouter, UploadFile
from app.api.schemas import CalculateRequest, CalculateResponse
from app.core.calculations import compute_dashboard
from app.services.excel_import import parse_excel

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/calculate", response_model=CalculateResponse)
def calculate(payload: CalculateRequest) -> dict:
    return compute_dashboard(payload.model_dump())


@router.post("/import-excel")
async def import_excel(file: UploadFile) -> list[dict]:
    data = await file.read()
    return parse_excel(data)
