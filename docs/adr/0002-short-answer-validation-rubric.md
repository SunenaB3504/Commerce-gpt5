# ADR 0002: Short‑answer validation rubric and thresholds

Date: 2025-08-13
Status: Accepted

## Context
We’re introducing assessment for short answers. We need a transparent, deterministic v1 rubric that works with our extractive, citation-first approach, without adding heavy ML dependencies.

## Decision
Adopt a four-part rubric with fixed weights and clear thresholds, implemented in a new endpoint `POST /answer/validate`.

- Rubric weights (sum to 100):
  - Key point coverage: 50
  - Content similarity (TF‑IDF cosine): 25
  - Structure (fits question type): 15
  - Terminology (correct terms used): 10
- Score = 100 * (0.50 * coverage + 0.25 * cosine + 0.15 * structure + 0.10 * terminology)
- Thresholds:
  - Correct: score ≥ 80
  - Partial: 50 ≤ score < 80
  - Incorrect: score < 50

## Rationale
- Coverage emphasizes alignment with book-grounded key points.
- Cosine adds robustness to paraphrasing.
- Structure rewards definitions vs. lists appropriately with simple heuristics.
- Terminology nudges precise academic language without overfitting.

## Details
- Gold answer (key points):
  1) Prefer curated Q&A (subject/chapter scoped) and extract bullet/numbered lines as atomic points.
  2) Else, retrieve top passages via TF‑IDF and extract candidate sentences with token-overlap to form 5–10 points.
- Matching: A point is “covered” if lemmatized token overlap with the user answer ≥ 0.6.
- Citations: Use curated citations if present; otherwise derive 2–3 from top retrieval hits.
- Feedback:
  - List up to 5 missing points.
  - 3–5 feedback bullets (structure, terminology, off‑topic hints).
  - Recommendations map missing points → page anchors where possible.
- Edge constraints:
  - Very short answers (< 15 tokens) implicitly cap achievable score; feedback indicates insufficient detail.
  - Very long answers (> 250 tokens) get a small precision penalty under structure.

## Alternatives considered
- ROUGE‑L/BERTScore for similarity: heavier deps; less explainable for v1.
- LLM‑based grading: higher variance and infra cost; revisit after Sprint 02.

## Risks and mitigations
- False negatives for highly paraphrased answers → mitigate via cosine component and alias expansion in curated bank.
- Over‑rewarded verbosity → structure heuristic penalizes overlong free‑form responses.
- Domain drift → keep curated bank scoped by subject/chapter and review periodically.

## Rollout & testing
- Unit tests with 10 canonical Q&A per pilot chapter: good/partial/poor variants.
- Calibrate thresholds so good ≥ 85, partial ~60–75, poor ≤ 40.
- Log rubric breakdowns for dashboard; revisit weights if systematic bias observed.

## Implementation notes
- Endpoint: `POST /answer/validate { question, userAnswer, subject, chapter }` returns `{ result, score, rubric[], feedback[], missingPoints[], citations[], recommendations[] }`.
- Uses scikit‑learn TF‑IDF; no new heavy runtime deps.
- Voice mode: same endpoint, with on‑device STT; only text is sent to backend.

## References
- ADR‑0001 (Rename Ask→Doubts; add Practice)
- docs/srs.md (ASK, VOICE), docs/technical-design.md (HTTP API)
