# Proposal: Self-Hosted OCR Extraction Worker Pool

**Status: proposal, not built.** Illustrative architecture + starter code for
future review — not wired into `core/urls.py` or `INSTALLED_APPS`.

## Why

Cycom's `Documents` module (built tonight) already has a generic
`linked_model`/`linked_id` attachment pattern. The natural next step is
extracting structured data (vendor name, invoice number, line items, totals)
from uploaded PDFs/images without per-document metering against a hosted
cloud API — keeping the cost model as one-time engineering + your own
compute, not a recurring per-page toll.

## Architecture

```
Document uploaded → Celery task queued (existing dependency, already in
                     core/celery.py) → OCR worker pulls text via a
                     pluggable backend → structured fields extracted →
                     written back to a new OCRExtraction record linked
                     to the Document
```

Pluggable backend interface (swap in a hosted API later without touching
callers):

```python
# products/cycom/documents/ocr/base.py
from abc import ABC, abstractmethod


class OCRBackend(ABC):
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Raw text extraction from an image/PDF."""

    @abstractmethod
    def extract_structured(self, text: str) -> dict:
        """Best-effort structured fields (vendor, invoice_number, total, date)."""
```

```python
# products/cycom/documents/ocr/tesseract_backend.py
import pytesseract
from pdf2image import convert_from_path

from products.cycom.documents.ocr.base import OCRBackend


class TesseractBackend(OCRBackend):
    """Open-source, self-hosted — no per-document API cost."""

    def extract_text(self, file_path: str) -> str:
        if file_path.lower().endswith(".pdf"):
            pages = convert_from_path(file_path)
            return "\n".join(pytesseract.image_to_string(p) for p in pages)
        return pytesseract.image_to_string(file_path)

    def extract_structured(self, text: str) -> dict:
        # Real implementation: regex/heuristic field extraction, or hand
        # the raw text to CyAI's ModelGateway for structured parsing —
        # reuses the AI layer already built rather than a new dependency.
        raise NotImplementedError
```

Celery task:

```python
# products/cycom/documents/tasks.py
from core.celery import app
from products.cycom.documents.models import Document
from products.cycom.documents.ocr.tesseract_backend import TesseractBackend


@app.task
def extract_document_text(document_id: str):
    document = Document.objects.get(id=document_id)
    backend = TesseractBackend()
    text = backend.extract_text(document.file.path)
    fields = backend.extract_structured(text)
    # write to a new OCRExtraction model (not yet defined) linked to `document`
    return fields
```

## Real gaps before this is production-ready

- New model `OCRExtraction` (fields, confidence scores, review-needed flag) not yet defined.
- `extract_structured`'s heuristics need real design — regex-only extraction is fragile; routing through CyAI's `ModelGateway` for structured parsing is the stronger option since that infrastructure already exists.
- Dependencies (`pytesseract`, `pdf2image`, system `tesseract`/`poppler` binaries) aren't in this repo's environment yet — same class of gap as tonight's `dateutil` situation (no requirements manifest currently tracks cycom's Python deps at all, a separate pre-existing issue worth its own fix).
