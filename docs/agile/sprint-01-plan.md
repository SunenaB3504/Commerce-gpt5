# Sprint 01 plan (2 weeks)

Sprint goal: Working vertical slice — upload/parse → chunk/embed → ask with citations, mobile-first PWA shell.

Scope (stories)
- US-001 Upload PDFs and parse text
- US-003 Chunk & embed content; build vector index (minimal)
- US-004 Ask endpoint with RAG and citations (happy path)
- US-007 PWA shell (manifest, service worker, icons)

Out of scope
- OCR fallback (US-002) unless time allows
- Teach me v1 (US-005) — next sprint

Deliverables
- Backend: /upload, /parse, /index, /ask (streaming tokens; retriever toggle; TF‑IDF cache)
- Frontend: index.html with upload; ask UI with mobile layout; installable PWA
- Tests: unit for parsing/chunking; simple E2E ask
- Tooling: scripts/eval_retrieval.py; custom stopwords at docs/data/stopwords.txt

Risks
- PDF parsing variance; fallback path documented
- Embedding model setup on Windows; pin versions

Definition of Done
- CI green; lint/type pass
- E2E ask returns grounded answer with ≥1 citation on sample PDF
- PWA installable; basic offline page

---

Sprint dates
- Start: 2025-08-11 (2 weeks/10 working days)
- Review/Retro: 2025-08-22

Status checkpoint (2025-08-12)
- Day 5: Completed + backlog cleared (TF‑IDF caching, custom stopwords, retriever toggle, eval script); tests green.
- Day 6: Completed (PWA shell + Ask UI). App is installable; shell cached; offline fallback served.

Team & roles
- Product/QA: Validates ACs, demo, and coverage on sample PDFs
- Dev: Full-stack (backend FastAPI + web PWA)

Success criteria
- E2E Ask returns grounded answers with citations for one uploaded PDF
- PWA is installable and serves an offline fallback page
- Unit tests for parse/chunk; one E2E ask test; docs updated

User stories with AC and tasks

US-001 Upload PDFs and parse text (SRS: FR-ING-001/003)
- AC: Multiple PDFs upload; parsed+clean text stored; errors logged
- Tasks: Backend POST /upload, /parse; Frontend upload UI; tests for cleanup rules

US-003 Chunk & embed content; build vector index (SRS: FR-ING-004/005)
- AC: Chunks 300–800 tokens with overlap, include page spans; kNN search returns expected passages
- Tasks: Chunker module; embeddings (MiniLM); index (Chroma/FAISS); unit tests

US-004 Ask endpoint with RAG and citations (SRS: FR-RAG-001/002/003)
- AC: POST /ask returns grounded answer with [chapter: pages] citations; filters by subject/chapter
- Tasks: Retriever, MMR re-ranker, prompt template, generator adapter, token streaming; E2E test

US-007 PWA shell (SRS: FR-PWA-001)
- AC: Installable PWA; shell cached; offline fallback served
- Tasks: manifest.json, service worker, icons; manual install test

Work breakdown structure (WBS)
- Backend foundation: skeleton, env, logging, error handling; /upload, /parse, /index, /ask stubs
- Parsing pipeline: PyMuPDF extraction, cleanup rules, metadata capture
- Chunk/Embed/Index: chunker, embedder, index builder; store/reload index
- RAG & Generation: retriever with filters, MMR, prompt templates, generator, streaming
- Web PWA: Upload page, Ask page, selectors, toasts, manifest, SW, icons
- QA & docs: unit tests, E2E, API docs, how-to run, demo script

Day-by-day plan
- Day 1: Backend skeleton, env config, API contracts
- Day 2: /parse; parse sample PDF; unit tests; keep uploads working
- Day 3: Chunker + tests; start embeddings & index
- Day 4: Finish embeddings/index; retrieval sanity; start /ask stub
- Day 5: End-to-end /ask with citations; basic streaming
- Day 6: PWA shell (manifest, SW, icons); Ask UI
- Day 7: Upload UI wiring; error handling; polish
- Day 8: E2E test; timeouts/file limits; docs; perf pass
- Day 9: Buffer (OCR fallback or refactors); demo prep
- Day 10: Review demo; retro; plan Sprint 02

QA mapping to SRS
- FR-ING-001/003: Parse unit tests; upload/parse API artifacts validated
- FR-ING-004/005: Chunk/overlap tests; retrieval recall sanity
- FR-RAG-001/002/003: E2E Ask with citations; filter constraints; MMR reduces duplicates
- FR-PWA-001: Lighthouse installability; SW caches shell; offline fallback works

Environments & config
- Local dev: Windows, Python 3.11+; simple static server for /web
- Env vars: API_BASE, INDEX_PATH, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVAL_K, USE_MMR

Risks & mitigations
- PDF variance → fallback parser; cleanup rules; test multiple samples
- Embedding install on Windows → pin versions; use MiniLM
- Streaming complexity → start with chunked responses, add streaming if time allows

Deliverables
- Backend: /upload, /parse, /index, /ask implemented
- Frontend: PWA shell + Upload and Ask UIs (mobile-first)
- Tests: unit + E2E; minimal CI; docs (README, API)
- Demo script included below

Demo script
- Upload a sample Economics Ch.1 PDF
- Show parsed stats and index built
- Ask: “Define opportunity cost” with filters; receive grounded answer with citations
- Install PWA; enable airplane mode; see offline fallback page

---

## Demo setup (Day 4)

