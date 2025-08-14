from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
from ..utils.calibration import suggest_thresholds
from ..utils.config import set_validate_overrides, current_validate_overrides, load_validate_scoring_config


router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(request: Request) -> None:
    token = os.environ.get("ADMIN_TOKEN", "").strip()
    if token:
        provided = request.headers.get("x-admin-token", "").strip()
        if provided != token:
            raise HTTPException(status_code=403, detail="Forbidden: invalid admin token")


@router.post("/reload/curated")
def reload_curated(request: Request) -> Dict[str, Any]:
    """Reload curated Q&A cache by invalidating the LRU key and warming it."""
    _require_admin(request)
    from ..utils import curated_qa as cq
    try:
        # Invalidate cache and warm it
        try:
            cq._combined_entries_cache_key.cache_clear()  # type: ignore[attr-defined]
        except Exception:
            pass
        entries = cq._combined_entries()
        return {"status": "ok", "curated_count": len(entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"reload_curated_failed: {e}")


@router.post("/reload/stopwords")
def reload_stopwords(request: Request) -> Dict[str, Any]:
    """Clear TF-IDF caches so updated stopwords take effect next query."""
    _require_admin(request)
    from ..utils import indexer
    try:
        cleared = indexer.clear_tfidf_cache(None)
        return {"status": "ok", "cleared_namespaces": cleared}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"reload_stopwords_failed: {e}")


@router.post("/reload/all")
def reload_all(request: Request) -> Dict[str, Any]:
    _require_admin(request)
    out1 = reload_curated(request)
    out2 = reload_stopwords(request)
    return {"status": "ok", **out1, **out2}

@router.post("/calibration/short-answer")
def calibration_short_answer(payload: dict, request: Request):
    _require_admin(request)
    rows = payload.get("rows") or []  # Expect client to supply scored rows with gold_label + score
    if not isinstance(rows, list) or not rows:
        raise HTTPException(status_code=400, detail="rows list required")
    sugg = suggest_thresholds(rows)
    return {"suggestions": sugg, "count": len(rows)}


@router.get("/validate/thresholds")
def get_validate_thresholds(request: Request) -> Dict[str, Any]:
    _require_admin(request)
    cfg = load_validate_scoring_config()
    return {
        "partial_min": cfg.partial_min,
        "correct_min": cfg.correct_min,
        "overrides": current_validate_overrides(),
    }


@router.post("/validate/thresholds")
def update_validate_thresholds(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    _require_admin(request)
    partial_min = payload.get("partial_min")
    correct_min = payload.get("correct_min")
    if partial_min is None and correct_min is None:
        raise HTTPException(status_code=400, detail="partial_min or correct_min required")
    ov = set_validate_overrides(partial_min=partial_min, correct_min=correct_min)
    cfg = load_validate_scoring_config()
    return {
        "status": "ok",
        "applied": ov,
        "effective": {"partial_min": cfg.partial_min, "correct_min": cfg.correct_min},
    }
