from fastapi import APIRouter, Depends, UploadFile
from app.api.schemas import CalculateRequest, CalculateResponse
from app.core.calculations import compute_dashboard
from app.services.excel_import import parse_excel
from app.auth.dependencies import require_user

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/calculate", response_model=CalculateResponse)
def calculate(payload: CalculateRequest, user: dict = Depends(require_user)) -> dict:
    return compute_dashboard(payload.model_dump())


@router.post("/import-excel")
async def import_excel(file: UploadFile, user: dict = Depends(require_user)) -> list[dict]:
    data = await file.read()
    return parse_excel(data)
