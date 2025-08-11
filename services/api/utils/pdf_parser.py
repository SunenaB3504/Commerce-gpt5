from typing import List, Tuple


def _clean(text: str) -> str:
    # Basic cleanup; can be extended with hyphenation fixes, whitespace normalization
    if not text:
        return ""
    # Normalize line endings and collapse excessive whitespace
    import re
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\x0b\x0c]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_text_pymupdf(path: str) -> List[Tuple[int, str]]:
    pages: List[Tuple[int, str]] = []
    try:
        import fitz  # type: ignore[reportMissingImports]  # PyMuPDF (optional)
    except Exception as e:
        raise ImportError("PyMuPDF not available") from e
    with fitz.open(path) as doc:
        for i, page in enumerate(doc):
            raw = page.get_text("text")
            pages.append((i + 1, _clean(raw)))
    return pages


def extract_text_pdfminer(path: str) -> List[Tuple[int, str]]:
    try:
        from pdfminer.high_level import extract_pages  # type: ignore[reportMissingImports]
        from pdfminer.layout import LTTextContainer  # type: ignore[reportMissingImports]
    except Exception as e:
        raise ImportError("pdfminer.six not available") from e

    pages: List[Tuple[int, str]] = []
    for i, page_layout in enumerate(extract_pages(path)):
        texts: List[str] = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                texts.append(element.get_text())
        pages.append((i + 1, _clean("\n".join(texts))))
    return pages


def extract_text(path: str) -> List[Tuple[int, str]]:
    """Return list of (page_number, cleaned_text). Prefers PyMuPDF, falls back to pdfminer.six."""
    try:
        return extract_text_pymupdf(path)
    except Exception:
        return extract_text_pdfminer(path)
