import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Set, Tuple
from typing import Dict, Iterable, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tools.extract_placeholders import extract_placeholders


SECTION_TITLES = {
    "facility": "Facility Information",
    "heating": "Heating",
    "dhw": "Domestic Hot Water",
    "cooling": "Cooling",
    "ventilation": "Ventilation",
    "controls": "Controls",
    "notes": "Notes",
    "photos": "Photos",
    "checklist": "Checklist",
    "findings": "Checklist / Findings",
    "measures": "Measures",
    "unmapped": "Unmapped placeholders",
}


def _iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON must be an object: {path}")
    return data


def _match_rule(placeholder: str, rule: dict) -> bool:
    match = rule.get("match", {})
    match_type = match.get("type")
    if match_type == "exact":
        return placeholder == match.get("value")
    if match_type == "substring":
        value = match.get("value", "")
        return value in placeholder
    if match_type == "regex":
        pattern = match.get("pattern", "")
        return re.search(pattern, placeholder) is not None
    return False


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(REPO_ROOT, path)


def _resolve_section_id(placeholder: str) -> str:
    inner = placeholder.strip("{}").lower()
    if "heat" in inner:
        return "heating"
    if "dhw" in inner or "domestic hot water" in inner:
        return "dhw"
    if "cool" in inner:
        return "cooling"
    if "vent" in inner or "mua" in inner or "mau" in inner or "erv" in inner or "hrv" in inner:
        return "ventilation"
    if "bas" in inner or "control" in inner:
        return "controls"
    if "photo" in inner or "image" in inner:
        return "photos"
    if "note" in inner:
        return "notes"
    if "checklist" in inner or "finding" in inner:
        return "checklist"
    if "measure" in inner:
        return "measures"
    return "facility"


def _normalize_question(question: dict) -> dict:
    base = {
        "id": question["id"],
        "title": question.get("title", question["id"].replace("_", " ").title()),
        "type": question.get("type", "text"),
        "options": question.get("options", []),
        "placeholder_targets": question.get("placeholder_targets", []),
        "default": question.get("default"),
        "required": bool(question.get("required", False)),
        "help": question.get("help", ""),
        "rules": question.get("rules", []),
    }
    return base


