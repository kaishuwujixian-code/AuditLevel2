import argparse
import json
import os
from typing import List, Set


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


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


def validate_schema(schema_path: str, placeholders_path: str, mapping_path: str) -> None:
    schema = _load_json(_resolve_path(schema_path))
    placeholders_data = _load_json(_resolve_path(placeholders_path))
    mapping = _load_json(_resolve_path(mapping_path))

    placeholders = placeholders_data.get("placeholders", [])
    if not isinstance(placeholders, list):
        raise ValueError("placeholders manifest must include a list at placeholders.")
    placeholder_set: Set[str] = set(placeholders)

    option_sets = mapping.get("option_sets", {})

    sections = schema.get("sections", [])
    if not isinstance(sections, list):
        raise ValueError("schema.sections must be a list.")

    question_ids: Set[str] = set()

    for section in sections:
        section_id = section.get("id")
        if not section_id:
            raise ValueError("Section missing id.")
        questions = section.get("questions", [])
        if not isinstance(questions, list):
            raise ValueError(f"Section {section_id} questions must be a list.")
        for question in questions:
            question_id = question.get("id")
            if not question_id:
                raise ValueError(f"Question missing id in section {section_id}.")
            if question_id in question_ids:
                raise ValueError(f"Duplicate question id: {question_id}")
            question_ids.add(question_id)

            placeholder_targets = question.get("placeholder_targets", [])
            if not isinstance(placeholder_targets, list):
                raise ValueError(
                    f"Question {question_id} placeholder_targets must be a list."
                )
            unknown_targets = [
                placeholder
                for placeholder in placeholder_targets
                if placeholder not in placeholder_set
            ]
            if unknown_targets:
                raise ValueError(
                    f"Question {question_id} has unknown placeholders: {', '.join(unknown_targets)}"
                )

            options_ref = question.get("options_ref")
            if options_ref and options_ref not in option_sets:
                raise ValueError(
                    f"Question {question_id} references unknown options_ref: {options_ref}"
                )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Level 1 questionnaire schema.")
    parser.add_argument(
        "--schema",
        default="schemas/level1_questionnaire.schema.json",
        help="Path to schema JSON",
    )
    parser.add_argument(
        "--placeholders",
        default="schemas/placeholders.level1.json",
        help="Path to placeholders manifest",
    )
    parser.add_argument(
        "--mapping",
        default="schemas/level1_questionnaire.mapping.json",
        help="Path to mapping JSON",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    validate_schema(args.schema, args.placeholders, args.mapping)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
