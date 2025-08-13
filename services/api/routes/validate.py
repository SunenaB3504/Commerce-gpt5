from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from ..utils.indexer import DiskIndex
from ..utils.answerer import _split_sentences
from ..utils.curated_qa import match_curated_answer


router = APIRouter()


class ShortAnswerRequest(BaseModel):
    question: str = Field(..., min_length=3)
    userAnswer: str = Field(..., min_length=1)
    subject: Optional[str] = None
    chapter: Optional[str] = None
    k: int = 8
    retriever: str = "auto"


class RubricItem(BaseModel):
    name: str
    got: float
    max: float


class ShortAnswerResponse(BaseModel):
    result: str
    score: float
    rubric: List[RubricItem]
    feedback: List[str]
    missingPoints: List[str]
    citations: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


def _build_gold_points(question: str, subject: Optional[str], chapter: Optional[str]) -> Dict[str, Any]:
    # Prefer curated bank
    curated = match_curated_answer(question, subject, chapter)
    points: List[str] = []
    citations: List[Dict[str, Any]] = []
    if curated is not None:
        text, cites = curated
        # Extract numbered/bulleted lines as atomic points
        for ln in text.splitlines():
            s = ln.strip()
            if not s:
                continue
            if any(s.startswith(pfx) for pfx in ("- ", "• ", "1) ", "2) ", "3) ", "4) ", "5) ", "1. ", "2. ")):
                # strip leading bullet/index
                import re
                s = re.sub(r"^(?:[-•]\s+|\d+[\.)]\s+|\d+\)\s+)", "", s).strip()
                if s:
                    points.append(s)
        citations = cites or []
    # If curated missing or yielded no points, fallback to retrieval to form points
    if not points:
        idx = DiskIndex()
        res = idx.query(subject=subject, chapter=chapter, query=question, k=8, retriever="tfidf")
        hits = res.get("results", [])
        # Collect sentences with highest overlap to the question
        import re
        q_terms = set(re.split(r"\W+", question.lower()))
        candidates: List[str] = []
        meta_list: List[Dict[str, Any]] = []
        for h in hits:
            text = h.get("text", "")
            meta = h.get("metadata", {}) or {}
            for s in _split_sentences(text):
                s_clean = s.strip()
                if not s_clean or len(s_clean) < 6 or len(s_clean) > 180:
                    continue
                st = set(re.split(r"\W+", s_clean.lower()))
                overlap = len(q_terms & st) / max(len(q_terms) or 1, 1)
                if overlap >= 0.1:
                    candidates.append(s_clean)
                    meta_list.append(meta)
        # De-dup and cap ~10
        seen = set()
        picked: List[str] = []
        for s in candidates:
            key = s.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            picked.append(s)
            if len(picked) >= 10:
                break
        points = picked
        # Basic citations from top hits
        citations = []
        added = set()
        for h in hits[:3]:
            m = h.get("metadata", {}) or {}
            key = (m.get("page_start"), m.get("page_end"), m.get("filename"))
            if key in added:
                continue
            citations.append({
                "page_start": m.get("page_start"),
                "page_end": m.get("page_end"),
                "filename": m.get("filename"),
                "source_path": m.get("source_path"),
            })
            added.add(key)
    gold_text = " \n".join(points)
    return {"points": points, "citations": citations, "text": gold_text}


def _tfidf_cosine(a: str, b: str) -> float:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
        from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
        vec = TfidfVectorizer(max_features=2048, ngram_range=(1, 2), stop_words="english")
        X = vec.fit_transform([a, b])
        sim = float(cosine_similarity(X[0], X[1])[0, 0])
        return max(0.0, min(sim, 1.0))
    except Exception:
        return 0.0


def _structure_score(question: str, answer: str) -> float:
    import re
    q = question.strip().lower()
    a = answer.strip()
    # Simple heuristics: bullets/numbering → good for list/steps; concise definition → good for define/what is
    is_list_q = bool(re.search(r"\b(list|enumerate|state|steps|types|advantages|disadvantages|features)\b", q))
    has_bullets = bool(re.search(r"(^|\n)(?:[-•]|\d+[\.)])\s+", a))
    is_define_q = bool(re.match(r"\s*(what\s+is|define)\b", q))
    concise = len(a.split()) <= 80
    score = 0.0
    if is_list_q and has_bullets:
        score += 1.0
    if is_define_q and concise:
        score += 1.0
    # Normalize to [0,1] with simple cap
    return min(score, 1.0)


