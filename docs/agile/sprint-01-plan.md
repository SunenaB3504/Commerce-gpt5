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
