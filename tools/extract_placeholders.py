#!/usr/bin/env python3
import argparse
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Set
from xml.etree import ElementTree

PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}")
WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass(frozen=True)
class PlaceholderReport:
    template: str
    generated_at: str
    placeholders: List[str]
    blocks: List[str]

    @property
    def stats(self) -> dict:
        return {"total": len(self.placeholders), "blocks": len(self.blocks)}

    def to_dict(self) -> dict:
        return {
            "template": self.template,
            "generated_at": self.generated_at,
            "placeholders": self.placeholders,
            "blocks": self.blocks,
            "stats": self.stats,
        }


def _extract_placeholders_from_text(text: str) -> List[str]:
    return PLACEHOLDER_PATTERN.findall(text)


def _extract_text_from_paragraphs(root: ElementTree.Element) -> List[str]:
    texts: List[str] = []
    for paragraph in root.findall(".//w:p", WORD_NAMESPACE):
        runs = [node.text or "" for node in paragraph.findall(".//w:t", WORD_NAMESPACE)]
        if runs:
            texts.append("".join(runs))
        else:
            texts.append("")
    return texts


def _extract_from_xml(xml_bytes: bytes) -> List[str]:
    root = ElementTree.fromstring(xml_bytes)
    placeholders: List[str] = []
    for paragraph_text in _extract_text_from_paragraphs(root):
        placeholders.extend(_extract_placeholders_from_text(paragraph_text))
    return placeholders


def _collect_docx_xml_parts(docx_path: str) -> List[str]:
    with zipfile.ZipFile(docx_path) as archive:
        names = [name for name in archive.namelist() if name.startswith("word/")]
        targets = [
            name
            for name in names
            if name == "word/document.xml" or name.startswith("word/header") or name.startswith("word/footer")
        ]
    return targets


def _read_xml_parts(docx_path: str, part_names: Iterable[str]) -> List[bytes]:
    xml_parts: List[bytes] = []
    with zipfile.ZipFile(docx_path) as archive:
        for name in part_names:
            xml_parts.append(archive.read(name))
    return xml_parts


def _block_placeholders(placeholders: Iterable[str]) -> List[str]:
    blocks: List[str] = []
    for placeholder in placeholders:
        inner = placeholder.strip("{}").strip()
        if inner.lower().find("block") != -1 or inner in {"MEASURE_BLOCK", "MEASURE_SUMMARY_ROW"}:
            blocks.append(placeholder)
    return blocks


def extract_placeholders(docx_path: str) -> PlaceholderReport:
    part_names = _collect_docx_xml_parts(docx_path)
    placeholders: Set[str] = set()
    for xml_bytes in _read_xml_parts(docx_path, part_names):
        placeholders.update(_extract_from_xml(xml_bytes))

    if not placeholders:
        raise ValueError(f"No placeholders found in {docx_path}.")

    sorted_placeholders = sorted(placeholders)
    blocks = sorted(set(_block_placeholders(sorted_placeholders)))
    generated_at = datetime.now(timezone.utc).isoformat()

    return PlaceholderReport(
        template=docx_path,
        generated_at=generated_at,
        placeholders=sorted_placeholders,
        blocks=blocks,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract placeholders from a Word template.")
    parser.add_argument(
        "--template",
        default="templates/level1.docx",
        help="Path to the Word template",
    )
    parser.add_argument(
        "--out",
        help="Output JSON path (prints to stdout when omitted)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        report = extract_placeholders(args.template)
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    payload = report.to_dict()
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
    else:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
