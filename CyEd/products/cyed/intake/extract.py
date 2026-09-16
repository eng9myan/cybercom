"""
Structured field extraction from document text — real regex/heuristics. Runs on
OCR output or a directly-posted transcript, so the "understanding" is real even
before an OCR provider is wired.
"""

import re

_DATE = re.compile(r"\b(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{4}[/\-.]\d{1,2}[/\-.]\d{1,2})\b")
_NUM = re.compile(r"\b(?:no|number|id)\b\.?\s*[:#]?\s*([A-Z0-9][A-Z0-9\-]{3,})", re.IGNORECASE)
_NAME = re.compile(r"\b(?:name|full name|student name)\s*[:\-]\s*([A-Za-z][A-Za-z '\-]{1,60})", re.IGNORECASE)
_AMOUNT = re.compile(r"\b(?:total|amount|paid)\s*[:$]?\s*\$?\s*([0-9][0-9,]*\.?\d{0,2})", re.IGNORECASE)


def extract_fields(text: str, doc_type: str = "other") -> dict:
    text = text or ""
    fields: dict = {}

    name = _NAME.search(text)
    if name:
        fields["name"] = name.group(1).strip()

    dates = _DATE.findall(text)
    if dates:
        # First date on a birth certificate is usually the DOB.
        fields["date_of_birth" if doc_type == "birth_certificate" else "date"] = dates[0]
        if len(dates) > 1:
            fields["dates"] = dates[:5]

    num = _NUM.search(text)
    if num:
        fields["document_number"] = num.group(1).strip()

    if doc_type == "receipt":
        amt = _AMOUNT.search(text)
        if amt:
            fields["amount"] = amt.group(1).replace(",", "")

    return fields
