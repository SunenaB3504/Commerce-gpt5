# Content Ingestion Pipeline

This document describes the bulk ingestion workflow for syllabus PDFs.

## Directory Layout
Input PDFs are organized under `Syllabus/<Subject>/` (e.g. `Syllabus/Economics/keec101.pdf`). The ingestion script outputs:

- Uploaded originals (uuid-prefixed) in `uploads/`
- Chunk JSON: `web/data/subjects/<Subject>/chapters/<Chapter>/chunks-001.json`
- Subject manifest: `web/data/subjects/<Subject>/manifest.json`
- Index namespace data: `indexes/<Subject>-ch<Chapter>/`
- Global log: `web/data/ingestion-log.json`
- Cache file: `.ingestion_cache.json`

## Chapter Inference Heuristic
From filename numeric groups:
1. Take last group of 2-3 digits.
2. If 3 digits ending with a plausible two-digit chapter (01-40), use the last two.
3. Else if full group within 1-40 use it.
4. Else fallback to first group within 1-40.
If none: chapter = `unknown` (skipped if `--skip-unknown`).

Examples:
- `keec101.pdf` -> `1`
- `lebs202.pdf` -> `2`
- `leac205.pdf` -> `5`

## Script Usage
Run via module:
```
python -m scripts.bulk_ingest --all-subjects --reset --verbose
```

Common options:
- `--all-subjects` Process every top-level directory under `Syllabus/`.
- `--root Syllabus/Economics` Limit to one path (repeatable).
- `--subject Economics` Override subject naming.
- `--chunk-size 1200` Character chunk size (default 1200).
- `--chunk-overlap 200` Overlap characters (default 200).
- `--ocr` Enable OCR fallback for low-text pages (depends on PyMuPDF + pytesseract + PIL).
- `--force` Reprocess even if hash already ingested.
- `--reset` Reset each namespace before upsert (useful for a clean rebuild).
- `--dry-run` Simulate without writing/changing files or indexes (still prints summary).
- `--verbose` Detailed per-file logging.
- `--skip-unknown` Skip files where chapter cannot be inferred.

## Idempotency & Caching
The script stores a SHA256 keyed cache in `.ingestion_cache.json`. Without `--force`, previously processed identical files are skipped quickly.

## Manifests
`manifest.json` holds chapter entries:
```
{
  "subject": "Economics",
  "chapters": [
    {
      "chapter": "1",
      "pdf_files": ["keec101.pdf", "leec101.pdf"],
      "source_upload_ids": ["<uuid1>", "<uuid2>"],
      "chunks_file": "web/data/subjects/Economics/chapters/1/chunks-001.json",
      "index_namespace": "Economics-ch1",
      "chunk_count": 50,
      "last_ingested": "2025-08-14T10:22:33Z"
    }
  ]
}
```

## Global Log
`web/data/ingestion-log.json` appends an entry per successful PDF ingestion containing timestamp, subject, chapter, pdf, chunk count, and namespace.

## Rebuild Strategy
1. (Optional) Delete `indexes/` and `web/data/subjects/<Subject>/chapters/*` to fully clear.
2. Run with `--all-subjects --reset` to repopulate.
3. Confirm manifests and chunk counts.

## Troubleshooting
- Empty or low-text PDF pages: Use `--ocr`.
- Missing dependencies: install `pymupdf`, `pdfminer.six`, optionally `pytesseract`, `Pillow`.
- Chapter collisions (multiple PDFs same chapter): chunks are appended; the manifest includes all contributing PDFs.

## Next Enhancements (Future)

## Admin Endpoints & Workflow

## Retrieval Validation & Troubleshooting

## Retrieval Benchmarking & Optimization

### Benchmarking Harness
To measure retrieval performance and quality:
1. Use the test suite (`test_e2e_ask.py`, `test_chunker_and_retrieval.py`) to benchmark hit@k and latency.
2. For manual benchmarking, use `/ask` API with representative queries and record response times and hit rates.

### Initial Optimization: Stopword Refinement & Bigram Weighting
- The indexer uses custom stopwords (from `docs/data/stopwords.txt`) and bigram weighting (`ngram_range=(1,2)`) in TF-IDF vectorizer.
- To refine stopwords, update `docs/data/stopwords.txt` and reload via `/admin/reload/stopwords`.
- Bigram weighting is enabled by default in the TF-IDF retriever for improved phrase matching.

### Validation
- After optimization, rerun retrieval tests and compare hit@k and latency to previous results.
- Document improvements in the sprint plan and ingestion report.

### Retrieval Smoke Test
To validate that chunked content is indexed and retrievable:
1. Run the test suite with pytest:
  ```
  pytest tests/test_chunker_and_retrieval.py
  pytest tests/test_e2e_ask.py
  ```
2. Ensure tests pass for chunking, indexing, and retrieval (BM25 fallback, citation presence, answer synthesis).
3. For API validation, use `/ask` endpoint with a known query and confirm expected answer and citations.

### Troubleshooting
- If tests are not discovered, ensure test files and functions are named with `test_` prefix and pytest is installed.
- If retrieval returns no results, check that chunk JSONs and index directories are populated and match the subject/chapter.
- For performance issues, review index size and chunk overlap settings.

### Reload Curated Q&A
Reloads the curated Q&A cache for all subjects.
```
POST /admin/reload/curated
Headers: x-admin-token: <your_token>
Response: {"status": "ok", "curated_count": <int>}
```

### Reload Stopwords
Clears TF-IDF caches so updated stopwords take effect.
```
POST /admin/reload/stopwords
Headers: x-admin-token: <your_token>
Response: {"status": "ok", "cleared_namespaces": [...]}
```

### Calibration: Suggest Short-Answer Thresholds
Suggests new scoring thresholds based on labeled sample answers.
```
POST /admin/calibration/short-answer
Headers: x-admin-token: <your_token>
Body: {"rows": [ ...scored samples... ]}
Response: {"suggestions": {...}, "count": <int>}
```

### Get/Update Validation Thresholds
Get or update the current scoring thresholds for short-answer validation.
```
GET /admin/validate/thresholds
Headers: x-admin-token: <your_token>
Response: {"partial_min": <float>, "correct_min": <float>, "overrides": {...}}

POST /admin/validate/thresholds
Headers: x-admin-token: <your_token>
Body: {"partial_min": <float>, "correct_min": <float>}
Response: {"status": "ok", "applied": {...}, "effective": {...}}
```

### Workflow Example
1. After ingestion, reload curated Q&A and stopwords to refresh caches.
2. Upload calibration samples and suggest new thresholds.
3. Review and apply threshold overrides as needed.
4. Validate changes via readiness dashboard and logs.
