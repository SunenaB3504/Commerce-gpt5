from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from typing import Dict, Any, List
from pathlib import Path
import json
import time
import subprocess
import sys
from pathlib import Path

ADMIN_TOKEN = None  # lazy loaded from env when needed


router = APIRouter()


@router.get("/eval/summary")
def eval_summary() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[3]  # repo root
    results_dir = root / "docs" / "evaluation" / "results"
    files: List[Dict[str, Any]] = []
    agg = {"count": 0, "hit_at_k": 0, "answers": 0, "citations": 0}
    for p in sorted(results_dir.glob("*.json")) if results_dir.exists() else []:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            s = data.get("summary", {})
            c = int(s.get("count") or 0)
            files.append({
                "file": p.name,
                "summary": s,
                "mtime": int(p.stat().st_mtime),
            })
            agg["count"] += c
            agg["hit_at_k"] += int(s.get("hit_at_k") or 0)
            agg["answers"] += int(s.get("answers") or 0)
            agg["citations"] += int(s.get("citations") or 0)
        except Exception:
            continue
    rate = lambda num, den: (num / den) if den else 0.0
    summary = {
        "total_questions": agg["count"],
        "hit_rate": rate(agg["hit_at_k"], agg["count"]),
        "answer_rate": rate(agg["answers"], agg["count"]),
        "citation_rate": rate(agg["citations"], agg["count"]),
        "files": files,
        "lastUpdated": int(time.time()),
    }
    return summary


@router.post("/eval/run")
def eval_run(
    admin_token: str | None = Header(default=None, alias="x-admin-token"),
    prompts: str | None = None,
    retriever: str = "bm25",
    k: int = 5,
) -> Dict[str, Any]:
    """Trigger the evaluation harness and return the new summary file content.

    Parameters:
      - prompts: relative path to prompts JSON (default: first JSON under docs/evaluation/prompts)
      - retriever: retrieval strategy (bm25|tfidf|chroma|auto)
      - k: top-k documents
    Security: requires x-admin-token header matching ADMIN_TOKEN env var if set.
    """
    import os
    global ADMIN_TOKEN
    if ADMIN_TOKEN is None:
        ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
    if ADMIN_TOKEN and admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="invalid admin token")

    root = Path(__file__).resolve().parents[3]
    prompts_dir = root / "docs" / "evaluation" / "prompts"
    if prompts:
        prompts_path = (root / prompts).resolve()
    else:
        # pick first *.json in prompts_dir
        cand = sorted(prompts_dir.glob("*.json"))
        if not cand:
            raise HTTPException(status_code=400, detail="No prompts JSON found")
        prompts_path = cand[0]

    results_dir = root / "docs" / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / f"run_{int(time.time())}.json"

    script = root / "scripts" / "eval_qna.py"
    if not script.exists():
        raise HTTPException(status_code=500, detail="eval script missing")

    # Execute the script as a subprocess for isolation
    cmd = [sys.executable, str(script), "--base", os.environ.get("API_BASE", "http://127.0.0.1:8003"), "--prompts", str(prompts_path), "--k", str(k), "--retriever", retriever, "--out", str(out_file)]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="evaluation timeout")
    if cp.returncode != 0:
        raise HTTPException(status_code=500, detail=f"eval failed: {cp.stderr.strip() or cp.stdout.strip()}")

    # Load produced file and also return aggregated summary
    try:
        produced = json.loads(out_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"cannot read results: {e}")
    return {"run": produced.get("summary"), "file": out_file.name, "eval_summary": eval_summary()}
