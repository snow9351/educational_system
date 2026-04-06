"""Load PDFs (text + OCR on thin pages), images (OCR), txt. Needs Tesseract; optional TESSERACT_CMD."""

from __future__ import annotations

import io
from typing import Any
import os
import re
import shutil
import sys
from pathlib import Path

_MIN_PAGE_TEXT_CHARS = 45

_tesseract_probe_done: bool = False
_tesseract_exe: str | None = None


def _candidate_tesseract_executables() -> list[Path]:
    out: list[Path] = []

    env = (os.environ.get("TESSERACT_CMD") or "").strip()
    if env:
        out.append(Path(env))

    w = shutil.which("tesseract")
    if w:
        out.append(Path(w))

    if sys.platform == "win32":
        for key in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(key)
            if base:
                out.append(Path(base) / "Tesseract-OCR" / "tesseract.exe")
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            out.append(Path(local) / "Programs" / "Tesseract-OCR" / "tesseract.exe")
    else:
        for p in (
            "/opt/homebrew/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/usr/bin/tesseract",
        ):
            out.append(Path(p))

    # De-duplicate while preserving order
    seen: set[str] = set()
    unique: list[Path] = []
    for p in out:
        s = str(p)
        if s not in seen:
            seen.add(s)
            unique.append(p)
    return unique


def _resolve_tesseract_executable() -> str | None:
    global _tesseract_probe_done, _tesseract_exe
    if _tesseract_probe_done:
        return _tesseract_exe

    _tesseract_probe_done = True
    try:
        import pytesseract
    except Exception:
        _tesseract_exe = None
        return None

    for cand in _candidate_tesseract_executables():
        if not cand.is_file():
            continue
        resolved = str(cand.resolve())
        pytesseract.pytesseract.tesseract_cmd = resolved
        try:
            pytesseract.get_tesseract_version()
            _tesseract_exe = resolved
            return _tesseract_exe
        except Exception:
            continue

    _tesseract_exe = None
    return None


def _tesseract_available() -> tuple[bool, str | None]:
    try:
        path = _resolve_tesseract_executable()
        if path:
            return True, None
        hint = (
            "Install Tesseract (https://github.com/UB-Mannheim/tesseract/wiki on Windows), "
            "or set TESSERACT_CMD to the full path of tesseract.exe (Windows) or tesseract (macOS/Linux)."
        )
        return False, hint
    except Exception as e:  # pragma: no cover - environment-specific
        return False, f"{type(e).__name__}: {e}"


def _ocr_help_suffix(ocr_err: str | None) -> str:
    if not ocr_err:
        return ""
    return f" {ocr_err}"


def _ocr_image(image_bytes: bytes) -> str:
    import pytesseract
    from PIL import Image

    _resolve_tesseract_executable()
    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return pytesseract.image_to_string(im, config="--psm 3").strip()


def load_text(file_path: str | Path) -> str:
    path = Path(file_path)
    return path.read_text(encoding="utf-8", errors="replace").strip()


def load_image(file_path: str | Path) -> str:
    path = Path(file_path)
    ok, err = _tesseract_available()
    if not ok:
        return (
            "[OCR unavailable: "
            "could not find a working Tesseract executable."
            + _ocr_help_suffix(err)
            + "]"
        )
    import pytesseract
    from PIL import Image

    try:
        im = Image.open(path).convert("RGB")
        return pytesseract.image_to_string(im, config="--psm 3").strip()
    except Exception as e:  # pragma: no cover
        return f"[Image read/OCR failed: {path.name} ({e})]"


def _extract_text_from_fitz_document(doc: Any, ocr_ok: bool, ocr_err: str | None) -> str:
    parts: list[str] = []
    for page in doc:
        text = (page.get_text() or "").strip()
        use_ocr = len(text) < _MIN_PAGE_TEXT_CHARS

        if not use_ocr:
            parts.append(text)
            continue

        if ocr_ok:
            try:
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                png = pix.tobytes("png")
                ocr_text = _ocr_image(png)
                if ocr_text:
                    parts.append(ocr_text)
                elif text:
                    parts.append(text)
            except Exception:
                if text:
                    parts.append(text)
        else:
            if text:
                parts.append(text)

    result = "\n\n".join(p for p in parts if p).strip()
    if not result:
        if not ocr_ok:
            return (
                "[OCR unavailable: this PDF has little or no embedded text."
                + _ocr_help_suffix(ocr_err)
                + "]"
            )
        return (
            "[No text extracted from PDF: try a higher-resolution scan, "
            "or install Tesseract language data for your content (e.g. eng).]"
        )
    return result


def load_pdf(file_path: str | Path) -> str:
    import fitz  # PyMuPDF

    path = Path(file_path)
    ocr_ok, ocr_err = _tesseract_available()

    with fitz.open(str(path)) as doc:
        return _extract_text_from_fitz_document(doc, ocr_ok, ocr_err)


def load_pdf_bytes(data: bytes, source_name: str = "upload.pdf") -> str:
    """Extract text from a PDF loaded in memory (e.g. Streamlit upload)."""
    import fitz  # PyMuPDF

    ocr_ok, ocr_err = _tesseract_available()
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            return _extract_text_from_fitz_document(doc, ocr_ok, ocr_err)
    except Exception as e:  # pragma: no cover
        return f"[PDF read failed: {source_name} ({e})]"


def load_image_bytes(data: bytes, source_name: str = "upload.png") -> str:
    ok, err = _tesseract_available()
    if not ok:
        return (
            "[OCR unavailable: could not find a working Tesseract executable."
            + _ocr_help_suffix(err)
            + "]"
        )
    import pytesseract
    from PIL import Image

    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
        return pytesseract.image_to_string(im, config="--psm 3").strip()
    except Exception as e:  # pragma: no cover
        return f"[Image read/OCR failed: {source_name} ({e})]"


def load_input_bytes(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return load_pdf_bytes(data, source_name=filename)

    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}:
        return load_image_bytes(data, source_name=filename)

    if suffix in {".txt", ".md", ".csv"}:
        return data.decode("utf-8", errors="replace").strip()

    try:
        return data.decode("utf-8", errors="replace").strip()
    except Exception:
        return (
            f"[Unsupported or binary upload: {filename}. "
            "Use .pdf, images, or .txt.]"
        )


def merge_loaded_segments(
    labeled_parts: list[tuple[str, str]],
    *,
    delimiter: str = "\n\n--- next file ---\n\n",
) -> str:
    blocks: list[str] = []
    for name, text in labeled_parts:
        if text:
            blocks.append(f"[[ Source file: {name} ]]\n{text}")
    return delimiter.join(blocks).strip()


def load_input(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(path)

    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}:
        return load_image(path)

    if suffix in {".txt", ".md", ".csv"}:
        return load_text(path)

    try:
        return load_text(path)
    except UnicodeDecodeError:
        return (
            f"[Could not decode as UTF-8 text: {path.name}. "
            "Use .txt, .pdf, or a supported image format.]"
        )


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
