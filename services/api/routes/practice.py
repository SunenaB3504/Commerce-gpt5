from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from ..utils.practice_sessions import start_session, get_session, record_answer
from ..utils.mcq_store import get_mcq_by_id
from .validate import validate_short_answer, ShortAnswerRequest


router = APIRouter()


class PracticeStartRequest(BaseModel):
    subject: str = Field(..., min_length=2)
    chapter: str = Field(..., min_length=1)
    total: int = 6
    mcq: int = 3
    short: int = 3
    adaptive: bool = False


class PracticeQuestionResponse(BaseModel):
    sessionId: str
    index: int
    total: int
    type: str
    questionId: Optional[str] = None
    question: str
    options: Optional[List[str]] = None
    subject: str
    chapter: str
    adaptive: bool | None = None
    rationale: Optional[str] = None


class PracticeSubmitRequest(BaseModel):
    sessionId: str
    type: str  # 'mcq' | 'short'
    questionId: Optional[str] = None
    selectedIndex: Optional[int] = None  # for mcq
    answer: Optional[str] = None  # for short


@router.post("/practice/start", response_model=PracticeQuestionResponse)
def practice_start(req: PracticeStartRequest):
    sess = start_session(req.subject.strip(), req.chapter.strip(), total=req.total, mix=(req.mcq, req.short))
    q = sess.current()
    if not q:
        raise HTTPException(status_code=400, detail="No questions available")
    return PracticeQuestionResponse(
        sessionId=sess.session_id,
        index=sess.index,
        total=sess.total,
        type=q.qtype,
        questionId=(q.meta.get("mcq_id") if q.qtype == "mcq" else q.id),
        question=q.question,
        options=q.options if q.qtype == "mcq" else None,
        subject=sess.subject,
        chapter=sess.chapter,
        adaptive=req.adaptive or None,
        rationale=("adaptive placeholder rationale" if req.adaptive else None),
    )


@router.post("/practice/next", response_model=PracticeQuestionResponse)
def practice_next(payload: Dict[str, Any]):
    session_id = (payload or {}).get("sessionId")
    if not session_id:
        raise HTTPException(status_code=400, detail="sessionId is required")
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    q = sess.next()
    if not q:
        raise HTTPException(status_code=400, detail="No more questions")
    adaptive = (payload or {}).get("adaptive") or None
    return PracticeQuestionResponse(
        sessionId=sess.session_id,
        index=sess.index,
        total=sess.total,
        type=q.qtype,
        questionId=(q.meta.get("mcq_id") if q.qtype == "mcq" else q.id),
        question=q.question,
        options=q.options if q.qtype == "mcq" else None,
        subject=sess.subject,
        chapter=sess.chapter,
        adaptive=adaptive,
        rationale=("adaptive placeholder rationale" if adaptive else None),
    )


@router.post("/practice/submit")
def practice_submit(req: PracticeSubmitRequest):
    sess = get_session(req.sessionId)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    q = sess.current()
    if not q:
        raise HTTPException(status_code=400, detail="No active question")

    result: Dict[str, Any] = {"type": req.type}
    if req.type == "mcq":
        if not req.questionId:
            raise HTTPException(status_code=400, detail="questionId is required for MCQ")
        m = get_mcq_by_id(sess.subject, sess.chapter, req.questionId)
        if not m:
            raise HTTPException(status_code=404, detail="MCQ not found")
        sel = int(req.selectedIndex or 0)
        correct_index = int(m.get("answerIndex", -1))
        correct = (sel == correct_index)
        result.update({
            "result": "correct" if correct else "incorrect",
            "explanation": m.get("explanation"),
            "citations": m.get("citations") or [],
            "correctIndex": correct_index,
        })
    elif req.type == "short":
        ans = (req.answer or "").strip()
        if not ans:
            raise HTTPException(status_code=400, detail="answer is required for short type")
        vreq = ShortAnswerRequest(question=q.question, userAnswer=ans, subject=sess.subject, chapter=sess.chapter)
        vres = validate_short_answer(vreq)
        result.update({
            "result": vres.result,
            "score": vres.score,
            "rubric": [ri.model_dump() for ri in vres.rubric],
            "feedback": vres.feedback,
            "missingPoints": vres.missingPoints,
            "citations": vres.citations,
            "recommendations": vres.recommendations,
        })
    else:
        raise HTTPException(status_code=400, detail="Unknown type")

    record_answer(sess, req.questionId or q.id, result)

    has_next = (sess.index + 1) < sess.total
    return {"submission": result, "index": sess.index, "total": sess.total, "hasNext": has_next}
