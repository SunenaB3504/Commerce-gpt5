from fastapi import APIRouter
from ..utils.metrics import export_all

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/runtime")
def get_runtime_metrics():
    return export_all()
