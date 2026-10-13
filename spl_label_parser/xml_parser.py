"""Conservative, local extraction of sections from HL7 v3 FDA SPL XML.

Extracts source content; does not validate FDA schemas or provide clinical advice.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

NS = "urn:hl7-org:v3"
LOINC_OID = "2.16.840.1.113883.6.1"
MAX_XML_BYTES = 5 * 1024 * 1024

SECTION_TYPES = {
    "34066-1": "boxed_warning",
    "34067-9": "indications_and_usage",
    "34070-3": "contraindications",
    "34068-7": "dosage_and_administration",
    "34084-4": "adverse_reactions",
    "34073-7": "drug_interactions",
    "43685-7": "warnings_and_precautions",
    "34071-1": "warnings",
}


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def _identifier(root: ET.Element, name: str) -> str | None:
    element = root.find(f"{{{NS}}}{name}")
    return (element.get("root") or element.get("extension")) if element is not None else None


def parse_spl(xml: bytes | str) -> dict[str, Any]:
    """Extract document metadata and sections from a UTF-8 SPL document.

    Raises ValueError on oversize, malformed, non-SPL, or DTD-bearing input.
    """
    if isinstance(xml, bytes):
        if len(xml) > MAX_XML_BYTES:
            raise ValueError("SPL XML exceeds the 5 MiB size limit")
        try:
            source = xml.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("SPL XML must be UTF-8 encoded") from exc
    elif isinstance(xml, str):
        if len(xml.encode("utf-8")) > MAX_XML_BYTES:
            raise ValueError("SPL XML exceeds the 5 MiB size limit")
        source = xml.lstrip("\ufeff")
    else:
        raise TypeError("SPL XML must be bytes or text")

    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", source, re.IGNORECASE):
        raise ValueError("DOCTYPE and ENTITY declarations are not allowed")
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise ValueError("Malformed SPL XML") from exc
    if root.tag != f"{{{NS}}}document":
        raise ValueError("Expected an HL7 v3 SPL document root")

    sections: list[dict[str, str]] = []
    for section in root.iter(f"{{{NS}}}section"):
        code_el = section.find(f"{{{NS}}}code")
        code = code_el.get("code", "") if code_el is not None else ""
        code_system = code_el.get("codeSystem", "") if code_el is not None else ""
        category = SECTION_TYPES.get(code, "other") if code_system == LOINC_OID else "other"
        sections.append({
            "code": code,
            "code_system": code_system,
            "category": category,
            "title": _text(section.find(f"{{{NS}}}title")),
            "text": _text(section.find(f"{{{NS}}}text")),
        })

    version = root.find(f"{{{NS}}}versionNumber")
    effective = root.find(f"{{{NS}}}effectiveTime")
    return {
        "document_id": _identifier(root, "id"),
        "set_id": _identifier(root, "setId"),
        "version_number": version.get("value") if version is not None else None,
        "effective_time": effective.get("value") if effective is not None else None,
        "title": _text(root.find(f"{{{NS}}}title")),
        "sections": sections,
    }


def parse_spl_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.stat().st_size > MAX_XML_BYTES:
        raise ValueError("SPL XML exceeds the 5 MiB size limit")
    return parse_spl(path.read_bytes())
