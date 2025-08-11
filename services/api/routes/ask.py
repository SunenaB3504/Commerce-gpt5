from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from ..utils.indexer import DiskIndex
from ..utils.answerer import build_answer


class AskHit(BaseModel):
    text: str
    metadata: Dict[str, Any]
    distance: Optional[float] = None


class AskResponse(BaseModel):
    namespace: str
    results: List[AskHit]
    answer: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None


router = APIRouter()


@router.get("/ask", response_model=AskResponse)
async def ask(
    q: str = Query(..., description="User question/query text"),
    subject: Optional[str] = Query(None),
    chapter: Optional[str] = Query(None),
    k: int = Query(5, ge=1, le=20),
    model: str = Query("all-MiniLM-L6-v2"),
    answer_synthesis: bool = Query(True, description="Whether to synthesize an answer from top passages"),
):
    index = DiskIndex()
    try:
        res = index.query(subject=subject, chapter=chapter, query=q, k=k, model=model)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")
    hits_dicts = res.get("results", [])
    hits = [AskHit(**r) for r in hits_dicts]
    out = AskResponse(namespace=res.get("namespace", ""), results=hits)
    if answer_synthesis and hits_dicts:
        built = build_answer(q, hits_dicts, mmr=True, max_passages=min(5, k), max_chars=900)
        out.answer = built.get("answer")
        out.citations = built.get("citations")
    return out


# Optional streaming endpoint (text/event-stream). This is a best-effort simple stream.
from fastapi.responses import StreamingResponse


@router.get("/ask/stream")
async def ask_stream(
    q: str = Query(...),
    subject: Optional[str] = Query(None),
    chapter: Optional[str] = Query(None),
    k: int = Query(5, ge=1, le=20),
    model: str = Query("all-MiniLM-L6-v2"),
):
    index = DiskIndex()
    try:
        res = index.query(subject=subject, chapter=chapter, query=q, k=k, model=model)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

    hits = res.get("results", [])
    built = build_answer(q, hits, mmr=True, max_passages=min(5, k), max_chars=900)

    async def event_gen():
        import json
        # Send header event
        header = {"type": "meta", "namespace": res.get("namespace", ""), "k": k}
        yield f"data: {json.dumps(header)}\n\n"
        # Stream selected passages
        for h in built.get("selected", []):
            yield f"data: {json.dumps({"type": "passage", "text": h.get('text', ''), "metadata": h.get('metadata', {})})}\n\n"
        # Stream final answer
        yield f"data: {json.dumps({"type": "answer", "text": built.get('answer', ''), "citations": built.get('citations', [])})}\n\n"
        # End
        yield "event: end\n data: {}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")
