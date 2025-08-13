from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

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


@router.post("/mcq/validate", response_model=MCQValidateResponse)
def mcq_validate(req: MCQValidateRequest):
    # Minimal stub: if correctIndex is provided, use it; else assume 0
    correct = int(req.correctIndex) if req.correctIndex is not None else 0
    result = "correct" if req.selectedIndex == correct else "incorrect"
    explanation = None
    if req.question and req.options:
        try:
            q = req.question.strip()
            # Provide a generic explanation placeholder
            explanation = f"The correct answer is option {correct + 1} based on the definition or concept referenced in the chapter."
        except Exception:
            explanation = None
    return MCQValidateResponse(result=result, correctIndex=correct, explanation=explanation, citations=[])
