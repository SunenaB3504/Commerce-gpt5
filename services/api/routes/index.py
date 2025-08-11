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

WEB_DATA_DIR = Path("web/data/subjects")


class IndexResponse(BaseModel):
    id: str
    namespace: str
    count: int
    subject: Optional[str] = None
    chapter: Optional[str] = None
    chunks_path: Optional[str] = None


router = APIRouter()


@router.post("/index", response_model=IndexResponse)
async def build_index(
    file: Optional[UploadFile] = File(None),
    path: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    chapter: Optional[str] = Form(None),
    chunk_size: int = Form(1200),
    chunk_overlap: int = Form(200),
    model: str = Form("all-MiniLM-L6-v2"),
):
    # Resolve source path
    source_path: Optional[Path] = None
    filename: Optional[str] = None
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

    # Parse pages
    try:
        pages_list: List[Tuple[int, str]] = extract_text(str(source_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parse failed: {e}")

    # Chunk
    chunks = chunk_pages(
        pages_list,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        subject=subject,
        chapter=chapter,
        filename=filename,
        source_path=str(source_path) if source_path else None,
    )

    # Persist chunks as JSON for the web app (optional but handy)
    chunks_path: Optional[str] = None
    if subject and chapter:
        safe_subject = subject.replace(" ", "_")
        safe_chapter = chapter.replace(" ", "_")
        target_dir = WEB_DATA_DIR / safe_subject / "chapters" / safe_chapter
        target_dir.mkdir(parents=True, exist_ok=True)
        # For now always write chunks-001.json
        chunks_file = target_dir / "chunks-001.json"
        # Minimal JSON schema: list of objects with text + metadata
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

    # Index via ChromaDB
    index = DiskIndex()
    try:
        res = index.upsert(chunks, subject=subject, chapter=chapter, model=model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index failed: {e}")

    return IndexResponse(
        id=str(uuid.uuid4()),
        namespace=res.get("namespace", ""),
        count=res.get("count", 0),
        subject=subject,
        chapter=chapter,
        chunks_path=chunks_path,
    )
