"""Cover extraction helpers shared by generator and uploader."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from .constants import COVER_QUALITY, COVER_WIDTH

try:
    import fitz  # type: ignore
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from PIL import Image  # type: ignore
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    from docx import Document as DocxDocument  # type: ignore
    HAS_PYTHON_DOCX = True
except ImportError:
    HAS_PYTHON_DOCX = False


def dependency_status() -> dict[str, bool]:
    """Return availability for required cover dependencies."""
    return {
        "PyMuPDF": HAS_PYMUPDF,
        "Pillow": HAS_PILLOW,
        "python-docx": HAS_PYTHON_DOCX,
    }


def extract_cover(file_path: Path, output_path: Path) -> bool:
    """Extract a WebP cover using the canonical 600px/q85 policy."""
    ext = file_path.suffix.lower()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if ext in {".pdf", ".epub"}:
        return _render_first_page(file_path, output_path)
    if ext == ".docx":
        return _extract_docx_image(file_path, output_path)
    return False


def _render_first_page(file_path: Path, output_path: Path) -> bool:
    if not HAS_PYMUPDF:
        return False
    try:
        doc = fitz.open(str(file_path))
        try:
            if doc.page_count == 0:
                return False
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0), alpha=False)
            if not HAS_PILLOW:
                pix.save(str(output_path))
                return True
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            _save_webp(img, output_path)
            return True
        finally:
            doc.close()
    except Exception:
        return False


def _extract_docx_image(file_path: Path, output_path: Path) -> bool:
    if not HAS_PYTHON_DOCX or not HAS_PILLOW:
        return False
    try:
        doc = DocxDocument(str(file_path))
        for rel in doc.part.rels.values():
            if "image" in rel.reltype:
                img = Image.open(BytesIO(rel.target_part.blob))
                _save_webp(img, output_path)
                return True
    except Exception:
        return False
    return False


def _save_webp(img: "Image.Image", output_path: Path) -> None:
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    if img.width > COVER_WIDTH:
        ratio = COVER_WIDTH / img.width
        img = img.resize((COVER_WIDTH, int(img.height * ratio)), Image.LANCZOS)
    img.save(str(output_path), "WEBP", quality=COVER_QUALITY, method=6)

