"""Calibration script for /answer/validate thresholds.

Usage (example):
  python scripts/calibrate_short_answer.py --subject Economics --chapter 1 --samples data/calibration/econ_ch1_samples.json

Sample JSON structure (list of objects):
[
  {"q": "what is inflation", "answers": [
      {"text": "Inflation is a rise in general price level over time reducing purchasing power", "label": "correct"},
      {"text": "Prices go up", "label": "partial"},
      {"text": "It is about GDP", "label": "incorrect"}
  ]}
]

The script will call the live API (or local uvicorn) for each answer and collect rubric scores, then
compute confusion matrices for various threshold candidates and suggest new partial/correct cutoffs.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from typing import List, Dict, Any, Tuple
import os
import math
import time
import urllib.parse
import http.client

DEFAULT_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8003")


def _post_json(base: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    from urllib.parse import urlparse
    import json as _json
    u = urlparse(base)
    conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=30)
    body = _json.dumps(payload)
    conn.request("POST", path, body=body, headers={"Content-Type": "application/json"})
    resp = conn.getresponse()
    data = resp.read().decode("utf-8", errors="replace")
    if resp.status >= 300:
        raise RuntimeError(f"HTTP {resp.status}: {data}")
    return json.loads(data)


def load_samples(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_scores(base: str, subject: str, chapter: str, samples_path: str) -> List[Dict[str, Any]]:
    samples = load_samples(samples_path)
    out: List[Dict[str, Any]] = []
    for item in samples:
        q = item["q"]
        for ans in item.get("answers", []):
            payload = {
                "question": q,
                "userAnswer": ans["text"],
                "subject": subject,
                "chapter": chapter,
                "retriever": "tfidf",
            }
            try:
                res = _post_json(base, "/answer/validate", payload)
            except Exception as e:
                print(f"WARN: request failed for '{q}' -> {e}", file=sys.stderr)
                continue
            out.append({
                "q": q,
                "gold_label": ans.get("label"),
                "answer": ans["text"],
                "score": res.get("score"),
                "result": res.get("result"),
                "rubric": res.get("rubric"),
            })
            time.sleep(0.05)
    return out


def suggest_thresholds(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Collect distributions by gold label
    buckets: Dict[str, List[float]] = {"correct": [], "partial": [], "incorrect": []}
    for r in rows:
        gl = r.get("gold_label") or ""
        if gl in buckets:
            buckets[gl].append(float(r.get("score") or 0.0))
    suggestions: Dict[str, Any] = {}
    # Basic heuristic: set partial_min halfway between median(incorrect) and median(partial),
    # and correct_min halfway between max(partial median, partial 75th) and median(correct).
    def safe_median(xs: List[float]) -> float:
        return statistics.median(xs) if xs else 0.0
    inc_med = safe_median(buckets["incorrect"]) or 0.0
    part_med = safe_median(buckets["partial"]) or 0.0
    corr_med = safe_median(buckets["correct"]) or 0.0
    part_q3 = statistics.quantiles(buckets["partial"], n=4)[2] if buckets["partial"] else part_med

    partial_min = round((inc_med + part_med) / 2, 1)
    correct_min = round((max(part_med, part_q3) + corr_med) / 2, 1)
    # Ensure ordering and reasonable spacing
    if correct_min - partial_min < 5:
        correct_min = min(100.0, partial_min + 5)
    suggestions["partial_min_suggested"] = partial_min
    suggestions["correct_min_suggested"] = correct_min
    suggestions["stats"] = {
        "incorrect_median": inc_med,
        "partial_median": part_med,
        "correct_median": corr_med,
        "partial_q3": part_q3,
    }
    return suggestions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--samples", required=True, help="Path to calibration samples JSON")
    ap.add_argument("--base", default=DEFAULT_BASE)
    args = ap.parse_args()

    rows = collect_scores(args.base, args.subject, args.chapter, args.samples)
    print(f"Collected {len(rows)} scored answers")
    if not rows:
        return
    sugg = suggest_thresholds(rows)
    print("\nSuggested thresholds (export as env vars):")
    print(f"  VALIDATE_PARTIAL_MIN={sugg['partial_min_suggested']}")
    print(f"  VALIDATE_CORRECT_MIN={sugg['correct_min_suggested']}")
    print("\nStats:")
    for k, v in sugg["stats"].items():
        print(f"  {k}: {v}")

    # Dump raw results
    out_path = "calibration_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "suggestions": sugg}, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {out_path}")

if __name__ == "__main__":
    main()
