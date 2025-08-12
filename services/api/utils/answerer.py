from __future__ import annotations

from typing import List, Dict, Any, Tuple


def _score_from_hit(hit: Dict[str, Any]) -> float:
    """Higher is better. If distance provided, convert to score; else basic length score."""
    d = hit.get("distance")
    if isinstance(d, (int, float)):
        return max(0.0, 1.0 - float(d))
    # Fallback heuristic: prefer longer chunks slightly
    t = hit.get("text", "")
    return min(len(t) / 1000.0, 1.0)


def _jaccard(a: str, b: str) -> float:
    as_ = set(a.lower().split())
    bs_ = set(b.lower().split())
    if not as_ or not bs_:
        return 0.0
    inter = len(as_ & bs_)
    uni = len(as_ | bs_)
    return inter / (uni or 1)


def select_passages_mmr(hits: List[Dict[str, Any]], max_passages: int = 5, lambda_mult: float = 0.7) -> List[Dict[str, Any]]:
    """Greedy MMR selection on plain text hits.

    - hits: list of {text, metadata, distance?}
    - returns: subset of hits with reduced redundancy
    """
    if not hits:
        return []
    # Sort by base relevance (score desc)
    candidates = sorted(hits, key=_score_from_hit, reverse=True)
    selected: List[Dict[str, Any]] = []
    while candidates and len(selected) < max_passages:
        if not selected:
            selected.append(candidates.pop(0))
            continue
        # Compute MMR for each candidate against selected
        mmr_scores: List[Tuple[float, int]] = []
        for i, h in enumerate(candidates):
            rel = _score_from_hit(h)
            max_sim = 0.0
            for s in selected:
                sim = _jaccard(h.get("text", ""), s.get("text", ""))
                if sim > max_sim:
                    max_sim = sim
            mmr = lambda_mult * rel - (1 - lambda_mult) * max_sim
            mmr_scores.append((mmr, i))
        mmr_scores.sort(key=lambda x: x[0], reverse=True)
        best_mmr, idx = mmr_scores[0]
        selected.append(candidates.pop(idx))
    return selected


def _split_sentences(text: str) -> List[str]:
    # Simple sentence splitter; avoids extra deps
    import re
    # Keep page newlines meaningful
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    out = [p.strip() for p in parts if p and p.strip()]
    return out


def synthesize_answer(query: str, passages: List[Dict[str, Any]], max_chars: int = 900) -> Tuple[str, List[Dict[str, Any]]]:
    """Extractive synthesis: globally rank clean sentences from top passages and attach citations.

    Returns (answer_text, citations[])
    citations: [{page_start, page_end, filename, source_path}]
    """
    if not passages:
        return ("No supporting passages found for this question.", [])

    import re
    q_terms = set(w.lower() for w in query.split())

    # Filters and bonuses
    interrogative_re = re.compile(r"\?$|^(what|why|how|when|where|who|name|explain|discuss|enumerate|give reasons|identify|prepare|compare)\b", re.I)
    exercise_re = re.compile(r"(exercise|work (these|this) out|short\s*answer|very\s*short|fill in|choose the correct|critically\s+appraise|match\s+the|state\s+whether|on\s+a\s+map\s+of\s+india)", re.I)
    heading_re = re.compile(r"^\d+(?:\.[\d]+)*\s+[A-Z][A-Z\s]+$")
    artifact_re = re.compile(r"\(cid:[^\)]+\)")
    motive_bonus_re = re.compile(r"(raw\s+material|supplier\s+of\s+raw|market\s+for\s+british\s+goods|market\s+for\s+british)", re.I)

    def is_noise_sentence(s: str) -> bool:
        s_clean = s.strip()
        if len(s_clean) < 5:
            return True
        if interrogative_re.search(s_clean) or exercise_re.search(s_clean):
            return True
        if heading_re.match(s_clean):
            return True
        letters = [ch for ch in s_clean if ch.isalpha()]
        if letters:
            upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
            if upper_ratio > 0.8 and len(letters) > 8:
                return True
        # Avoid overlong instruction-like lines
        if len(s_clean) > 300 and (";" in s_clean or ":" in s_clean):
            return True
        return False

    # Gather candidates across all passages
    candidates: List[Tuple[str, Dict[str, Any]]] = []
    for h in passages:
        text = artifact_re.sub(" ", h.get("text", ""))
        meta = h.get("metadata", {}) or {}
        for s in _split_sentences(text):
            s = s.strip()
            if not s:
                continue
            if is_noise_sentence(s):
                continue
            if len(s) > 260:
                continue
            candidates.append((s, meta))

    if not candidates:
        return ("No direct answer found in retrieved passages.", [])

    # Score and rank candidates
    def s_score(s: str) -> float:
        st = set(s.lower().split())
        overlap = len(q_terms & st) / (len(q_terms) or 1)
        declarative_bonus = 0.1 if s.endswith('.') else 0.0
        definitional_bonus = 0.0
        if re.match(r"^(what\s+is|define)\b", query.strip(), re.I):
            if re.search(r"\b(is|are|refers\s+to|means)\b", s, re.I):
                definitional_bonus = 0.2
        motive_bonus = 0.2 if motive_bonus_re.search(s) else 0.0
        return overlap + declarative_bonus + definitional_bonus + motive_bonus

    ranked = sorted(candidates, key=lambda t: s_score(t[0]), reverse=True)

    # Greedy selection with redundancy suppression
    def _norm(x: str) -> str:
        return re.sub(r"\s+", " ", x.strip().lower())

    chosen: List[Tuple[str, Dict[str, Any]]] = []
    for s, m in ranked:
        if len(" ".join([c[0] for c in chosen]) + " " + s) > max_chars:
            break
        s_n = _norm(s)
        if any(_norm(c[0]) == s_n for c in chosen):
            continue
        if any(_jaccard(c[0], s) > 0.75 for c in chosen):
            continue
        chosen.append((s, m))
        if len(chosen) >= 3 and len(" ".join([c[0] for c in chosen])) > max_chars * 0.6:
            break

    citations: List[Dict[str, Any]] = []
    added_pages = set()
    for _, meta in chosen:
        key = (meta.get("page_start"), meta.get("page_end"), meta.get("filename"))
        if key in added_pages:
            continue
        citations.append({
            "page_start": meta.get("page_start"),
            "page_end": meta.get("page_end"),
            "filename": meta.get("filename"),
            "source_path": meta.get("source_path"),
        })
        added_pages.add(key)

    answer = " ".join([c[0] for c in chosen]).strip()
    if citations:
        refs = [
            f"p{c.get('page_start')}-{c.get('page_end')}" if c.get('page_start') and c.get('page_end') else "p?"
            for c in citations
        ]
        tail = f" [Sources: {', '.join(refs)}]"
        if len(answer) + len(tail) <= max_chars + 100:
            answer += tail
    return (answer or "No direct answer found in retrieved passages.", citations)


def build_answer(query: str, hits: List[Dict[str, Any]], *, mmr: bool = True, max_passages: int = 5, max_chars: int = 900) -> Dict[str, Any]:
    """High-level helper that selects passages (optionally MMR) and synthesizes an answer."""
    if mmr:
        sel = select_passages_mmr(hits, max_passages=max_passages)
    else:
        sel = hits[:max_passages]
    text, cites = synthesize_answer(query, sel, max_chars=max_chars)
    return {"answer": text, "citations": cites, "selected": sel}
