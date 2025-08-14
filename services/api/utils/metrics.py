from __future__ import annotations

import time
import threading
from typing import Dict, List, Any

_LOCK = threading.Lock()
_MAX = 200  # ring buffer size per metric
_DATA: Dict[str, List[Dict[str, Any]]] = {}


def record(metric: str, ms: float, extra: Dict[str, Any] | None = None) -> None:
    row = {"t": int(time.time()), "ms": float(ms)}
    if extra:
        row.update(extra)
    with _LOCK:
        buf = _DATA.setdefault(metric, [])
        buf.append(row)
        if len(buf) > _MAX:
            del buf[: len(buf) - _MAX]


def summary(metric: str) -> Dict[str, Any]:
    with _LOCK:
        buf = list(_DATA.get(metric, []))
    if not buf:
        return {"count": 0, "p50": 0, "p95": 0, "avg": 0}
    values = [r["ms"] for r in buf]
    values_sorted = sorted(values)
    def pct(p: float) -> float:
        if not values_sorted:
            return 0.0
        k = int(round((p / 100.0) * (len(values_sorted) - 1)))
        return values_sorted[k]
    avg = sum(values) / len(values)
    return {"count": len(values), "p50": pct(50), "p95": pct(95), "avg": avg}


def export_all() -> Dict[str, Any]:
    return {k: summary(k) for k in _DATA.keys()}
