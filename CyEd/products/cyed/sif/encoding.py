"""
Mapper dicts → SIF XML and SIF JSON.

The dict convention mirrors the SIF Association's own XML-to-JSON binding so
one structure serves both encodings:

  * ``"@Name"`` is an XML attribute.
  * ``"#text"`` is element text alongside attributes.
  * ``None`` values are dropped entirely — SIF distinguishes "absent" from
    "empty", and emitting ``<ACARAId/>`` would assert the school has a blank
    ACARA id rather than none on record.
  * A list becomes repeated sibling elements.

Written by hand rather than pulled from a library because the omission rule
above is the whole point, and a generic serialiser would emit the empty
elements this one deliberately drops.
"""

from xml.etree import ElementTree as ET

from products.cyed.sif.mappers import SIF_AU_NAMESPACE


def _prune(value):
    """
    Drop `None` recursively, and drop containers left empty by that pruning.

    A dict that pruned to nothing is itself absent — otherwise a student with
    no email would emit `<EmailList/>`, which claims an empty list of emails
    rather than no information.
    """
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            pruned = _prune(item)
            if pruned is None:
                continue
            cleaned[key] = pruned
        return cleaned or None
    if isinstance(value, list):
        cleaned = [p for p in (_prune(v) for v in value) if p is not None]
        return cleaned or None
    return value


def to_json(obj: dict) -> dict:
    """SIF JSON binding: the pruned dict as-is."""
    return _prune(obj) or {}


def _build(parent, key, value):
    if isinstance(value, dict):
        element = ET.SubElement(parent, key)
        for sub_key, sub_value in value.items():
            if sub_key.startswith("@"):
                element.set(sub_key[1:], str(sub_value))
            elif sub_key == "#text":
                element.text = str(sub_value)
            else:
                _build(element, sub_key, sub_value)
    elif isinstance(value, list):
        for item in value:
            _build(parent, key, item)
    else:
        element = ET.SubElement(parent, key)
        element.text = "" if value is None else str(value)


def to_xml(object_type: str, obj: dict) -> str:
    """One SIF object as namespaced XML."""
    pruned = _prune(obj) or {}
    root = ET.Element(object_type, {"xmlns": SIF_AU_NAMESPACE})
    for key, value in pruned.items():
        if key.startswith("@"):
            root.set(key[1:], str(value))
        elif key == "#text":
            root.text = str(value)
        else:
            _build(root, key, value)
    return ET.tostring(root, encoding="unicode")


def collection_to_xml(collection_name: str, object_type: str, objects) -> str:
    """A SIF collection: repeated objects under a plural wrapper element."""
    root = ET.Element(collection_name, {"xmlns": SIF_AU_NAMESPACE})
    for obj in objects:
        pruned = _prune(obj) or {}
        child = ET.SubElement(root, object_type)
        for key, value in pruned.items():
            if key.startswith("@"):
                child.set(key[1:], str(value))
            elif key == "#text":
                child.text = str(value)
            else:
                _build(child, key, value)
    return ET.tostring(root, encoding="unicode")
