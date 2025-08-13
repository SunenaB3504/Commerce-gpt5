"""
QnA evaluation harness.

Runs a set of prompts against /ask and records metrics:
- hit@k (any of required 'must' tokens present in hits)
- answer presence
- citation presence
- answer length
- latency (ms)

Usage:
  python scripts/eval_qna.py --prompts docs/evaluation/prompts/econ_ch3_sample.json --k 5 --retriever bm25 --out docs/evaluation/results/econ_ch3_sample.json
"""
from __future__ import annotations

import argparse
import json
import time
from typing import List, Dict, Any
import requests
from pathlib import Path


def run_eval(base: str, prompts_path: str, k: int, retriever: str, out_path: str) -> Dict[str, Any]:
    prompts = json.loads(Path(prompts_path).read_text(encoding='utf-8'))
    rows: List[Dict[str, Any]] = []
    ok_hits = 0
    ok_ans = 0
    ok_cite = 0

    for p in prompts:
        q = p["q"]
        musts = [m.lower() for m in p.get("must", [])]
        subject = p.get("subject")
        chapter = p.get("chapter")
        t0 = time.perf_counter()
        r = requests.get(
            f"{base}/ask",
            params={"q": q, "subject": subject, "chapter": chapter, "k": k, "retriever": retriever},
            timeout=30,
        )
        dt_ms = int((time.perf_counter() - t0) * 1000)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        ans = (data.get("answer") or "").strip()
        cites = data.get("citations") or []

        hit_ok = any(any(m in (h.get("text", "").lower()) for m in musts) for h in results) if musts else len(results) > 0
        ans_ok = bool(ans)
        cite_ok = len(cites) > 0

        ok_hits += 1 if hit_ok else 0
        ok_ans += 1 if ans_ok else 0
        ok_cite += 1 if cite_ok else 0

        rows.append({
            "q": q,
            "hit": hit_ok,
            "answer": ans_ok,
            "citations": cite_ok,
            "answer_len": len(ans),
            "latency_ms": dt_ms,
            "k": k,
            "retriever": retriever,
        })

    summary = {
        "count": len(rows),
        "hit_at_k": ok_hits,
        "answers": ok_ans,
        "citations": ok_cite,
        "hit_rate": (ok_hits / len(rows)) if rows else 0.0,
        "answer_rate": (ok_ans / len(rows)) if rows else 0.0,
        "citation_rate": (ok_cite / len(rows)) if rows else 0.0,
    }

    out_dir = Path(out_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding='utf-8')
    return {"summary": summary, "rows": rows}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://localhost:8000')
    ap.add_argument('--prompts', required=True)
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--retriever', choices=['auto','tfidf','bm25','chroma'], default='bm25')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    res = run_eval(args.base, args.prompts, args.k, args.retriever, args.out)
    print(json.dumps(res["summary"], indent=2))
