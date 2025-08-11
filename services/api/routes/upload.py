from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class UploadResponse(BaseModel):
    id: str
    filename: str
    path: str
    subject: Optional[str] = None
    chapter: Optional[str] = None

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    chapter: Optional[str] = Form(None),
):
    # Validate extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    uid = str(uuid.uuid4())
    out_path = UPLOAD_DIR / f"{uid}_{file.filename}"

    data = await file.read()
    with out_path.open("wb") as f:
        f.write(data)

    return UploadResponse(
        id=uid,
        filename=file.filename,
        path=str(out_path),
        subject=subject,
        chapter=chapter,
    )
