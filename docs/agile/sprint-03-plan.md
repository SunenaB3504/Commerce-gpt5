# Sprint 03 Plan (2 weeks)

Sprint Goal: Adaptive learning & operational robustness — deliver adaptive practice recommendations, automated calibration pipeline, improved retrieval performance, richer readiness analytics, and admin workflow polish.

## Objectives
1. Adaptive Practice: Personalize next questions based on prior performance (MCQ correctness & short-answer rubric gaps).
2. Automated Calibration: Ingest labeled sample answers, auto-compute threshold suggestions nightly, and surface diffs in dashboard.
3. Retrieval Performance & Quality: Reduce median /ask latency and improve hit@k & citation rates through indexing and ranking tuning.
4. Persistence & Reliability: Persist practice sessions & overrides across restarts and add lightweight health/report endpoints.
5. Readiness Analytics: Trend charts (hit@k, answer rate, citation rate), threshold change history, and run comparisons.
6. Admin UX: Add UI controls for reload, calibration run, threshold apply, and logs snapshot.

## User Stories
- US-020 Adaptive Question Selection (Carry-over enhancement)
  - As a learner, I want the system to prioritize questions covering my weak points so I can close gaps efficiently.
  - Acceptance:
    - After at least 5 answered questions, subsequent short-answer prompts prioritize top 2 missing key points aggregated.
    - MCQ selection biases toward topics where recent correctness < 60%.
    - Endpoint `/practice/start` accepts `adaptive=true` (default off initially) and logs rationale per question.

- US-021 Practice Session Persistence Upgrade
  - Persist sessions & answers to disk + restore on restart (already partial) plus background cleanup & size cap.
  - Acceptance: Sessions survive restart within TTL; file rotation if >5MB.

- US-022 Runtime Threshold Persistence
  - As an admin, I want threshold overrides to survive restart.
  - Acceptance: Overrides saved to `data/runtime/threshold_overrides.json`; on boot they load before env vars.

- US-023 Calibration Samples Ingestion
  - Upload labeled calibration samples via admin UI.
  - Acceptance: POST `/admin/calibration/samples` stores JSON; listing endpoint returns counts & last modified.

- US-024 Nightly Calibration Job
  - Scheduled (or manual trigger) job computes suggestions using stored samples and writes history record.
  - Acceptance: History file keeps last 5 runs with timestamp & suggested values.

- US-025 Threshold Diff Visualization
  - Dashboard shows current vs suggested vs previous values with sparkline.
  - Acceptance: Readiness page renders diff table; changes highlight > +/-5 point deltas.

- US-026 Retrieval Index Optimization
  - Benchmark and implement at least one improvement (stopword refinement, bigram weighting, or hybrid rerank).
  - Acceptance: Achieve ≥ +5 percentage point absolute improvement in hit@k on benchmark prompts OR ≥15% latency reduction.

- US-027 Latency & Metrics Endpoint
  - Expose `/metrics/runtime` with rolling averages (ask latency, validation latency, cache hit rate).
  - Acceptance: JSON includes last 50 requests aggregates per route.

- US-028 Trend & Comparison Analytics
  - Generate chart-ready datasets for eval runs (if ≥2 runs) and display simple SVG sparkline.
  - Acceptance: `/eval/summary` extended with trend arrays; UI sparkline renders.

- US-029 Admin UI Controls
  - Provide admin panel page with buttons: reload curated, reload stopwords, run eval, run calibration, apply suggestions, view logs tail.
  - Acceptance: All buttons gated by token; success/fail toasts.

- US-030 Voice Accessibility Enhancements
  - Add ARIA labels, keyboard shortcuts, and transcript export.
  - Acceptance: WCAG AA basics (labels, focus styles), export button generates downloadable text.

- US-031 Error Budget & Logging
  - Centralize structured logs with request IDs; expose last N errors endpoint.
  - Acceptance: `/admin/logs/errors` returns JSON array; each log has timestamp, route, summary.

## Day-by-Day (Indicative)
Day 1: Architecture & backlog refinement (adaptive algorithm design, calibration data schema, metrics hooks). Implement persistent threshold overrides (US-022).  
Day 2: Adaptive question selection core logic & flag (US-020 basic) + session persistence refinement (US-021).  
Day 3: Calibration samples ingestion endpoints & storage (US-023).  
Day 4: Nightly calibration job scaffold + history recording (manual trigger for now) (US-024).  
Day 5: Threshold diff visualization & readiness trend arrays (US-025 part, US-028 data).  
Day 6: Retrieval benchmarking harness + implement initial optimization (US-026).  
Day 7: Metrics endpoint (/metrics/runtime) & logging/error capture (US-027 + part of US-031).  
Day 8: Admin UI panel (US-029) + voice accessibility & transcript export (US-030).  
Day 9: Remaining analytics & sparkline UI (US-028 completion) + error logs endpoint (US-031).  
Day 10: Hardening, performance re-test, documentation, retro prep, stretch tasks.

## Success Metrics (Exit Criteria)
- Adaptive practice: ≥70% of post-adaptive questions target previously missed points (sampled sessions).
- Retrieval: Achieve either ≥5pp hit@k improvement (baseline vs end) OR 15% reduction in median /ask latency.
- Calibration: Nightly job produces suggestions; diff visible; at least one accepted change applied via UI.
- Persistence: Session & threshold override persistence verified across restart in tests.
- Readiness analytics: Trend sparkline visible for hit@k and citation_rate with ≥3 data points.
- Admin operations: All listed admin functions usable via UI without manual curl.

## Risks & Mitigation
- Adaptive overspecialization → random exploration ratio (epsilon 0.2) in question selection.
- Calibration data scarcity → allow mixing synthetic labeled answers with real samples (flagged).
- Retrieval optimization regression → keep baseline run JSON & enable side-by-side diff.
- Metrics overhead → ring buffer with O(1) append; avoid heavy locking.
- UI complexity on readiness page → progressive disclosure (tabs or collapsible sections).

## Stretch (If Time)
- Lightweight spaced repetition scoring.
- Embedding-based answer similarity reranker.
- Exportable learner progress report PDF.

## Definition of Done (Sprint 03)
- All core endpoints documented and covered by at least smoke tests.
- Admin UI includes calibration + eval + threshold management.
- Adaptive flag can be toggled; no crashes when off.
- Metrics endpoint consumed by readiness dashboard for latency display.
- Retrieval benchmark before/after numbers recorded in repo.

## Dependencies
- Existing eval prompts; may need additional prompts for retrieval tuning.
- Labeled calibration samples (initial small set required early in sprint).

## Open Questions
- Should adaptive selection incorporate difficulty rating? (Not yet—needs item metadata.)
- Persistence backend migration to SQLite? (Deferred unless JSON proves limiting.)

---
### Day 1 Progress (2025-08-14)
- Implemented threshold overrides persistence to `data/runtime/threshold_overrides.json` (US-022).
- Added metrics scaffold (`services/api/utils/metrics.py`) and instrumented `/ask` & `/answer/validate` latency collection.
- Added adaptive flag & rationale placeholder fields in Practice start/next responses (US-020 scaffold).
- Added tests for threshold persistence and metrics invocation.
- Next (Day 2 target): Implement adaptive selection algorithm (point-gap & MCQ correctness weighting) and session persistence refinement.

