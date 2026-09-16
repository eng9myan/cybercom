"""
OCR seam. The image→text step is where a provider plugs in (Tesseract, AWS
Textract, Azure Document Intelligence) — gated by CYED_OCR_ENABLED. Text/JSON
uploads are read directly. Everything AFTER text (field extraction) is real and
runs regardless, so a device that already does OCR just posts `raw_text`.
"""

import os


def extract_text(data: bytes, content_type: str) -> str | None:
    ct = (content_type or "").lower()
    if ct.startswith("text/") or ct in ("application/json",):
        try:
            return data.decode("utf-8", "replace")
        except Exception:
            return None
    if os.environ.get("CYED_OCR_ENABLED") == "1":
        # A real provider call (Textract/Tesseract) goes here and returns text.
        return None
    return None  # no provider configured → caller marks ocr_pending
