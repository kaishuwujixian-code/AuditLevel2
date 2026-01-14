import argparse
import json
import os
import sys
from typing import Dict, List, Set

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.extract_placeholders import extract_placeholders


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(REPO_ROOT, path)


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON must be an object: {path}")
    return data


def _ensure_sorted(items: List[str], label: str) -> None:
    if items != sorted(items):
        raise ValueError(f"{label} must be sorted by id.")


def validate_schema(schema_path: str, template_path: str) -> None:
    schema = _load_json(_resolve_path(schema_path))
    placeholders = extract_placeholders(_resolve_path(template_path))["placeholders"]
    placeholder_set: Set[str] = set(placeholders)

    sections = schema.get("sections", [])
    if not isinstance(sections, list):
        raise ValueError("schema.sections must be a list.")

    section_ids: List[str] = []
    question_ids: Set[str] = set()

    for section in sections:
        section_id = section.get("id")
        if not section_id:
            raise ValueError("Section missing id.")
        section_ids.append(section_id)
        questions = section.get("questions", [])
        if not isinstance(questions, list):
            raise ValueError(f"Section {section_id} questions must be a list.")
        question_id_list: List[str] = []
        for question in questions:
            question_id = question.get("id")
            if not question_id:
                raise ValueError(f"Question missing id in section {section_id}.")
            if question_id in question_ids:
                raise ValueError(f"Duplicate question id: {question_id}")
            question_ids.add(question_id)
            question_id_list.append(question_id)

            placeholder_targets = question.get("placeholder_targets", [])
            if not isinstance(placeholder_targets, list):
                raise ValueError(f"Question {question_id} placeholder_targets must be a list.")
            unknown_targets = [
                placeholder for placeholder in placeholder_targets if placeholder not in placeholder_set
            ]
            if unknown_targets:
                raise ValueError(
                    f"Question {question_id} has unknown placeholders: {', '.join(unknown_targets)}"
                )

        _ensure_sorted(question_id_list, f"Questions in section {section_id}")

    _ensure_sorted(section_ids, "Sections")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Level 1 questionnaire schema.")
    parser.add_argument(
        "--schema",
        default="schemas/level1_questionnaire.schema.json",
        help="Path to schema JSON",
    )
    parser.add_argument(
        "--template",
        default="templates/level1.docx",
        help="Path to Word template",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    validate_schema(args.schema, args.template)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
