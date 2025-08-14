# Sprint 02 plan (2 weeks)

Sprint goal: Learning flows and validation — “Teach me v1”, MCQ + Short-answer validation, Practice (Ask me assessment) with basic voice.

Scope (stories)
- US-005 Teach me v1 (overview + sources)
- US-006 MCQ validation and feedback
- US-010 Readiness dashboard (initial)
- US-007 Short-answer validation (rubric scoring + feedback)
- US-008 Practice session flow (assessment mode; Option A)
- US-009 Voice mode for Practice (STT/TTS in browser)

Deliverables
- Backend: /teach (subject/chapter), /mcq/validate, /answer/validate, /practice/start|next|submit
- Frontend: Teach page (chapter outline), Practice page (assessment: MCQ + short-answer)
- Voice: In-browser STT/TTS for Practice (Chrome-family first); audio stays on-device
- UX rename (Option A): current “Ask” → “Doubts”, “Practice” = assessment
- Eval: hit@k, citation presence, latency dashboard (basic)

Risks
- Hallucination risk in teach synthesis — constrain to citations
- MCQ ground truth quality — curate and version
- Short-answer scoring fairness — calibrate thresholds with samples
- Voice STT variance across browsers — default to manual input fallback

Definition of Done
- Teach returns structured outline with citations
- MCQ validation returns correct/incorrect with explanation and source
- Eval dashboard shows metrics for sample chapters
- Short-answer validator returns rubric, score, citations, and recommendations
- Practice flow supports MCQ and short-answer (text); voice available on supported browsers

## Day-by-day plan (10 working days)

- Day 1: Kickoff and scaffolding — Completed (2025-08-13)
	- Define contracts for /teach and /mcq/validate (request/response schemas).
	- Create stubs for routes, service utilities, and minimal tests.
	- Draft data shapes for Teach outline sections and MCQ store.
	- Apply Option A UX rename: “Ask” → “Doubts”; add “Practice” entry point in nav.
	- Done: Implemented POST /answer/validate (short-answer rubric), added POST /teach and POST /mcq/validate stubs, registered routers, added Practice page link, updated schema docs, and added tests. All tests passing.

- Day 2: Teach me v1 — extractive outline
	- Completed (2025-08-13)
	- Done: Implemented outline synthesis using retrieval with depth-based caps (basic/standard/deep).
	- Done: Sections shipped — overview, key terms, short answers, long answers, formulae; with citations and page anchors.
	- Done: Glossary extraction from “Term: definition” patterns; glossary highlighting in UI.
	- Done: Curated fallback to supplement overview and short answers when retrieval is sparse.
	- Done: Teach page in PWA with depth selector, per-section show/hide citations, page badges, copy/print actions, and print stylesheet.
	- Done: Tests updated for outline structure, citations, glossary key presence, and depth-cap behavior.

- Day 3: Teach me v1 — coverage and UI
	- Completed (2025-08-13)
	- Done: Backend computes coverage (required vs covered/gaps) using docs/content/subjects/<subject>/chapters/<chapter>/coverage.json when present, with fallback to request topics.
	- Done: readingList aggregated from citations across sections, de-duplicated by (page, filename) and sorted.
	- Done: Teach UI shows coverage summary and a lightweight loading skeleton.

- Day 4: MCQ ingestion and schema
	- Completed (2025-08-13)
	- Done: MCQ schema and store added (JSON at data/mcq/<subject>/<chapter>.json; fields id, question, options, answerIndex, explanation, citations).
	- Done: Utilities to load MCQs and query by id; in-memory cache with file-backed source.
	- Done: Seeded Economics chapter 1 MCQs and added unit tests for ingestion and /mcq/validate using store.

- Day 5: MCQ validation API and UX
	- Completed (2025-08-13)
	- Done: Added POST /mcq/get to fetch question/options by id (no answer leak) and enhanced /mcq/validate to use store.
	- Done: Practice UI wired to load question/options and validate answer; shows result, explanation, and sources.
	- Done: Tests for /mcq/get and /mcq/validate (correct and incorrect paths) passing.

- Day 6: Eval harness
	- Completed (2025-08-13)
	- Done: Added QnA eval script (scripts/eval_qna.py) to compute hit@k, answer/citation rates, answer length, latency; writes JSON results.
	- Done: Seed prompts at docs/evaluation/prompts/econ_ch3_sample.json and documented usage in docs/evaluation/test-plan.md.
	- Note: Threshold refinement for /answer/validate can be iterated after collecting sample outputs.

- Day 7: Practice sessions (text) + Readiness dashboard (initial)
	- Completed (2025-08-13)
	- Done: Implemented /practice/start, /practice/next, /practice/submit with an in-memory session store (subject/chapter mix; MCQ + short-answer). 
	- Done: Practice UI wired for sessions — question card, MCQ options or short-answer textarea, submit/next flow, and feedback rendering. Fixed submit bug (radio selection + feedback element) and cache-busted script.
	- Done: Added /eval/summary to aggregate evaluation JSON; created Readiness page to display headline metrics and file list.
	- Done: Added smoke script scripts/smoke-day7.ps1 to exercise Practice and Readiness endpoints.

- Day 8: Voice mode for Practice + Admin hot-reload — Completed (2025-08-13)
	- Done: Practice voice mode (beta) — Web Speech API recognition and speechSynthesis; commands: repeat/again, next/skip, option A–D, submit; short-answer dictation via “answer …”.
	- Done: Added transcript box and “Use as answer” to review and insert captured speech.
	- Done: Admin endpoints — POST /admin/reload/curated, /admin/reload/stopwords, and /admin/reload/all with optional x-admin-token (env ADMIN_TOKEN). Stopwords reload clears TF‑IDF caches.
	- Done: Seeded short-answer curated entries for Economics Chapter 1 to ensure mixed MCQ/short sessions.

- Day 9: Content scaling and perf pass
	- Completed (2025-08-14)
	- Done: Expanded curated Q&A (Economics Ch1 + new Ch2 concepts: GDP, nominal vs real, demand law, determinants, shifts) to improve short-answer coverage.
	- Done: Extended domain stopwords to down-rank instructional noise and generic verbs.
	- Done: Added calibration script scripts/calibrate_short_answer.py to analyze scored answers and suggest threshold env vars.
	- Done: Added in-memory TF-IDF similarity cache in /answer/validate to reduce repeated vectorizations.
	- Done: Added smoke-day9-validate.ps1 for quick /answer/validate health (good vs partial answer).
	- Pending (future): deeper retrieval perf profiling & session persistence.

- Day 10: Demo prep and retro — Completed (2025-08-14)
	- Added practice session persistence (JSON with 6h TTL) so sessions survive restarts.
	- Added POST /eval/run to trigger evaluation harness and update readiness metrics on demand.
	- Added calibration API: POST /admin/calibration/short-answer (suggest thresholds from scored rows) + runtime threshold override endpoints GET/POST /admin/validate/thresholds.
	- Enhanced readiness dashboard: run eval button, refresh, thresholds panel, suggestion & apply workflow (placeholder rows for now).
	- Implemented live threshold overrides without restart (in-memory) layered over env defaults.
	- Voice UX polish: auto-stop after 5s silence, live word count during dictation.
	- Added tests for persistence, threshold override, and eval run endpoint (with subprocess mock).
	- Updated documentation (this plan) to reflect Day 10 scope & completion; pending README additions for new admin endpoints.
	- Prepared for Sprint 02 demo: evaluation can be triggered in UI; runtime calibration pipeline sketched.
