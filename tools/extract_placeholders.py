import argparse
import json
import os
import re
import sys
import zipfile
from typing import List, Set
from xml.etree import ElementTree

import tkinter as tk
from tkinter import filedialog


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
    return {"placeholders": sorted_placeholders}


def _select_docx_path(default_dir: str) -> str:
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Select Word template",
        initialdir=default_dir,
        filetypes=[("Word document", "*.docx")],
    )
    root.destroy()
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract placeholders from a Word template.")
    parser.add_argument(
        "--docx",
        default="templates/level1.docx",
        help="Path to the Word template",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Open a file dialog to select the Word template",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    docx_path = args.docx
    if args.ui:
        selected = _select_docx_path(os.path.dirname(docx_path) or ".")
        if not selected:
            raise SystemExit("No template selected.")
        docx_path = selected
    result = extract_placeholders(docx_path)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
