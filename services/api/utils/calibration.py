from __future__ import annotations
"""Calibration utilities extracted from calibration script for reuse via API endpoints."""
from typing import List, Dict, Any
import statistics


def suggest_thresholds(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    buckets: Dict[str, List[float]] = {"correct": [], "partial": [], "incorrect": []}
    for r in rows:
        gl = r.get("gold_label") or r.get("label") or ""
        if gl in buckets:
            try:
                buckets[gl].append(float(r.get("score") or 0.0))
            except Exception:
                continue
    def safe_median(xs: List[float]) -> float:
        return statistics.median(xs) if xs else 0.0
    inc_med = safe_median(buckets["incorrect"]) or 0.0
    part_med = safe_median(buckets["partial"]) or 0.0
    corr_med = safe_median(buckets["correct"]) or 0.0
    part_q3 = statistics.quantiles(buckets["partial"], n=4)[2] if buckets["partial"] else part_med
    partial_min = round((inc_med + part_med) / 2, 1)
    correct_min = round((max(part_med, part_q3) + corr_med) / 2, 1)
    if correct_min - partial_min < 5:
        correct_min = min(100.0, partial_min + 5)
    return {
        "partial_min_suggested": partial_min,
        "correct_min_suggested": correct_min,
        "stats": {
            "incorrect_median": inc_med,
            "partial_median": part_med,
            "correct_median": corr_med,
            "partial_q3": part_q3,
        }
    }
