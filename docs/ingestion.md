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
- Optional chapter title extraction (first heading on first page).
- Embedding model selection per run.
- Parallel ingestion for speed.
- Deduplication across overlapping PDFs contributing to same chapter.
