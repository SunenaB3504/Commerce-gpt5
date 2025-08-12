from __future__ import annotations

from typing import Optional, Tuple, List, Dict
import os
import json
from functools import lru_cache


def _norm(s: str) -> str:
    import re
    return re.sub(r"\s+", " ", s.strip().lower())


def _project_root() -> str:
    # services/api/utils -> repo root
    here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def _external_curated_path() -> str:
    # Prefer docs/data/curated_qa.json
    root = _project_root()
    return os.path.join(root, "docs", "data", "curated_qa.json")


def _tokenize(s: str) -> List[str]:
    import re
    s = _norm(re.sub(r"[^a-z0-9\s]", " ", s.lower()))
    return [t for t in s.split() if t]


def _matches(q: str, cand_q: str, aliases: Optional[List[str]] = None) -> bool:
    qn = _norm(q)
    cn = _norm(cand_q)
    if cn == qn or cn in qn or qn in cn:
        return True
    # Check aliases
    for alt in (aliases or []):
        an = _norm(alt)
        if an == qn or an in qn or qn in an:
            return True
    # Token overlap heuristic: require that at least 60% of cand tokens appear in q
    c_tokens = _tokenize(cn)
    q_tokens = set(_tokenize(qn))
    if c_tokens:
        overlap = sum(1 for t in c_tokens if t in q_tokens) / max(len(c_tokens), 1)
        if overlap >= 0.6:
            return True
    # Alias token overlap
    for alt in (aliases or []):
        a_tokens = _tokenize(alt)
        if a_tokens:
            overlap = sum(1 for t in a_tokens if t in q_tokens) / max(len(a_tokens), 1)
            if overlap >= 0.6:
                return True
    return False


# Minimal curated bank for high-stakes prompts (exam-ready).
# Expand safely over time.
_CURATED: List[Dict[str, str]] = [
    {
        "subject": "Economics",
        "chapter": "3",
        "q": "ways a partner can retire from the firm",
        "a": (
            "Exam-ready: Ways a partner may retire (Indian Partnership Act, 1932)\n"
            "1) By consent of all partners (mutual agreement). [s.32(1)(a)]\n"
            "2) In accordance with the partnership deed, if it expressly permits retirement and conditions are fulfilled. [s.32(1)(b)]\n"
            "3) In a partnership at will, by giving written notice of intention to retire to all partners; retirement is effective from the date stated or the date of delivery. [s.32(1)(c) read with s.7]\n"
        ),
        # Optional static page hint anchored to the uploaded book extraction (approx pages 15–16 in our chunks for ch3)
        "pages": "p15-16",
    },
    {
        "subject": "Economics",
        "chapter": "3",
        "q": "modes of payment to a retiring partner",
        "aliases": "settlement of amount due to retiring partner; disposal of amount due to retiring partner; payment to retiring partner; settlement to retiring partner; settlement of the amount due to a retired partner",
        "a": (
            "Exam-ready: Modes of payment to a retiring partner\n"
            "1) Lump-sum settlement in cash/bank: Retiring Partner’s Capital A/c Dr → Bank/Cash\n"
            "2) Convert entire balance to loan: Retiring Partner’s Capital A/c Dr → Retiring Partner’s Loan A/c\n"
            "3) Part cash now, balance as loan: Retiring Partner’s Capital A/c Dr → Bank/Cash; Retiring Partner’s Loan A/c\n"
            "4) Instalments with interest on unpaid balance: Interest A/c Dr → Retiring Partner’s Loan A/c; then Retiring Partner’s Loan A/c Dr → Bank/Cash\n"
            "Note: Loan balance appears under liabilities until cleared. If payment is deferred without agreement, s.37 IPA allows either 6% p.a. interest or a share of profits attributable to the use of the outgoing partner’s capital."
        ),
        # Based on section 3.7 Disposal of Amount Due to Retiring Partner
        "pages": "p18-19",
    },
]


def _load_external_entries() -> List[Dict[str, str]]:
    path = _external_curated_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("entries") if isinstance(data, dict) else data
        out: List[Dict[str, str]] = []
        if isinstance(entries, list):
            for item in entries:
                if isinstance(item, dict) and item.get("q") and item.get("a"):
                    out.append(item)  # type: ignore[arg-type]
        return out
    except Exception:
        return []


@lru_cache(maxsize=1)
def _combined_entries_cache_key() -> str:
    # Use file mtime as a simple cache key; function body returns a string that changes when file changes
    path = _external_curated_path()
    try:
        mt = os.path.getmtime(path)
        return f"{path}:{mt}"
    except Exception:
        return f"{path}:na"


def _combined_entries() -> List[Dict[str, str]]:
    # lru_cache on a trivial function to allow cache invalidation when mtime changes
    _ = _combined_entries_cache_key()
    # Merge built-ins with external
    extern = _load_external_entries()
    return _CURATED + extern


def match_curated_answer(query: str, subject: Optional[str], chapter: Optional[str]) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    qn = _norm(query)
    subj = (subject or "").strip().lower()
    chap = (chapter or "").strip().lower()

    # Exact/substring/synonym match over curated entries (built-in + external) with optional subject/chapter filter
    for item in _combined_entries():
        if subj and item.get("subject", "").lower() and item["subject"].lower() != subj:
            continue
        if chap and item.get("chapter", "").lower() and item["chapter"].lower() != chap:
            continue
        cand_q_raw = item.get("q", "")
        cand_q = _norm(cand_q_raw)
        if not cand_q:
            continue
        aliases_field = item.get("aliases")
        aliases: List[str] = []
        if isinstance(aliases_field, list):
            aliases = [str(a) for a in aliases_field]
        elif isinstance(aliases_field, str):
            # support semicolon-separated string
            aliases = [a.strip() for a in aliases_field.split(";") if a.strip()]
        if _matches(qn, cand_q, aliases):
            ans = item.get("a", "").strip()
            cites: List[Dict[str, str]] = []
            pages = item.get("pages")
            if pages:
                cites.append({"page_hint": pages})
            return (ans, cites)
    return None
