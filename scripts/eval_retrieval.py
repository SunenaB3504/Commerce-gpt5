"""
Simple retrieval evaluation script.

Runs a small set of q,a expectations against the local API (default http://localhost:8000)
and reports whether top-k contains expected key phrases and whether an answer is returned.

Usage:
  python scripts/eval_retrieval.py --k 5 --retriever auto --subject Economics --chapter 3
"""
from __future__ import annotations

import argparse
import requests
from typing import List, Dict


def expectations_economics_ch3() -> List[Dict[str, str]]:
    return [
        {
            "q": "Ways a partner can retire from the firm",
            "must": "with consent",
        },
        {
            "q": "Modes of payment to a retiring partner",
            "must": "lump sum",
        },
        {
            "q": "What is sacrificing ratio",
            "must": "sacrificing ratio",
        },
        {
            "q": "Why do we prepare revaluation account",
            "must": "assets and liabilities",
        },
    ]


def run_eval(base: str, subject: str | None, chapter: str | None, k: int, retriever: str) -> None:
    tests = []
    if (subject or "").lower().startswith("econ") and (chapter or "") in {"3", "03", "ch3", "chapter3"}:
        tests = expectations_economics_ch3()
    else:
        print("No canned tests for this subject/chapter; running empty set.")

    ok_hits = 0
    ok_ans = 0
    total = len(tests)
    for t in tests:
        q = t["q"]
        must = t["must"]
        try:
            r = requests.get(
                f"{base}/ask",
                params={
                    "q": q,
                    "subject": subject,
                    "chapter": chapter,
                    "k": k,
                    "retriever": retriever,
                },
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Request failed for '{q}': {e}")
            continue
        # Check hits contain must
        results = data.get("results", [])
        if any(must.lower() in (h.get("text", "").lower()) for h in results):
            ok_hits += 1
        # Check answer present
        ans = (data.get("answer") or "").strip()
        if ans:
            ok_ans += 1
        print(f"- {q}: hits={len(results)} answer={'Y' if ans else 'N'}")

    if total:
        print(f"\nSummary: hit@{k} containing 'must'={ok_hits}/{total} | answers={ok_ans}/{total}")
    else:
        print("No tests executed.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000", help="API base URL")
    ap.add_argument("--subject", default="Economics")
    ap.add_argument("--chapter", default="3")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--retriever", choices=["auto", "tfidf", "bm25", "chroma"], default="auto")
    args = ap.parse_args()

    run_eval(args.base, args.subject, args.chapter, args.k, args.retriever)