def _merge_question(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    merged["placeholder_targets"] = sorted(
        set(existing.get("placeholder_targets", []))
        | set(incoming.get("placeholder_targets", []))
    )
    if not merged.get("options") and incoming.get("options"):
        merged["options"] = incoming["options"]
    return merged


def _make_unmapped_id(placeholder: str) -> str:
    inner = placeholder.strip("{}").strip()
    base = re.sub(r"[^a-z0-9]+", "_", inner.lower()).strip("_") or "unmapped"
    digest = hashlib.sha1(placeholder.encode("utf-8")).hexdigest()[:6]
    return f"{base}_{digest}"


def _keyword_placeholders(placeholders: Iterable[str], keywords: Iterable[str]) -> List[str]:
    results = []
    for placeholder in placeholders:
        inner = placeholder.strip("{}").lower()
        if any(keyword in inner for keyword in keywords):
            results.append(placeholder)
    return sorted(set(results))


def _build_findings_questions(placeholders: List[str]) -> List[dict]:
    return [
        {
            "id": "building_condition_overall",
            "title": "Overall building condition",
            "type": "single_select",
            "options": [
                {"label": "Good", "value": "good"},
                {"label": "Average", "value": "average"},
                {"label": "Poor", "value": "poor"},
                {"label": "Unknown", "value": "unknown"},
            ],
            "placeholder_targets": _keyword_placeholders(
                placeholders, ["condition", "overall condition"]
            ),
            "default": None,
            "required": False,
            "help": "General impression of the building condition.",
            "rules": [],
        },
        {
            "id": "safety_issues",
            "title": "Safety issues observed",
            "type": "multi_select",
            "options": [
                {"label": "Gas leak", "value": "gas_leak"},
                {"label": "Combustion air", "value": "combustion_air"},
                {"label": "Electrical", "value": "electrical"},
                {"label": "Asbestos suspected", "value": "asbestos_suspected"},
                {"label": "Mold", "value": "mold"},
                {"label": "Trip hazard", "value": "trip_hazard"},
                {"label": "Other", "value": "other"},
            ],
            "placeholder_targets": _keyword_placeholders(
                placeholders, ["safety", "hazard"]
            ),
            "default": None,
            "required": False,
            "help": "Document any safety hazards.",
            "rules": [],
        },
        {
            "id": "o_and_m_gaps",
            "title": "Operations and maintenance gaps",
            "type": "multi_select",
            "options": [
                {"label": "No schedules", "value": "no_schedules"},
                {"label": "No setbacks", "value": "no_setbacks"},
                {"label": "No VFD control", "value": "no_vfd_control"},
                {"label": "Sensors failed", "value": "sensors_failed"},
                {"label": "Overrides", "value": "overrides"},
                {"label": "Other", "value": "other"},
            ],
            "placeholder_targets": _keyword_placeholders(
                placeholders, ["maintenance", "o&m", "o and m", "operations"]
            ),
            "default": None,
            "required": False,
            "help": "Record any O&M gaps found during walkthrough.",
            "rules": [],
        },
        {
            "id": "photos",
            "title": "Photos",
            "type": "image_list",
            "options": [],
            "placeholder_targets": _keyword_placeholders(
                placeholders, ["photo", "image"]
            ),
            "default": None,
            "required": False,
            "help": "Attach relevant photos.",
            "rules": [],
        },
        {
            "id": "notes",
            "title": "Notes",
            "type": "notes",
            "options": [],
            "placeholder_targets": _keyword_placeholders(
                placeholders, ["notes", "site notes", "finding"]
            ),
            "default": None,
            "required": False,
            "help": "Additional findings or checklist notes.",
            "rules": [],
        },
    ]


def _build_measure_questions(options: List[dict], placeholders: List[str]) -> List[dict]:
    measure_targets = _keyword_placeholders(placeholders, ["measure", "measure block"])
    notes_targets = _keyword_placeholders(placeholders, ["measure notes", "measure note"])
    return [
        {
            "id": "selected_measures",
            "title": "Selected measures",
            "type": "multi_select",
            "options": options,
            "placeholder_targets": measure_targets,
            "default": None,
            "required": False,
            "help": "Select applicable measures.",
            "rules": [],
        },
        {
            "id": "measure_notes",
            "title": "Measure notes",
            "type": "notes",
            "options": [],
            "placeholder_targets": notes_targets,
            "default": None,
            "required": False,
            "help": "Additional measure-specific notes.",
            "rules": [],
        },
    ]


def _load_measure_options(template_json_path: str) -> List[dict]:
    try:
        data = _load_json(template_json_path)
    except FileNotFoundError:
        return [{"label": "TBD", "value": "tbd"}]
    measures = data.get("measures", {})
    if not isinstance(measures, dict) or not measures:
        return [{"label": "TBD", "value": "tbd"}]
    return [
        {"label": key, "value": key}
        for key in sorted(measures.keys())
    ]


def generate_schema(
    template_path: str,
    mapping_path: str,
    out_path: str,
    measure_catalog_path: Optional[str] = None,
) -> dict:
    resolved_template = _resolve_path(template_path)
    resolved_mapping = _resolve_path(mapping_path)
    resolved_out = _resolve_path(out_path)
    placeholders = extract_placeholders(resolved_template)["placeholders"]

    mapping = _load_json(resolved_mapping)
    rules = mapping.get("rules", [])
    option_sets = mapping.get("option_sets", {})
    measure_catalog = measure_catalog_path or mapping.get(
        "measure_catalog_path", "templates/template.level1.json"
    )

    questions_by_id: Dict[str, dict] = {}
    sections: Dict[str, List[str]] = defaultdict(list)
    warnings: List[str] = []
    mapped_placeholders: Set[str] = set()

    for rule in rules:
        question_data = rule.get("question", {})
        question_id = question_data.get("id")
        if not question_id:
            raise ValueError("Mapping rule is missing question id.")
        options: List[dict] = question_data.get("options", [])
        options_ref = question_data.get("options_ref")
        if options_ref:
            if options_ref not in option_sets:
                warnings.append(f"options_ref not found: {options_ref}")
            options = option_sets.get(options_ref, [])
        question = _normalize_question(
            {
                **question_data,
                "options": options,
                "placeholder_targets": [],
            }
        )
        if question_id in questions_by_id:
            questions_by_id[question_id] = _merge_question(
                questions_by_id[question_id], question
            )
        else:
            questions_by_id[question_id] = question
        section_id = question_data.get("section_id") or "facility"
        if question_id not in sections[section_id]:
            sections[section_id].append(question_id)
def generate_schema(template_path: str, mapping_path: str, out_path: str) -> dict:
    placeholders_data = extract_placeholders(template_path)
    placeholders = placeholders_data["placeholders"]

    mapping = _load_json(mapping_path)
    rules = mapping.get("rules", [])
    option_sets = mapping.get("option_sets", {})

    questions_by_id: Dict[str, dict] = {}
    sections: Dict[str, List[dict]] = defaultdict(list)

    for placeholder in placeholders:
        matched_rule: Optional[dict] = None
        for rule in rules:
            if _match_rule(placeholder, rule):
                matched_rule = rule
                break
        if matched_rule:
            question_id = matched_rule["question"]["id"]
            questions_by_id[question_id] = _merge_question(
                questions_by_id[question_id],
                {"placeholder_targets": [placeholder], "options": []},
            )
            mapped_placeholders.add(placeholder)
        else:
            question_id = _make_unmapped_id(placeholder)
            question = _normalize_question(
                {
                    "id": question_id,
                    "title": placeholder.strip("{}").strip() or placeholder,

        if matched_rule:
            question_data = matched_rule.get("question", {})
            question_id = question_data.get("id")
            if not question_id:
                raise ValueError("Mapping rule is missing question id.")
            options: List[dict] = question_data.get("options", [])
            options_ref = question_data.get("options_ref")
            if options_ref:
                options = option_sets.get(options_ref, [])
            question = _normalize_question(
                {
                    **question_data,
                    "options": options,
                    "placeholder_targets": [placeholder],
                }
            )
            if question_id in questions_by_id:
                questions_by_id[question_id] = _merge_question(
                    questions_by_id[question_id], question
                )
            else:
                questions_by_id[question_id] = question
            section_id = question_data.get("section_id") or _resolve_section_id(placeholder)
            sections[section_id].append(questions_by_id[question_id])
        else:
            inner = placeholder.strip("{}").strip()
            question_id = re.sub(r"[^a-z0-9]+", "_", inner.lower()).strip("_")
            if not question_id:
                question_id = "unmapped_placeholder"
            question = _normalize_question(
                {
                    "id": question_id,
                    "title": inner or placeholder,
                    "type": "text",
                    "options": [],
                    "placeholder_targets": [placeholder],
                    "default": None,
                    "required": False,
                    "help": "Unmapped placeholder.",
                    "rules": [],
                }
            )
            questions_by_id[question_id] = question
            sections["unmapped"].append(question_id)

    for rule in rules:
        matched = any(_match_rule(placeholder, rule) for placeholder in placeholders)
        if not matched:
            question_id = rule.get("question", {}).get("id", "unknown")
            warnings.append(f"No placeholders matched rule for question: {question_id}")

    findings_questions = _build_findings_questions(placeholders)
    for question in findings_questions:
        question_id = question["id"]
        questions_by_id[question_id] = question
        sections["findings"].append(question_id)

    measure_options = _load_measure_options(_resolve_path(measure_catalog))
    measures_questions = _build_measure_questions(measure_options, placeholders)
    for question in measures_questions:
        question_id = question["id"]
        questions_by_id[question_id] = question
        sections["measures"].append(question_id)

    serialized_sections = []
    for section_id in sorted(sections.keys()):
        question_ids = sorted(set(sections[section_id]))
        ordered_questions = [questions_by_id[qid] for qid in question_ids]
            if question_id in questions_by_id:
                questions_by_id[question_id] = _merge_question(
                    questions_by_id[question_id], question
                )
            else:
                questions_by_id[question_id] = question
            sections["unmapped"].append(questions_by_id[question_id])

    findings_questions = _build_findings_questions(placeholders)
    sections["findings"].extend(findings_questions)

    measure_options = _load_measure_options("templates/template.level1.json")
    measures_questions = _build_measure_questions(measure_options, placeholders)
    sections["measures"].extend(measures_questions)

    serialized_sections = []
    for section_id in sorted(sections.keys()):
        questions = sections[section_id]
        deduped = {question["id"]: question for question in questions}.values()
        ordered_questions = sorted(deduped, key=lambda item: item["id"])
        serialized_sections.append(
            {
                "id": section_id,
                "title": SECTION_TITLES.get(section_id, section_id.title()),
                "questions": ordered_questions,
            }
        )

    unmapped_placeholders = sorted(set(placeholders) - mapped_placeholders)
    stats = {
        "placeholder_count": len(placeholders),
        "mapped_placeholders_count": len(mapped_placeholders),
        "unmapped_placeholders_count": len(unmapped_placeholders),
        "question_count": len({q["id"] for q in questions_by_id.values()}),
        "section_count": len(serialized_sections),
    }

    schema = {
        "version": "1.0",
        "source_template": template_path,
        "generated_at": _iso_timestamp(),
        "placeholders": placeholders,
        "unmapped_placeholders": unmapped_placeholders,
        "warnings": warnings,
        "stats": stats,
        "sections": serialized_sections,
    }

    with open(resolved_out, "w", encoding="utf-8") as handle:
        "sections": serialized_sections,
    }

    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(schema, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    return schema


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Level 1 questionnaire schema.")
    parser.add_argument(
        "--template",
        default="templates/level1.docx",
        help="Path to the Word template",
    )
    parser.add_argument(
        "--mapping",
        default="schemas/level1_questionnaire.mapping.json",
        help="Path to the mapping JSON",
    )
    parser.add_argument(
        "--out",
        default="schemas/level1_questionnaire.schema.json",
        help="Output schema path",
    )
    parser.add_argument(
        "--measure-catalog",
        default="",
        help="Path to template.level1.json for measure options",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    measure_catalog = args.measure_catalog or None
    generate_schema(args.template, args.mapping, args.out, measure_catalog)
    generate_schema(args.template, args.mapping, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
