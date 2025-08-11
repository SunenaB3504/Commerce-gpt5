from typing import List, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class Chunk:
    id: str
    text: str
    page_start: int
    page_end: int
    metadata: Dict[str, Any]


def _sliding_windows(text: str, size: int, overlap: int) -> List[Tuple[int, int, str]]:
    """Return list of (start_index, end_index, chunk_text) over characters."""
    if size <= 0:
        raise ValueError("size must be > 0")
    if overlap < 0 or overlap >= size:
        overlap = 0
    chunks: List[Tuple[int, int, str]] = []
    i = 0
    n = len(text)
    while i < n:
        end = min(i + size, n)
        chunks.append((i, end, text[i:end]))
        if end == n:
            break
        i = end - overlap
    return chunks


def chunk_pages(
    pages: List[Tuple[int, str]],
    *,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
    subject: str | None = None,
    chapter: str | None = None,
    filename: str | None = None,
    source_path: str | None = None,
) -> List[Chunk]:
    """
    Convert a list of (page_number, text) into overlapping character-based chunks.

    - chunk_size and chunk_overlap are in characters (roughly ~4 chars/token for English).
    - Includes basic metadata for indexing and later citation.
    """
    import uuid

    # Concatenate pages while tracking page boundaries
    full_text_parts: List[str] = []
    page_break_positions: List[Tuple[int, int]] = []  # (page_no, end_pos)
    cursor = 0
    for pno, ptxt in pages:
        if not ptxt:
            ptxt = ""
        full_text_parts.append(ptxt)
        cursor += len(ptxt)
        page_break_positions.append((pno, cursor))
        # Insert a separator to avoid word-joins across pages
        full_text_parts.append("\n\n")
        cursor += 2

    full_text = "".join(full_text_parts).strip()
    win_list = _sliding_windows(full_text, chunk_size, chunk_overlap)

    def _page_span(start_idx: int, end_idx: int) -> Tuple[int, int]:
        start_page = 1
        end_page = 1
        for pno, pos in page_break_positions:
            if pos <= start_idx:
                start_page = pno
            if pos <= end_idx:
                end_page = pno
            else:
                break
        return start_page, end_page

    out: List[Chunk] = []
    for idx, (s, e, ctext) in enumerate(win_list, start=1):
        p_start, p_end = _page_span(s, e)
        meta = {
            "subject": subject,
            "chapter": chapter,
            "page_start": p_start,
            "page_end": p_end,
            "filename": filename,
            "source_path": source_path,
            "chunk_index": idx,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }
        out.append(
            Chunk(
                id=str(uuid.uuid4()),
                text=ctext.strip(),
                page_start=p_start,
                page_end=p_end,
                metadata=meta,
            )
        )

    # Drop empty chunks, if any
    out = [c for c in out if c.text]
    return out
