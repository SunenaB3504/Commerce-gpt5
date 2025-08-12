# Sprint 01 retrospective

Date: 2025-08-12

What went well
- Delivered a working vertical slice (upload/parse → chunk/index → ask with citations) with PWA shell.
- Added TF‑IDF caching and retriever toggle for speed and control.
- Curated fallback made answers exam-ready; externalized JSON allows scaling.
- Hardened API with payload limit and request timeouts; UI gained timeouts and toasts.
- OCR fallback integrated end-to-end for scanned PDFs.

What could be improved
- Earlier agreement on retrieval defaults (embedding vs classic) to avoid rework.
- More automated eval coverage (hit@k, answer coverage by chapter).
- Admin controls (hot-reload curated Q&A, stopwords) could reduce restarts.

Actions for Sprint 02
- Ship “Teach me v1” and MCQ validation flows.
- Add eval harness and dashboard (hit@k, citation presence, latency).
- Expand curated Q&A across chapters; add admin hot-reload endpoint.
- Performance toggles in UI (retriever, K, filter) persisted to localStorage.
- Document ops knobs: MAX_UPLOAD_MB, REQUEST_TIMEOUT_SEC, OCR_MIN_CHARS, OCR_ZOOM.
