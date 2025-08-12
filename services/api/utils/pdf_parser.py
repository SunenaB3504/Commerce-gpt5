from typing import List, Tuple, Optional
import os


def _clean(text: str) -> str:
    # Basic cleanup; can be extended with hyphenation fixes, whitespace normalization
    if not text:
        return ""
    # Normalize line endings and collapse excessive whitespace
    import re
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\x0b\x0c]", " ", text)
    # Remove PDF artifact tokens like (cid:216) and similar
    text = re.sub(r"\(cid:[^\)]+\)", " ", text)
    # Fix common hyphen-space breaks like "de- industrialisation" -> "de-industrialisation"
    text = re.sub(r"(\w)-\s+(\w)", r"\1-\2", text)
    # Remove stray spaces before punctuation
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
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

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def extract_text_ocr(path: str, *, min_chars: Optional[int] = None, zoom: Optional[float] = None) -> List[Tuple[int, str]]:
    """OCR-enhanced extraction. Uses PyMuPDF text, OCRs pages with too little text.

    - min_chars: below this threshold, OCR is attempted for the page.
    - zoom: scale factor for rasterization (e.g., 2.0 ~ 144 DPI if default is ~72 DPI).
    """
    min_chars = _env_int("OCR_MIN_CHARS", min_chars if min_chars is not None else 40)
    zoom = float(os.getenv("OCR_ZOOM", str(zoom if zoom is not None else 2.0)))

    pages: List[Tuple[int, str]] = []
    try:
        import fitz  # type: ignore
        from PIL import Image  # type: ignore
        import pytesseract  # type: ignore
    except Exception:
        # If any dependency missing, fall back to non-OCR path
        try:
            return extract_text_pymupdf(path)
        except Exception:
            return extract_text_pdfminer(path)

    with fitz.open(path) as doc:
        for i, page in enumerate(doc):
            text = _clean(page.get_text("text"))
            if len(text) >= min_chars:
                pages.append((i + 1, text))
                continue
            # Rasterize and OCR
            try:
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                mode = "RGB"
                img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                ocr_text = pytesseract.image_to_string(img)
                ocr_text = _clean(ocr_text)
                # Prefer OCR text if it adds meaningful content
                use_text = ocr_text if len(ocr_text) > len(text) else text
                pages.append((i + 1, use_text))
            except Exception:
                pages.append((i + 1, text))
    return pages


def extract_text(path: str, *, ocr: bool = False) -> List[Tuple[int, str]]:
    """Return list of (page_number, cleaned_text).

    - Default: prefers PyMuPDF, falls back to pdfminer.six.
    - ocr=True: OCR-enhanced path; for low-text pages, rasterize and OCR.
    """
    if ocr:
        return extract_text_ocr(path)
    try:
        return extract_text_pymupdf(path)
    except Exception:
        return extract_text_pdfminer(path)
