from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Tuple
from pathlib import Path
import uuid
import json

from ..utils.pdf_parser import extract_text
from ..utils.chunker import chunk_pages
from ..utils.indexer import DiskIndex

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class UploadResponse(BaseModel):
    id: str
    filename: str
    path: str
    subject: Optional[str] = None
    chapter: Optional[str] = None
    auto_index: bool = False
    namespace: Optional[str] = None
    index_count: Optional[int] = None
    chunks_path: Optional[str] = None

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    chapter: Optional[str] = Form(None),
    auto_index: bool = Form(True),
    reset: bool = Form(False),
    chunk_size: int = Form(1200),
    chunk_overlap: int = Form(200),
    model: str = Form("all-MiniLM-L6-v2"),
):
    # Validate extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    uid = str(uuid.uuid4())
    out_path = UPLOAD_DIR / f"{uid}_{file.filename}"

    data = await file.read()
    with out_path.open("wb") as f:
        f.write(data)

    # Base response
    resp = UploadResponse(
        id=uid,
        filename=file.filename,
        path=str(out_path),
        subject=subject,
        chapter=chapter,
        auto_index=bool(auto_index),
    )

    # Optionally auto-index immediately
    if auto_index:
        try:
            # Parse PDF pages
            pages_list: List[Tuple[int, str]] = extract_text(str(out_path))
            # Chunk
            chunks = chunk_pages(
                pages_list,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                subject=subject,
                chapter=chapter,
                filename=file.filename,
                source_path=str(out_path),
            )
            # Persist chunks JSON to web for testing
            chunks_path: Optional[str] = None
            if subject and chapter:
                safe_subject = subject.replace(" ", "_")
                safe_chapter = chapter.replace(" ", "_")
                target_dir = Path("web/data/subjects") / safe_subject / "chapters" / safe_chapter
                target_dir.mkdir(parents=True, exist_ok=True)
                chunks_file = target_dir / "chunks-001.json"
                payload = [
                    {
                        "id": c.id,
                        "text": c.text,
                        "page_start": c.page_start,
                        "page_end": c.page_end,
                        "metadata": c.metadata,
                    }
                    for c in chunks
                ]
                with chunks_file.open("w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                chunks_path = str(chunks_file).replace("\\", "/")

            # Index
            index = DiskIndex()
            res = index.upsert(chunks, subject=subject, chapter=chapter, model=model, reset=reset)

            resp.namespace = res.get("namespace")
            resp.index_count = res.get("count")
            resp.chunks_path = chunks_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Auto-index failed: {e}")

    return resp
