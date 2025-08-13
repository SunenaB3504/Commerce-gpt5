from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

from ..utils.indexer import DiskIndex
from ..utils.curated_qa import match_curated_answer


router = APIRouter()


class TeachRequest(BaseModel):
    subject: str = Field(...)
    chapter: str = Field(...)
    topics: Optional[List[str]] = None
    depth: Optional[str] = Field("standard", description="basic|standard|deep")
    retriever: Optional[str] = Field("auto")
    k: Optional[int] = Field(10, ge=3, le=25)


class TeachSection(BaseModel):
    sectionId: str
    title: str
    bullets: List[str] = []
    pageAnchors: List[int] = []
    citations: List[Dict[str, Any]] = []


class TeachResponse(BaseModel):
    outline: List[TeachSection]
    glossary: List[Dict[str, Any]] = []
    readingList: List[Dict[str, Any]] = []
    coverage: Dict[str, Any] = {}
    meta: Dict[str, Any] = {}


def _load_required_topics(subject: Optional[str], chapter: Optional[str]) -> List[str]:
    """Load required topics from optional JSON file under docs/content/subjects/<s>/chapters/<c>/coverage.json.
    Falls back to empty list if not present.
    { "required": ["overview", "key terms", ...] }
    """
    try:
        s = (subject or "").replace(" ", "_")
        c = (chapter or "").replace(" ", "_")
        p = Path("docs/content/subjects") / s / "chapters" / c / "coverage.json"
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            req = data.get("required") if isinstance(data, dict) else None
            if isinstance(req, list):
                return [str(x).strip() for x in req if str(x).strip()]
    except Exception:
        pass
    return []


def _coverage_from_outline(required: List[str], outline: List[TeachSection]) -> Tuple[List[str], List[str]]:
    """Compute covered and gaps using simple case-insensitive substring match against
    section titles and bullets.
    """
    covered: List[str] = []
    gaps: List[str] = []
    # Gather searchable corpus
    corpus: List[str] = []
    for sec in outline:
        if sec.title:
            corpus.append(sec.title.lower())
        for b in sec.bullets or []:
            corpus.append(str(b).lower())
    for r in required:
        key = r.lower()
        hit = any(key in t for t in corpus)
        (covered if hit else gaps).append(r)
    return covered, gaps


