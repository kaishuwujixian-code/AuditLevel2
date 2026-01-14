import json
import re
import sys
from typing import Iterable, List, Set

from docx import Document


PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}")


def _extract_from_text(text: str) -> List[str]:
    return PLACEHOLDER_PATTERN.findall(text)


def _extract_from_paragraphs(paragraphs: Iterable) -> List[str]:
    placeholders: List[str] = []
    for paragraph in paragraphs:
        text = "".join(run.text for run in paragraph.runs)
        placeholders.extend(_extract_from_text(text))
    return placeholders


def _extract_from_tables(tables: Iterable) -> List[str]:
    placeholders: List[str] = []
    for table in tables:
        for row in table.rows:
            for cell in row.cells:
                placeholders.extend(_extract_from_paragraphs(cell.paragraphs))
                placeholders.extend(_extract_from_tables(cell.tables))
    return placeholders


def _extract_from_section(section) -> List[str]:
    placeholders: List[str] = []
    placeholders.extend(_extract_from_paragraphs(section.header.paragraphs))
    placeholders.extend(_extract_from_tables(section.header.tables))
    placeholders.extend(_extract_from_paragraphs(section.footer.paragraphs))
    placeholders.extend(_extract_from_tables(section.footer.tables))
    return placeholders


def _block_placeholders(placeholders: Iterable[str]) -> List[str]:
    blocks: List[str] = []
    for placeholder in placeholders:
        inner = placeholder.strip("{}").strip()
        if inner.lower().find("block") != -1 or inner in {"MEASURE_BLOCK", "MEASURE_SUMMARY_ROW"}:
            blocks.append(placeholder)
    return blocks


def extract_placeholders(docx_path: str) -> dict:
    doc = Document(docx_path)
    placeholders: Set[str] = set()

    placeholders.update(_extract_from_paragraphs(doc.paragraphs))
    placeholders.update(_extract_from_tables(doc.tables))

    for section in doc.sections:
        placeholders.update(_extract_from_section(section))

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
