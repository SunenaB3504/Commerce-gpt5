from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import json
from pathlib import Path


def _get_float(name: str, default: float, min_v: float | None = 0.0, max_v: float | None = 1.0) -> float:
    try:
        v = float(os.getenv(name, ""))
    except Exception:
        return default
    if min_v is not None:
        v = max(min_v, v)
    if max_v is not None:
        v = min(max_v, v)
    return v


@dataclass(frozen=True)
class ValidateScoringConfig:
    # Weights should sum to 1.0; we'll normalize just in case.
    w_coverage: float = 0.50
    w_cosine: float = 0.25
    w_structure: float = 0.15
    w_terminology: float = 0.10
    # Result thresholds in [0,100]
    correct_min: float = 80.0
    partial_min: float = 50.0
    # Matching thresholds
    coverage_point_overlap: float = 0.60  # token overlap to count a point as matched
    # Feedback triggers
    structure_min_hint: float = 0.50
    terminology_min_hint: float = 0.40
    off_topic_cosine_max: float = 0.30
    off_topic_coverage_max: float = 0.30


_VALIDATE_OVERRIDES: Dict[str, Any] = {}
_OVERRIDES_PATH = Path(__file__).resolve().parents[3] / "data" / "runtime" / "threshold_overrides.json"
_OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_overrides_from_disk() -> None:
    global _VALIDATE_OVERRIDES
    try:
        if _OVERRIDES_PATH.exists():
            data = json.loads(_OVERRIDES_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # only take numeric values we recognise
                out: Dict[str, Any] = {}
                for k in ("partial_min", "correct_min"):
                    if k in data:
                        try:
                            out[k] = float(data[k])
                        except Exception:
                            pass
                _VALIDATE_OVERRIDES.update(out)
    except Exception:
        pass


_load_overrides_from_disk()


def set_validate_overrides(partial_min: Optional[float] = None, correct_min: Optional[float] = None) -> Dict[str, Any]:
    if partial_min is not None:
        _VALIDATE_OVERRIDES["partial_min"] = max(0.0, min(float(partial_min), 100.0))
    if correct_min is not None:
        _VALIDATE_OVERRIDES["correct_min"] = max(0.0, min(float(correct_min), 100.0))
    # persist
    try:
        _OVERRIDES_PATH.write_text(json.dumps(_VALIDATE_OVERRIDES, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return dict(_VALIDATE_OVERRIDES)


def current_validate_overrides() -> Dict[str, Any]:
    return dict(_VALIDATE_OVERRIDES)


def load_validate_scoring_config() -> ValidateScoringConfig:
    # Load weights as [0,1]; normalize if needed
    w_cov = _get_float("VALIDATE_W_COVERAGE", 0.50, 0.0, 1.0)
    w_cos = _get_float("VALIDATE_W_COSINE", 0.25, 0.0, 1.0)
    w_str = _get_float("VALIDATE_W_STRUCTURE", 0.15, 0.0, 1.0)
    w_term = _get_float("VALIDATE_W_TERMINOLOGY", 0.10, 0.0, 1.0)
    total = w_cov + w_cos + w_str + w_term
    if total <= 0:
        w_cov, w_cos, w_str, w_term = 0.50, 0.25, 0.15, 0.10
        total = 1.0
    w_cov /= total
    w_cos /= total
    w_str /= total
    w_term /= total

    correct_min = _get_float("VALIDATE_CORRECT_MIN", 80.0, 0.0, 100.0)
    partial_min = _get_float("VALIDATE_PARTIAL_MIN", 50.0, 0.0, 100.0)

    overlap = _get_float("VALIDATE_COVERAGE_POINT_OVERLAP", 0.60, 0.0, 1.0)

    structure_min_hint = _get_float("VALIDATE_STRUCTURE_MIN_HINT", 0.50, 0.0, 1.0)
    terminology_min_hint = _get_float("VALIDATE_TERMINOLOGY_MIN_HINT", 0.40, 0.0, 1.0)
    off_topic_cosine_max = _get_float("VALIDATE_OFF_TOPIC_COSINE_MAX", 0.30, 0.0, 1.0)
    off_topic_coverage_max = _get_float("VALIDATE_OFF_TOPIC_COVERAGE_MAX", 0.30, 0.0, 1.0)

    cfg = ValidateScoringConfig(
        w_coverage=w_cov,
        w_cosine=w_cos,
        w_structure=w_str,
        w_terminology=w_term,
        correct_min=correct_min,
        partial_min=partial_min,
        coverage_point_overlap=overlap,
        structure_min_hint=structure_min_hint,
        terminology_min_hint=terminology_min_hint,
        off_topic_cosine_max=off_topic_cosine_max,
        off_topic_coverage_max=off_topic_coverage_max,
    )
    # Apply runtime overrides
    if _VALIDATE_OVERRIDES:
        correct_o = _VALIDATE_OVERRIDES.get("correct_min")
        partial_o = _VALIDATE_OVERRIDES.get("partial_min")
        if correct_o is not None or partial_o is not None:
            object.__setattr__(cfg, "correct_min", correct_o if correct_o is not None else cfg.correct_min)
            object.__setattr__(cfg, "partial_min", partial_o if partial_o is not None else cfg.partial_min)
    return cfg