def _collect_citations(hits: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    citations: List[Dict[str, Any]] = []
    added = set()
    for h in hits[: limit * 2]:
        m = h.get("metadata", {}) or {}
        key = (m.get("page_start"), m.get("page_end"), m.get("filename"))
        if key in added:
            continue
        citations.append(
            {
                "page_start": m.get("page_start"),
                "page_end": m.get("page_end"),
                "filename": m.get("filename"),
                "source_path": m.get("source_path"),
            }
        )
        added.add(key)
        if len(citations) >= limit:
            break
    return citations


def _split_sentences(text: str) -> List[str]:
    import re
    parts = re.split(r"(?<=[.!?])\s+|\n+", (text or "").strip())
    return [p.strip() for p in parts if p and p.strip()]


def _overview_bullets(hits: List[Dict[str, Any]], cap: int = 5) -> List[str]:
    bullets: List[str] = []
    for h in hits:
        t = (h.get("text") or "").strip()
        if not t:
            continue
        s = _split_sentences(t)
        if not s:
            continue
        first = s[0].strip()
        if first and first not in bullets:
            bullets.append(first if len(first) < 160 else first[:157] + "…")
        if len(bullets) >= cap:
            break
    return bullets


def _key_terms(hits: List[Dict[str, Any]], cap: int = 8) -> List[str]:
    import re
    stop = {"and", "or", "the", "of", "a", "an", "to", "in", "for", "on", "by", "with", "as"}
    terms: List[str] = []
    seen = set()
    # Count occurrences to rank later
    counts: Dict[str, int] = {}
    for h in hits:
        text = (h.get("text") or "").strip()
        for line in text.splitlines():
            # Pattern: Term: definition
            if ":" in line:
                left = line.split(":", 1)[0].strip()
                if 2 <= len(left.split()) <= 5 and left[0].isupper():
                    cand = re.sub(r"\s+", " ", left)
                    key = cand.lower()
                    counts[key] = counts.get(key, 0) + 2  # boost for defined terms
                    if key not in seen:
                        terms.append(cand)
                        seen.add(key)
        # Title-case sequences
        tokens = re.findall(r"[A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]{2,}){0,2}", text)
        for cand in tokens:
            words = [w.lower() for w in cand.split()]
            if any(w in stop for w in words):
                continue
            key = cand.lower()
            counts[key] = counts.get(key, 0) + 1
            if key not in seen:
                terms.append(cand)
                seen.add(key)
    # Rank terms by counts (desc) and by length (shorter first)
    ranked = sorted(terms, key=lambda t: (-counts.get(t.lower(), 0), len(t)))
    return ranked[:cap]


def _short_answers(hits: List[Dict[str, Any]], cap: int = 5) -> List[str]:
    import re
    out: List[str] = []
    seen = set()
    for h in hits:
        for s in _split_sentences(h.get("text", "")):
            if len(s.split()) > 24:
                continue
            if re.search(r"\b(is|are|refers\s+to|means)\b", s, re.I):
                cand = re.sub(r"\s+", " ", s).strip().rstrip(".;")
                key = cand.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(cand)
                if len(out) >= cap:
                    return out
    return out


def _long_answers(hits: List[Dict[str, Any]], cap: int = 3) -> List[str]:
    out: List[str] = []
    seen = set()
    for h in hits:
        for s in _split_sentences(h.get("text", "")):
            w = s.split()
            if 18 <= len(w) <= 40:
                cand = s.strip().rstrip(".;")
                key = cand.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(cand)
                if len(out) >= cap:
                    return out
    return out


def _formulae(hits: List[Dict[str, Any]], cap: int = 4) -> List[str]:
    import re
    out: List[str] = []
    seen = set()
    for h in hits:
        for line in (h.get("text", "") or "").splitlines():
            ln = line.strip()
            if not ln:
                continue
            if ("=" in ln or "%" in ln) and len(ln) <= 140:
                if re.search(r"[0-9%]", ln):
                    cand = re.sub(r"\s+", " ", ln)
                    key = cand.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(cand)
                    if len(out) >= cap:
                        return out
    return out


def _curated_points_for_topics(subject: Optional[str], chapter: Optional[str], topics: List[str], cap: int = 6) -> List[str]:
    # Use curated answers to extract bullet-like points for the given topics
    points: List[str] = []
    seen = set()
    import re
    for t in topics:
        try:
            m = match_curated_answer(t, subject, chapter)
        except Exception:
            m = None
        if not m:
            continue
        text, _ = m
        for line in (text or "").splitlines():
            s = line.strip()
            if not s:
                continue
            if re.match(r"^(?:[-•*]\s+|\d+[\.)]\s+)", s):
                s = re.sub(r"^(?:[-•*]\s+|\d+[\.)]\s+)", "", s).strip()
            # keep concise points
            if 3 <= len(s) <= 160:
                key = s.lower()
                if key in seen:
                    continue
                seen.add(key)
                points.append(s)
                if len(points) >= cap:
                    return points
        # fallback to sentences if no bullets
        if not points:
            for s in _split_sentences(text or ""):
                sc = s.strip()
                if 3 <= len(sc) <= 160:
                    key = sc.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    points.append(sc)
                    if len(points) >= cap:
                        return points
    return points


@router.post("/teach", response_model=TeachResponse)
def teach(req: TeachRequest):
    # Build a structured outline using simple extractive heuristics over retrieved chunks
    try:
        idx = DiskIndex()
        topics = req.topics or ["overview"]
        query = "; ".join(topics[:3])
        # First attempt with requested retriever (default auto)
        res = idx.query(
            subject=req.subject,
            chapter=req.chapter,
            query=query,
            k=int(req.k or 10),
            retriever=req.retriever or "auto",
        )
        # If no results (e.g., empty chroma collection), retry with BM25
        if not res.get("results"):
            res = idx.query(
                subject=req.subject,
                chapter=req.chapter,
                query=query,
                k=int(req.k or 10),
                retriever="bm25",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index query failed: {e}")

    hits = res.get("results", [])
    # Depth-based caps
    depth = (req.depth or "standard").lower()
    caps = {
        "basic": {"ov": 3, "terms": 5, "shorts": 3, "longs": 2, "forms": 2},
        "standard": {"ov": 5, "terms": 8, "shorts": 5, "longs": 3, "forms": 4},
        "deep": {"ov": 8, "terms": 12, "shorts": 8, "longs": 5, "forms": 6},
    }.get(depth, {"ov": 5, "terms": 8, "shorts": 5, "longs": 3, "forms": 4})
    # Overview (with curated fallback to ensure useful content)
    ov_bullets = _overview_bullets(hits, cap=caps["ov"]) 
    if len(ov_bullets) < max(2, caps["ov"] // 2):
        curated_pts = _curated_points_for_topics(req.subject, req.chapter, topics, cap=caps["ov"])
        # merge unique
        seen = set([b.lower() for b in ov_bullets])
        for p in curated_pts:
            if p.lower() not in seen:
                ov_bullets.append(p)
                seen.add(p.lower())
            if len(ov_bullets) >= caps["ov"]:
                break
    if not ov_bullets:
        ov_bullets = ["Outline will populate as content is indexed."]
    ov_cites = _collect_citations(hits, limit=5)
    overview = TeachSection(
        sectionId="overview",
        title=f"Chapter {req.chapter} overview",
        bullets=ov_bullets,
        pageAnchors=[c.get("page_start") for c in ov_cites if c.get("page_start")],
        citations=ov_cites,
    )

    # Key terms
    terms = _key_terms(hits, cap=caps["terms"])
    key_terms = TeachSection(
        sectionId="key-terms",
        title="Key terms",
        bullets=terms,
        pageAnchors=overview.pageAnchors,
        citations=ov_cites,
    )

    # Short answers (definitions)
    shorts = _short_answers(hits, cap=caps["shorts"]) 
    if len(shorts) < max(1, caps["shorts"] // 2):
        curated_pts = _curated_points_for_topics(req.subject, req.chapter, topics, cap=caps["shorts"]) 
        seen = set([s.lower() for s in shorts])
        for p in curated_pts:
            if p.lower() not in seen:
                shorts.append(p)
                seen.add(p.lower())
            if len(shorts) >= caps["shorts"]:
                break
    short_sec = TeachSection(
        sectionId="short-answers",
        title="Short answers (definitions)",
        bullets=shorts,
        pageAnchors=overview.pageAnchors,
        citations=ov_cites,
    )

    # Long answers (explanations)
    longs = _long_answers(hits, cap=caps["longs"])
    long_sec = TeachSection(
        sectionId="long-answers",
        title="Long answers (explanations)",
        bullets=longs,
        pageAnchors=overview.pageAnchors,
        citations=ov_cites,
    )

    # Formulae
    forms = _formulae(hits, cap=caps["forms"])
    formula_sec = TeachSection(
        sectionId="formulae",
        title="Formulae",
        bullets=forms,
        pageAnchors=overview.pageAnchors,
        citations=ov_cites,
    )

    outline = [overview, key_terms, short_sec, long_sec, formula_sec]
    # Build glossary with simple definitions when available
    glossary: List[Dict[str, Any]] = []
    # map term->definition (shortest seen right-hand side of Term: definition)
    defs: Dict[str, str] = {}
    for h in hits:
        text = (h.get("text") or "").strip()
        for line in text.splitlines():
            if ":" in line:
                left, right = line.split(":", 1)
                term = left.strip()
                definition = right.strip()
                k = term.lower()
                if k in [t.lower() for t in terms]:
                    prev = defs.get(k)
                    if prev is None or len(definition) < len(prev):
                        defs[k] = definition
    for t in terms:
        k = t.lower()
        glossary.append({"term": t, "definition": defs.get(k, "")})
    # Build reading list from citations across outline (unique, sorted)
    rl_items: List[Dict[str, Any]] = []
    seen_rl = set()
    for sec in outline:
        for c in sec.citations or []:
            page = c.get("page_start")
            fname = c.get("filename")
            if page is None:
                continue
            key = (int(page), fname or "")
            if key in seen_rl:
                continue
            seen_rl.add(key)
            rl_items.append({"page": int(page), "filename": fname})
    rl_items.sort(key=lambda x: (x.get("page", 0), x.get("filename") or ""))

    # Coverage: required from file or request topics
    required_topics = _load_required_topics(req.subject, req.chapter) or (req.topics or [])
    cov_covered, cov_gaps = _coverage_from_outline(required_topics, outline)

    resp = TeachResponse(
        outline=outline,
        glossary=glossary,
        readingList=rl_items,
        coverage={"requiredTopics": required_topics, "covered": cov_covered, "gaps": cov_gaps},
        meta={"retrieverUsed": req.retriever or "auto", "depth": depth},
    )
    return resp
