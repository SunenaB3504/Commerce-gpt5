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
- Backend: /upload, /parse, /index, /ask (streaming tokens)
- Frontend: index.html with upload; ask UI with mobile layout; installable PWA
- Tests: unit for parsing/chunking; simple E2E ask

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
