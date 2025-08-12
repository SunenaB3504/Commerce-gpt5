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

- Day 1: Kickoff and scaffolding
	- Define contracts for /teach and /mcq/validate (request/response schemas).
	- Create stubs for routes, service utilities, and minimal tests.
	- Draft data shapes for Teach outline sections and MCQ store.
	- Apply Option A UX rename: “Ask” → “Doubts”; add “Practice” entry point in nav.

- Day 2: Teach me v1 — extractive outline
	- Implement outline synthesis using existing retrieval + curated fallback.
	- Sections: key terms, short answers, long answers, formulae, page anchors.
	- Unit tests for outline structure and citation presence.

- Day 3: Teach me v1 — coverage and UI
	- Hook coverage matrix (docs/content) to ensure required sections present.
	- Build a simple Teach page in the PWA that calls /teach and renders sections.
	- Add loading/error states; verify on mobile.

- Day 4: MCQ ingestion and schema
	- Define MCQ schema (question, options A–D, correct, explanation, sources).
	- Implement parser for MCQs from existing markdown/JSON content.
	- Seed a small MCQ set per chapter; add unit tests for parsing.

- Day 5: MCQ validation API and UX
	- Implement /mcq/validate (checks selected option, returns result + explanation + citations).
	- Add a minimal UI form to submit MCQ and visualize feedback.
	- E2E test covering happy/negative cases.

- Day 6: Eval harness
	- Extend eval scripts for hit@k, citation presence, answer length, latency.
	- Add a small YAML/JSON suite of test prompts per chapter.
	- Store results to JSON; summarize in console and docs.
	- Implement /answer/validate (short-answer) with rubric scoring (coverage, cosine, structure, terminology) and unit tests.

- Day 7: Practice sessions (text) + Readiness dashboard (initial)
	- Implement /practice/start|next|submit with in-memory session store (subject/chapter/topic filters).
	- Practice UI: question card, MCQ selector or short-answer textarea, feedback view.
	- Backend route to serve aggregated eval metrics; basic web dashboard (table/cards) and link to rerun eval.

- Day 8: Voice mode for Practice + Admin hot-reload
	- Voice: integrate Web Speech API (STT) and SpeechSynthesis (TTS) with Practice UI; commands (repeat/next/skip/A–D/stop); captions.
	- Admin hot-reload: endpoints to reload curated Q&A and stopwords; developer-only toggle in PWA; unit tests for reload behavior.

- Day 9: Content scaling and perf pass
	- Expand curated entries for top chapters (batch import from docs/data).
	- Calibrate short-answer thresholds with sample answers; refine stopwords and matcher.
	- Perf checks on /teach, /mcq/validate, /answer/validate; caching or memoization where safe.
	- Update docs and smoke scripts.

- Day 10: Demo prep and retro
	- Polish UX copy and error states; finalize docs and demo script.
	- Run full eval; export snapshot for dashboard.
	- Sprint 02 review and retrospective; outline Sprint 03.
