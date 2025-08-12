from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Tuple
from pathlib import Path
import uuid

from ..utils.pdf_parser import extract_text

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class PageText(BaseModel):
    page: int
    text: str

class ParseResponse(BaseModel):
    id: str
    filename: str
    pages: List[PageText]
    subject: Optional[str] = None
    chapter: Optional[str] = None

router = APIRouter()

@router.post("/parse", response_model=ParseResponse)
async def parse_pdf(
    file: Optional[UploadFile] = File(None),
    path: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    chapter: Optional[str] = Form(None),
    ocr: bool = Form(False, description="Enable OCR fallback for low-text pages"),
):
    # Input contract: either provide a PDF file or path to an uploaded file
    source_path: Optional[Path] = None
    filename = None

    if file is not None:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        uid = str(uuid.uuid4())
        source_path = UPLOAD_DIR / f"{uid}_{file.filename}"
        data = await file.read()
        with source_path.open("wb") as f:
            f.write(data)
        filename = file.filename
    elif path:
        source_path = Path(path)
        if not source_path.exists():
            raise HTTPException(status_code=404, detail="Provided path does not exist")
        filename = source_path.name
    else:
        raise HTTPException(status_code=400, detail="Provide either a file or a path")

    try:
        pages_list: List[Tuple[int, str]] = extract_text(str(source_path), ocr=ocr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parse failed: {e}")

    pages = [PageText(page=p, text=t) for p, t in pages_list]
    return ParseResponse(id=str(uuid.uuid4()), filename=filename, pages=pages, subject=subject, chapter=chapter)