def _terminology_score(question: str, answer: str) -> float:
    import re
    q_terms = [t for t in re.split(r"\W+", question.lower()) if len(t) > 3]
    if not q_terms:
        return 0.0
    a = answer.lower()
    present = sum(1 for t in q_terms if t in a)
    return present / max(len(q_terms), 1)


@router.post("/answer/validate", response_model=ShortAnswerResponse)
def validate_short_answer(req: ShortAnswerRequest):
    q = req.question.strip()
    ua = req.userAnswer.strip()
    if not q or not ua:
        raise HTTPException(status_code=400, detail="question and userAnswer are required")

    gold = _build_gold_points(q, req.subject, req.chapter)
    points: List[str] = gold.get("points", [])
    gold_text: str = gold.get("text", "")

    # Coverage: match points by token overlap
    import re
    ua_tokens = set(re.split(r"\W+", ua.lower()))
    matched: List[str] = []
    missing: List[str] = []
    for p in points:
        p_tokens = set(re.split(r"\W+", p.lower()))
        if not p_tokens:
            continue
        overlap = len(ua_tokens & p_tokens) / max(len(p_tokens), 1)
        if overlap >= 0.6:
            matched.append(p)
        else:
            missing.append(p)
    coverage = (len(matched) / max(len(points), 1)) if points else 0.0

    cosine = _tfidf_cosine(ua, gold_text)
    structure = _structure_score(q, ua)
    terminology = _terminology_score(q, ua)

    score = 100.0 * (0.50 * coverage + 0.25 * cosine + 0.15 * structure + 0.10 * terminology)
    score = max(0.0, min(score, 100.0))

    if score >= 80.0:
        result = "correct"
    elif score >= 50.0:
        result = "partial"
    else:
        result = "incorrect"

    rubric = [
        RubricItem(name="Key point coverage", got=round(50 * coverage, 1), max=50),
        RubricItem(name="Content similarity", got=round(25 * cosine, 1), max=25),
        RubricItem(name="Structure", got=round(15 * structure, 1), max=15),
        RubricItem(name="Terminology", got=round(10 * terminology, 1), max=10),
    ]

    feedback: List[str] = []
    if result != "correct":
        if missing:
            feedback.append(f"You missed {min(3, len(missing))} key point(s).")
        if structure < 0.5:
            feedback.append("Improve structure: use bullets/numbering or be concise for definitions.")
        if terminology < 0.4:
            feedback.append("Use the correct terms from the chapter in your answer.")
        if cosine < 0.3 and coverage < 0.3:
            feedback.append("Your answer seems off-topic. Revisit the chapter section.")

    # Citations: use gold citations if any; else derive from retrieval on the question
    citations = gold.get("citations", [])
    if not citations:
        try:
            idx = DiskIndex()
            res = idx.query(subject=req.subject, chapter=req.chapter, query=q, k=5, retriever=req.retriever)
            hits = res.get("results", [])
            added = set()
            for h in hits[:3]:
                m = h.get("metadata", {}) or {}
                key = (m.get("page_start"), m.get("page_end"), m.get("filename"))
                if key in added:
                    continue
                citations.append({
                    "page_start": m.get("page_start"),
                    "page_end": m.get("page_end"),
                    "filename": m.get("filename"),
                    "source_path": m.get("source_path"),
                })
                added.add(key)
        except Exception:
            pass

    # Recommendations: map first two missing points to generic recommendations
    recommendations: List[Dict[str, Any]] = []
    for mp in missing[:2]:
        recommendations.append({"topic": mp, "pages": [c.get("page_start") for c in citations if c.get("page_start")]})

    return ShortAnswerResponse(
        result=result,
        score=round(score, 1),
        rubric=rubric,
        feedback=feedback,
        missingPoints=missing[:5],
        citations=citations,
        recommendations=recommendations,
    )
