import argparse
import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

SECTION_TITLES = {
    "controls": "Controls",
    "cooling": "Cooling",
    "dhw": "Domestic Hot Water",
    "facility": "Facility Information",
    "findings": "Findings",
    "heating": "Heating",
    "measures": "Measures",
    "placeholders_raw": "Template Fields",
    "ventilation": "Ventilation",
}

SECTION_ORDER = [
    "facility",
    "placeholders_raw",
    "heating",
    "cooling",
    "dhw",
    "ventilation",
    "controls",
    "measures",
    "findings",
]

BLOCK_PLACEHOLDERS = {
    "{Central Heating/Cooling Systems block}",
    "{Central Ventilation System Block}",
    "{DHW System Block}",
    "{MEASURE_BLOCK}",
    "{MEASURE_SUMMARY_ROW}",
    "{Miscellaneous Block}",
}


def _iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON must be an object: {path}")
    return data


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(REPO_ROOT, path)


def _normalize_key(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", text.strip().lower())
    return normalized.strip("_")


def _make_unmapped_id(placeholder: str, used_ids: set) -> str:
    inner = placeholder.strip("{}").strip()
    base = _normalize_key(inner) or "unmapped"
    candidate = base
    counter = 2
    while candidate in used_ids:
        candidate = f"{base}_{counter}"
        counter += 1
    used_ids.add(candidate)
    return candidate


def _normalize_options(options: Optional[list]) -> List[dict]:
    if not options:
        return []
    normalized = []
    for item in options:
        if isinstance(item, dict):
            normalized.append(item)
        else:
            normalized.append({"label": str(item), "value": item})
    return normalized


def _normalize_question(question: dict) -> dict:
    title = question.get("title") or question["id"].replace("_", " ").title()
    return {
        "id": question["id"],
        "title": title,
        "type": question.get("type", "text"),
        "section_id": question.get("section_id", "facility"),
        "options": _normalize_options(question.get("options", [])),
        "options_ref": question.get("options_ref"),
        "placeholder_targets": question.get("placeholder_targets", []),
        "help": question.get("help", ""),
        "required": bool(question.get("required", False)),
    }


def _merge_question(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    merged["placeholder_targets"] = sorted(
        set(existing.get("placeholder_targets", []))
        | set(incoming.get("placeholder_targets", []))
    )
    if not merged.get("options") and incoming.get("options"):
        merged["options"] = incoming["options"]
    if not merged.get("options_ref") and incoming.get("options_ref"):
        merged["options_ref"] = incoming["options_ref"]
    return merged


def _match_rule(placeholder: str, rule: dict) -> bool:
    match = rule.get("match", {})
    match_type = match.get("type")
    if match_type == "exact":
        return placeholder == match.get("value")
    if match_type == "substring":
        return match.get("value", "") in placeholder
    if match_type == "regex":
        pattern = match.get("pattern", "")
        return re.search(pattern, placeholder) is not None
    return False


def generate_schema(placeholders_path: str, mapping_path: str, out_path: str) -> dict:
    placeholders_data = _load_json(_resolve_path(placeholders_path))
    placeholders = placeholders_data.get("placeholders", [])
    if not isinstance(placeholders, list):
        raise ValueError("placeholders manifest must include a list at placeholders.")

    mapping = _load_json(_resolve_path(mapping_path))
    rules = mapping.get("rules", [])
    option_sets = mapping.get("option_sets", {})

    questions_by_id: Dict[str, dict] = {}
    sections: Dict[str, List[str]] = {}
    mapped_placeholders = set()
    used_question_ids = set()

    for placeholder in placeholders:
        matched_rule = None
        for rule in rules:
            if _match_rule(placeholder, rule):
                matched_rule = rule
                break

        if matched_rule:
            question_data = dict(matched_rule.get("question", {}))
            question_id = question_data.get("id")
            if not question_id:
                raise ValueError("Mapping rule is missing question id.")
            used_question_ids.add(question_id)

            options_ref = question_data.get("options_ref")
            if options_ref:
                question_data["options"] = option_sets.get(options_ref, [])

            question = _normalize_question(
                {
                    **question_data,
                    "placeholder_targets": [placeholder],
                }
            )
            if question_id in questions_by_id:
                questions_by_id[question_id] = _merge_question(
                    questions_by_id[question_id], question
                )
            else:
                questions_by_id[question_id] = question

            section_id = question.get("section_id", "facility")
            sections.setdefault(section_id, [])
            if question_id not in sections[section_id]:
                sections[section_id].append(question_id)
            mapped_placeholders.add(placeholder)
        else:
            if placeholder in BLOCK_PLACEHOLDERS:
                continue
            question_id = _make_unmapped_id(placeholder, used_question_ids)
            question = _normalize_question(
                {
                    "id": question_id,
                    "title": placeholder.strip("{}").strip() or placeholder,
                    "type": "text",
                    "section_id": "placeholders_raw",
                    "options": [],
                    "placeholder_targets": [placeholder],
                    "help": "Unmapped placeholder.",
                    "required": False,
                }
            )
            questions_by_id[question_id] = question
            sections.setdefault("placeholders_raw", []).append(question_id)

    serialized_sections = []
    ordered_section_ids = [
        section_id for section_id in SECTION_ORDER if section_id in sections
    ]
    ordered_section_ids.extend(
        section_id
        for section_id in sorted(sections.keys())
        if section_id not in ordered_section_ids
    )
    for section_id in ordered_section_ids:
        question_ids = sorted(set(sections[section_id]))
        ordered_questions = [questions_by_id[qid] for qid in question_ids]
        serialized_sections.append(
            {
                "id": section_id,
                "title": SECTION_TITLES.get(section_id, section_id.title()),
                "questions": ordered_questions,
            }
        )

    stats = {
        "total_placeholders": len(placeholders),
        "mapped": len(mapped_placeholders),
        "unmapped": len(placeholders) - len(mapped_placeholders),
    }

    schema = {
        "version": "1.0",
        "source_placeholders": placeholders_path,
        "generated_at": _iso_timestamp(),
        "placeholders": placeholders,
        "sections": serialized_sections,
        "stats": stats,
    }

    with open(_resolve_path(out_path), "w", encoding="utf-8") as handle:
        json.dump(schema, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    return schema


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Level 1 questionnaire schema.")
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
    parser.add_argument(
        "--out",
        default="schemas/level1_questionnaire.schema.json",
        help="Output schema path",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    generate_schema(args.placeholders, args.mapping, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
