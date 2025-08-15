"""Bulk ingestion script for chapter-wise PDFs located under `Syllabus/`.

Usage (examples, run from repo root):
  python -m scripts.bulk_ingest --root Syllabus/Economics --subject Economics
  python -m scripts.bulk_ingest --root Syllabus/Accountancy --subject Accountancy --reset
  python -m scripts.bulk_ingest --all-subjects --reset

Features:
  - Walks syllabus subject folders, processes PDFs (copy -> extract -> chunk -> index)
  - Writes chunk JSON under web/data/subjects/<Subject>/chapters/<Chapter>/chunks-001.json
  - Maintains per-subject manifest.json and global ingestion log
  - Skips previously processed files by SHA256 unless --force
  - Supports dry-run and verbose logging

Notes:
  - Chapter inference: derived from filename numeric groups (first or last 2-3 digits).
  - Filenames like keec101.pdf -> chapter 1 (strip leading zeros, take last two digits unless 3-digit pattern ends with 01..12)
  - Mixed code variants (leec / keec) treated equivalently for Economics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SYLLABUS_DIR = REPO_ROOT / "Syllabus"
UPLOADS_DIR = REPO_ROOT / "uploads"
WEB_DATA_SUBJECTS = REPO_ROOT / "web" / "data" / "subjects"
INGESTION_LOG = REPO_ROOT / "web" / "data" / "ingestion-log.json"
CACHE_FILE = REPO_ROOT / ".ingestion_cache.json"

# Import API utilities via sys.path injection
API_UTILS = REPO_ROOT / "services" / "api" / "utils"
if str(API_UTILS.parent.parent) not in sys.path:
    sys.path.insert(0, str(API_UTILS.parent.parent))

from services.api.utils.pdf_parser import extract_text  # type: ignore
from services.api.utils.chunker import chunk_pages, Chunk  # type: ignore
from services.api.utils.indexer import DiskIndex  # type: ignore


@dataclass
class IngestResult:
    subject: str
    chapter: str
    pdf: str
    upload_path: str
    chunks_path: Optional[str]
    chunk_count: int
    namespace: str
    index_count: int
    skipped: bool = False
    reason: Optional[str] = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            h.update(block)
    return h.hexdigest()


def load_cache() -> Dict[str, Any]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, Any]) -> None:
    try:
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


def load_ingestion_log() -> List[Dict[str, Any]]:
    if INGESTION_LOG.exists():
        try:
            return json.loads(INGESTION_LOG.read_text(encoding='utf-8'))
        except Exception:
            return []
    return []


def append_ingestion_log(entry: Dict[str, Any]) -> None:
    log = load_ingestion_log()
    log.append(entry)
    INGESTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    INGESTION_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')


def infer_chapter(filename: str) -> Optional[str]:
    base = filename.lower().rsplit('.', 1)[0]
    # Pattern groups of digits
    # Strategy: look for sequences of 2-3 digits near end; choose last two digits if plausible (01-40), else first group.
    m_all = list(re.finditer(r"(\d{2,3})", base))
    if not m_all:
        return None
    # Prefer last group
    nums = [g.group(1) for g in m_all]
    candidate = nums[-1]
    # If 3 digits ending with two-digit plausible chapter (01-40), take those last two
    if len(candidate) == 3 and candidate[-2:].isdigit():
        last_two = int(candidate[-2:])
        if 1 <= last_two <= 40:
            return str(last_two)
    # Else if full candidate plausible 1-40
    val = int(candidate)
    if 1 <= val <= 40:
        return str(val)
    # fallback to first group
    val2 = int(nums[0])
    if 1 <= val2 <= 40:
        return str(val2)
    return None


def ensure_manifest(subject: str) -> Dict[str, Any]:
    subj_dir = WEB_DATA_SUBJECTS / subject.replace(' ', '_')
    subj_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = subj_dir / 'manifest.json'
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding='utf-8'))
        except Exception:
            pass
    manifest = {"subject": subject, "chapters": []}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


def update_manifest(manifest: Dict[str, Any], *, subject: str, chapter: str, pdf_filename: str, namespace: str, chunks_file_rel: str, chunk_count: int, upload_ids: List[str]) -> None:
    chapters = manifest.setdefault('chapters', [])
    entry = None
    for ch in chapters:
        if ch.get('chapter') == chapter:
            entry = ch
            break
    now_iso = datetime.now(timezone.utc).isoformat()
    if not entry:
        entry = {
            'chapter': chapter,
            'pdf_files': [],
            'source_upload_ids': [],
            'chunks_file': chunks_file_rel,
            'index_namespace': namespace,
            'chunk_count': chunk_count,
            'last_ingested': now_iso,
        }
        chapters.append(entry)
    # Update fields
    if pdf_filename not in entry['pdf_files']:
        entry['pdf_files'].append(pdf_filename)
    entry['chunks_file'] = chunks_file_rel
    entry['index_namespace'] = namespace
    entry['chunk_count'] = chunk_count
    entry['last_ingested'] = now_iso
    for uid in upload_ids:
        if uid not in entry['source_upload_ids']:
            entry['source_upload_ids'].append(uid)


def persist_manifest(subject: str, manifest: Dict[str, Any]) -> None:
    subj_dir = WEB_DATA_SUBJECTS / subject.replace(' ', '_')
    subj_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = subj_dir / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


def ingest_pdf(path: Path, *, subject: str, chapter: str, chunk_size: int, chunk_overlap: int, ocr: bool, force: bool, reset: bool, dry_run: bool, verbose: bool, cache: Dict[str, Any]) -> IngestResult:
    sha = sha256_file(path)
    cache_entry = cache.get(sha)
    if cache_entry and not force:
        return IngestResult(subject=subject, chapter=chapter, pdf=path.name, upload_path=cache_entry.get('upload_path', ''), chunks_path=cache_entry.get('chunks_path'), chunk_count=cache_entry.get('chunk_count', 0), namespace=cache_entry.get('namespace', ''), index_count=cache_entry.get('index_count', 0), skipped=True, reason='cached')

    import uuid
    upload_uuid = str(uuid.uuid4())
    upload_filename = f"{upload_uuid}_{path.name}"
    upload_dest = UPLOADS_DIR / upload_filename
    if not dry_run:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        upload_dest.write_bytes(path.read_bytes())
    if verbose:
        print(f"Copied {path} -> {upload_dest}")

    pages = extract_text(str(upload_dest if not dry_run else path), ocr=ocr)
    # Filter empty pages early
    pages = [(pno, txt) for pno, txt in pages if txt.strip()]
    if not pages:
        return IngestResult(subject=subject, chapter=chapter, pdf=path.name, upload_path=str(upload_dest), chunks_path=None, chunk_count=0, namespace=f"{subject}-ch{chapter}", index_count=0, skipped=True, reason='no_text')

    chunks: List[Chunk] = chunk_pages(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap, subject=subject, chapter=chapter, filename=path.name, source_path=str(upload_dest))
    chunk_count = len(chunks)
    namespace = f"{subject.replace(' ', '_')}-ch{chapter}"

    # Write chunks JSON
    subj_dir = WEB_DATA_SUBJECTS / subject.replace(' ', '_') / 'chapters' / chapter
    chunks_file = subj_dir / 'chunks-001.json'
    chunks_file_rel = str(chunks_file.relative_to(REPO_ROOT)).replace('\\', '/')
    if not dry_run:
        subj_dir.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                'id': c.id,
                'text': c.text,
                'page_start': c.page_start,
                'page_end': c.page_end,
                'metadata': c.metadata,
            } for c in chunks
        ]
        chunks_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    if verbose:
        print(f"Wrote chunks JSON: {chunks_file} ({chunk_count} chunks)")

    # Index
    index = DiskIndex()
    res = {'namespace': namespace, 'count': 0}
    if not dry_run:
        res = index.upsert(chunks, subject=subject, chapter=chapter, model='all-MiniLM-L6-v2', reset=reset)
    if verbose:
        print(f"Indexed namespace {res['namespace']} count={res['count']}")

    # Cache entry
    cache[sha] = {
        'subject': subject,
        'chapter': chapter,
        'pdf': path.name,
        'upload_path': str(upload_dest),
        'chunks_path': chunks_file_rel,
        'chunk_count': chunk_count,
        'namespace': res['namespace'],
        'index_count': res['count'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }

    return IngestResult(subject=subject, chapter=chapter, pdf=path.name, upload_path=str(upload_dest), chunks_path=chunks_file_rel, chunk_count=chunk_count, namespace=res['namespace'], index_count=res['count'])


def iter_pdfs(root: Path) -> Iterable[Path]:
    for p in sorted(root.rglob('*.pdf')):
        if p.is_file():
            yield p


def determine_subject(root: Path, arg_subject: Optional[str]) -> str:
    if arg_subject:
        return arg_subject
    # Use immediate folder name relative to Syllabus
    try:
        rel = root.relative_to(SYLLABUS_DIR)
        parts = rel.parts
        if parts:
            return parts[0].replace('_', ' ')
    except Exception:
        pass
    return root.name.replace('_', ' ')


def process_roots(roots: List[Path], *, subject_override: Optional[str], **kwargs) -> List[IngestResult]:
    results: List[IngestResult] = []
    cache = load_cache()
    for root in roots:
        if not root.exists():
            print(f"WARN: root {root} missing, skipping")
            continue
        subject = determine_subject(root, subject_override)
        manifest = ensure_manifest(subject)
        for pdf_path in iter_pdfs(root):
            chapter = infer_chapter(pdf_path.name) or 'unknown'
            if kwargs.get('skip_unknown') and chapter == 'unknown':
                print(f"Skip unknown chapter for {pdf_path.name}")
                continue
            res = ingest_pdf(pdf_path, subject=subject, chapter=chapter, **{k: v for k, v in kwargs.items() if k in {'chunk_size','chunk_overlap','ocr','force','reset','dry_run','verbose'}}, cache=cache)
            results.append(res)
            if not res.skipped and not kwargs.get('dry_run'):
                update_manifest(manifest, subject=subject, chapter=chapter, pdf_filename=pdf_path.name, namespace=res.namespace, chunks_file_rel=res.chunks_path or '', chunk_count=res.chunk_count, upload_ids=[res.upload_path.split('/')[-1].split('_')[0]])
                # Append ingestion log
                append_ingestion_log({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'subject': subject,
                    'chapter': chapter,
                    'pdf': pdf_path.name,
                    'chunks': res.chunk_count,
                    'namespace': res.namespace,
                    'chunks_file': res.chunks_path,
                })
        if not kwargs.get('dry_run'):
            persist_manifest(subject, manifest)
    save_cache(cache)
    return results


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Bulk ingest syllabus PDFs")
    ap.add_argument('--root', action='append', help='Root directory containing chapter PDFs (repeatable)')
    ap.add_argument('--all-subjects', action='store_true', help='Process all first-level subject dirs under Syllabus/')
    ap.add_argument('--subject', help='Override subject name for all --root dirs')
    ap.add_argument('--chunk-size', type=int, default=1200)
    ap.add_argument('--chunk-overlap', type=int, default=200)
    ap.add_argument('--ocr', action='store_true')
    ap.add_argument('--force', action='store_true', help='Reprocess even if file hash already ingested')
    ap.add_argument('--reset', action='store_true', help='Reset index namespace before upsert')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--skip-unknown', action='store_true')
    return ap.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    results: List[IngestResult]
    roots: List[Path] = []
    if args.all_subjects:
        # Enumerate immediate dirs in Syllabus
        for child in SYLLABUS_DIR.iterdir():
            if child.is_dir():
                roots.append(child)
    if args.root:
        roots.extend(Path(r) for r in args.root)
    if not roots:
        print("No roots specified. Use --root or --all-subjects.")
        return 1
    results = process_roots(roots, subject_override=args.subject, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap, ocr=bool(args.ocr), force=bool(args.force), reset=bool(args.reset), dry_run=bool(args.dry_run), verbose=bool(args.verbose), skip_unknown=bool(args.skip_unknown))
    # Summary
    ingested = [r for r in results if not r.skipped]
    skipped = [r for r in results if r.skipped]
    print(f"Ingested {len(ingested)} PDFs; skipped {len(skipped)} (cache/empty)")
    if args.verbose:
        for r in ingested:
            print(f"  {r.subject} ch{r.chapter} {r.pdf}: chunks={r.chunk_count} ns={r.namespace}")
        for r in skipped:
            print(f"  SKIP {r.pdf} reason={r.reason}")
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