Prerequisites
- Windows with PowerShell (pwsh)
- Python venv at `.venv` and dependencies from `requirements.txt`
- Sample PDF present under `uploads/` (e.g., `uploads/18a9c7c4-..._keec101.pdf`)

Steps
1) Start the API (use 8004 locally)
	```powershell
	C:/Users/Admin/Sunil/llm/Commerce-gpt5/.venv/Scripts/python.exe -m uvicorn services.api.main:app --host 127.0.0.1 --port 8004
	```
	Health: `GET http://127.0.0.1:8004/health/` → `{ "status": "ok" }`

2) Index the sample (optional if already indexed)
	- VS Code REST Client: open `scripts/day4.rest`, set `@host` to `http://127.0.0.1:8004`, run “Re-index … by path”.
	- or call `POST /data/index` with form fields: `path`, `subject=Economics`, `chapter=1`.

3) Ask with synthesis (smoke script)
	```powershell
	./scripts/smoke-day4-8004.ps1
	```
	Expect: Namespace (e.g., `Economics-ch1`), a synthesized Answer ending with `[Sources: …]`, Citations list, and Top passages.

4) Web Ask UI (optional)
	- Open `web/index.html` in a browser.
	- In DevTools Console: `window.API_BASE_OVERRIDE = 'http://127.0.0.1:8004'` and reload.
	- Use Ask form: Subject `Economics`, Chapter `1`, enter your question.

5) Streaming (optional)
	- Open in browser: `http://127.0.0.1:8004/ask/stream?q=two-fold%20motive%20behind%20the%20deindustrialisation&subject=Economics&chapter=1&k=6`
	- Observe meta → passage events → final answer.

Troubleshooting
- If port 8003 is busy, keep using 8004 and update scripts/REST host.
- Empty results: re-index by path via `scripts/day4.rest`.
- Ranking weak: install scikit-learn (TF‑IDF) or enable Chroma vectors, then re-index.

Day 1 status (done)
- Backend skeleton with FastAPI created; CORS enabled
- Routes: /health and /data/upload implemented and tested
	- Health: { "status": "ok" } on 127.0.0.1:8002/health/
	- Upload: PDF accepted, returns id/filename/path/subject/chapter; file saved under uploads/
	- Negative: non-PDF returns HTTP 400
- Frontend: Minimal index.html with upload form; config and upload JS added; basic styles
- Requirements pinned in requirements.txt (PyMuPDF deferred to Day 2 to avoid Windows build issues)
- Note: Local dev using port 8002 (8000 was occupied)

Next up (Day 2)
- Implement /parse with PyMuPDF extraction and cleanup (target Python 3.11 wheels)
- Add proper 400/413 error responses for size/type; logging
- Unit tests for parsing rules and basic text normalization
- Optional: small UI control to trigger parse after upload

Day 2 status (done)
- /data/parse implemented; uses PyMuPDF if available else pdfminer.six fallback.
- Parsed keec101.pdf successfully; saved page-wise JSON at parse-keec101.json.
- REST client added (scripts/day2.rest); verified on 127.0.0.1:8002.

Day 3 status (done)
- Chunking implemented with overlap and page-span metadata (services/api/utils/chunker.py).
- Indexing + retrieval implemented:
	- Primary path: ChromaDB + MiniLM (if installed).
	- Fallback path: Pure-Python JSON index with TF-IDF/token overlap; no heavy deps required.
- Routes live: POST /data/index (build index and persist chunks JSON), GET /ask (top-k passages with metadata).
- Validation: Indexed keec101.pdf; /ask returned non-empty results for queries like “two-fold motive behind deindustrialisation,” showing text snippets from the chapter.
- Tooling: scripts/day3.rest; scripts/smoke-day3.ps1.
- Note: API running on 127.0.0.1:8003 locally.

Day 4 status (done)
- Added answer synthesis utility with MMR and extractive sentence picking; inline citations.
- Extended GET /ask to return answer + citations; added /ask/stream (SSE) simple stream.
- Web: minimal Ask UI on index.html; day4 REST and smoke scripts.
- Validation: Ran scripts/smoke-day4-8004.ps1 against http://127.0.0.1:8004; received namespace, synthesized answer, citations, and top passages.

Day 5 status (done)
- TF‑IDF installed; BM25-like fallback; unit tests/E2E ask added; synthesis noise filters.
- Backlog cleared:
	- TF‑IDF caching with on-disk persistence per-namespace (auto invalidated on upsert).
	- Custom stopwords loaded from docs/data/stopwords.txt (merged with English list).
	- Retriever toggle on /ask and /ask/stream: auto|tfidf|bm25|chroma.
	- Evaluation script at scripts/eval_retrieval.py (reports hit@k and answer presence).

How to use (new)
```powershell
# Force TF‑IDF retriever via API
GET /ask?q=...&subject=Economics&chapter=3&retriever=tfidf

# Run the local eval (with API running, default http://127.0.0.1:8000)
python scripts/eval_retrieval.py --k 5 --retriever tfidf --subject Economics --chapter 3
```

Day 6 status (done)
- PWA shell implemented:
	- manifest.webmanifest (name, start_url=/web/index.html, scope=/web, theme/background, icons incl. maskable).
	- service-worker.js: caches shell assets (versioned cache), bypasses API, offline.html for navigations, old caches cleared on activate.
	- offline.html present and styled; icons available (SVGs).
- Web UI wired:
	- index.html registers SW; includes install button, network status dot, cache clear; links manifest and icons.
	- Ask and Upload forms present with basic mobile layout; JS modules (config/upload/ask/pwa) loaded.
- Result: App passes manual install and offline fallback checks. Lighthouse pass optional.
