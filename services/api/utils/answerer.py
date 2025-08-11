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
    """Extractive synthesis: pick salient sentences from top passages with citations.

    Returns (answer_text, citations[])
    citations: [{page_start, page_end, filename, source_path}]
    """
    if not passages:
        return ("No supporting passages found for this question.", [])

    q_terms = set(w.lower() for w in query.split())
    chosen: List[str] = []
    citations: List[Dict[str, Any]] = []
    added_pages = set()  # to dedupe citations

    for h in passages:
        text = h.get("text", "")
        meta = h.get("metadata", {}) or {}
        p_start = meta.get("page_start")
        p_end = meta.get("page_end")
        fname = meta.get("filename")
        src = meta.get("source_path")
        sent_list = _split_sentences(text)
        if not sent_list:
            continue
        # Rank sentences by overlap with query terms
        def s_score(s: str) -> float:
            st = set(s.lower().split())
            return len(q_terms & st) / (len(q_terms) or 1)

        sent_list.sort(key=s_score, reverse=True)
        # Take top 1-2 sentences per passage
        take = 2 if len(sent_list) > 1 else 1
        for s in sent_list[:take]:
            if len(" ".join(chosen) + " " + s) > max_chars:
                break
            chosen.append(s)
        key = (p_start, p_end, fname)
        if key not in added_pages:
            citations.append({
                "page_start": p_start,
                "page_end": p_end,
                "filename": fname,
                "source_path": src,
            })
            added_pages.add(key)
        if len(" ".join(chosen)) >= max_chars:
            break

    answer = " ".join(chosen).strip()
    if citations:
        # Append inline citation bracket at the end summarizing pages
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
