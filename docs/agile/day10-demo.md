# Day 10 demo guide

Prereqs
- Server running (uvicorn services.api.main:app --port 8000)
- Sample PDF present under uploads/

Steps
1) Upload with auto-index (and OCR if needed)
   - POST /data/upload with subject=Economics, chapter=3, auto_index=true, ocr=false
   - Expect id, path, namespace, index_count, chunks_path
2) Ask a question
   - GET /ask?q=Ways%20a%20partner%20can%20retire%20from%20the%20firm&subject=Economics&chapter=3&k=6&retriever=tfidf
   - Expect answer, citations, top passages
3) PWA quick check
   - Open /web/index.html, try Ask UI, toggle retriever, verify toasts and busy states
4) Offline fallback (optional)
   - Install PWA; go offline; navigate and see offline.html

Toggles & knobs
- retriever: auto|tfidf|bm25|chroma
- k: 3–15
- filter_noise: true|false
- OCR_MIN_CHARS (40), OCR_ZOOM (2.0)
- MAX_UPLOAD_MB (16), REQUEST_TIMEOUT_SEC (45)
