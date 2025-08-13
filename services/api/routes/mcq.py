from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from services.api.utils.mcq_store import get_mcq_by_id

router = APIRouter()


class MCQValidateRequest(BaseModel):
    questionId: Optional[str] = None
    question: Optional[str] = None
    options: Optional[List[str]] = None
    correctIndex: Optional[int] = Field(None, ge=0)
    selectedIndex: int = Field(..., ge=0)
    subject: Optional[str] = None
    chapter: Optional[str] = None


class MCQValidateResponse(BaseModel):
    result: str
    correctIndex: int
    explanation: Optional[str] = None
    citations: List[Dict[str, Any]] = []


class MCQGetRequest(BaseModel):
    subject: str
    chapter: str
    questionId: str


class MCQGetResponse(BaseModel):
    id: str
    question: str
    options: List[str]
    citations: List[Dict[str, Any]] = []


@router.post("/mcq/validate", response_model=MCQValidateResponse)
def mcq_validate(req: MCQValidateRequest):
    # Use store if questionId provided and subject/chapter present
    correct = None
    explanation = None
    citations: List[Dict[str, Any]] = []
    if req.questionId and req.subject and req.chapter:
        item = get_mcq_by_id(req.subject, req.chapter, req.questionId)
        if item:
            try:
                correct = int(item.get("answerIndex"))
            except Exception:
                correct = None
            explanation = item.get("explanation")
            if isinstance(item.get("citations"), list):
                citations = item.get("citations")
    # Fallback to provided correctIndex or default 0
    if correct is None:
        correct = int(req.correctIndex) if req.correctIndex is not None else 0
    result = "correct" if req.selectedIndex == correct else "incorrect"
    if req.question and req.options:
        try:
            q = req.question.strip()
            # Provide a generic explanation placeholder
            if not explanation:
                explanation = f"The correct answer is option {correct + 1} based on the definition or concept referenced in the chapter."
        except Exception:
            explanation = None
    return MCQValidateResponse(result=result, correctIndex=correct, explanation=explanation, citations=citations)


@router.post("/mcq/get", response_model=MCQGetResponse)
def mcq_get(req: MCQGetRequest):
    item = get_mcq_by_id(req.subject, req.chapter, req.questionId)
    if not item:
        # Return a minimal placeholder so UI can handle gracefully
        return MCQGetResponse(id=req.questionId, question="Not found", options=[], citations=[])
    return MCQGetResponse(
        id=str(item.get("id")),
        question=str(item.get("question", "")),
        options=list(item.get("options", [])),
        citations=list(item.get("citations", [])) if isinstance(item.get("citations"), list) else [],
    )
