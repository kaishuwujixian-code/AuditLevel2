import json
import re
import sys
import zipfile
from typing import Iterable, List, Set
from xml.etree import ElementTree


PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}")
WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _extract_from_text(text: str) -> List[str]:
    return PLACEHOLDER_PATTERN.findall(text)


def _extract_from_xml(xml_bytes: bytes) -> List[str]:
    placeholders: List[str] = []
    root = ElementTree.fromstring(xml_bytes)
    for paragraph in root.findall(".//w:p", WORD_NAMESPACE):
        text_parts = [node.text or "" for node in paragraph.findall(".//w:t", WORD_NAMESPACE)]
        if not text_parts:
            continue
        text = "".join(text_parts)
        placeholders.extend(_extract_from_text(text))
    return placeholders


def _block_placeholders(placeholders: Iterable[str]) -> List[str]:
    blocks: List[str] = []
    for placeholder in placeholders:
        inner = placeholder.strip("{}").strip()
        if inner.lower().find("block") != -1 or inner in {"MEASURE_BLOCK", "MEASURE_SUMMARY_ROW"}:
            blocks.append(placeholder)
    return blocks


def extract_placeholders(docx_path: str) -> dict:
    placeholders: Set[str] = set()
    with zipfile.ZipFile(docx_path) as archive:
        for name in archive.namelist():
            if not name.startswith("word/"):
                continue
            if name == "word/document.xml" or name.startswith("word/header") or name.startswith("word/footer"):
                xml_bytes = archive.read(name)
                placeholders.update(_extract_from_xml(xml_bytes))

    if not placeholders:
        raise ValueError(f"No placeholders found in {docx_path}.")

    sorted_placeholders = sorted(placeholders)
    blocks = sorted(set(_block_placeholders(sorted_placeholders)))
    return {"placeholders": sorted_placeholders, "blocks": blocks}


def main() -> int:
    docx_path = "templates/level1.docx"
    result = extract_placeholders(docx_path)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
