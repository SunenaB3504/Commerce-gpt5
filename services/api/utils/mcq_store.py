from __future__ import annotations

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import threading

_cache_lock = threading.Lock()
_mcq_cache: Dict[str, List[Dict[str, Any]]] = {}


def _key(subject: str, chapter: str) -> str:
    return f"{subject.lower().strip()}::{chapter.lower().strip()}"


def load_mcqs(subject: str, chapter: str) -> List[Dict[str, Any]]:
    """Load MCQs from data/mcq/<subject>/<chapter>.json and cache them."""
    subj = subject.lower().replace(" ", "-")
    chap = str(chapter).lower()
    p = Path("data/mcq") / subj / f"{chap}.json"
    k = _key(subj, chap)
    with _cache_lock:
        if k in _mcq_cache:
            return _mcq_cache[k]
        if not p.exists():
            _mcq_cache[k] = []
            return []
        try:
            items = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(items, list):
                items = []
        except Exception:
            items = []
        _mcq_cache[k] = items
        return items


def get_mcqs(subject: str, chapter: str) -> List[Dict[str, Any]]:
    return load_mcqs(subject, chapter)


def get_mcq_by_id(subject: str, chapter: str, qid: str) -> Optional[Dict[str, Any]]:
    for item in load_mcqs(subject, chapter):
        if str(item.get("id")) == str(qid):
            return item
    return None
