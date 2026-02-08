from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, List


BLOCK_PLACEHOLDERS = {
    "{Central Cooling Systems block}",
    "{Central Heating Systems block}",
    "{Central Ventilation System Block}",
    "{DHW System Block}",
    "{MEASURE_BLOCK}",
    "{MEASURE_SUMMARY_ROW}",
    "{Miscellaneous Block}",
    "{FINDINGS_BLOCK}",
}


def load_questionnaire_schema(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Questionnaire schema must be a JSON object.")
    return data


def iter_schema_questions(schema: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for section in schema.get("sections", []):
        questions = section.get("questions", [])
        if isinstance(questions, list):
            for question in questions:
                if isinstance(question, dict):
                    yield question


def collect_template_placeholders(schema: Dict[str, Any]) -> List[str]:
    placeholders = schema.get("placeholders", [])
    if not isinstance(placeholders, list):
        return []
    mapped = set()
    for question in iter_schema_questions(schema):
        for target in question.get("placeholder_targets", []) or []:
            mapped.add(target)
    return [
        placeholder
        for placeholder in placeholders
        if placeholder not in mapped and not _is_block_placeholder(placeholder)
    ]


def apply_answers_to_project(
    project_data: Dict[str, Any],
    answers: Dict[str, Any],
    schema: Dict[str, Any],
    template_fields: Dict[str, Any] | None = None,
) -> None:
    project_data["answers"] = answers
    placeholders = build_placeholder_map(schema, answers, template_fields)
    if placeholders:
        existing = project_data.get("placeholders", {})
        merged = dict(existing) if isinstance(existing, dict) else {}
        merged.update(placeholders)
        project_data["placeholders"] = merged
    _sync_project_info(project_data, answers)


def build_placeholder_map(
    schema: Dict[str, Any],
    answers: Dict[str, Any],
    template_fields: Dict[str, Any] | None = None,
) -> Dict[str, str]:
    placeholders: Dict[str, str] = {}
    for question in iter_schema_questions(schema):
        question_id = question.get("id")
        if not question_id or question_id not in answers:
            continue
        value = answers.get(question_id)
        string_value = _stringify_value(value)
        if string_value is None:
            continue
        for placeholder in question.get("placeholder_targets", []) or []:
            placeholders[placeholder] = string_value

    for placeholder, value in (template_fields or {}).items():
        string_value = _stringify_value(value)
        if string_value is not None and string_value.strip():
            placeholders[placeholder] = string_value
    return placeholders


def _stringify_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)


def _is_block_placeholder(placeholder: str) -> bool:
    if placeholder in BLOCK_PLACEHOLDERS:
        return True
    if not placeholder.startswith("{") or not placeholder.endswith("}"):
        return False
    inner_text = placeholder[1:-1].strip().lower()
    return inner_text.endswith(" block") or inner_text.endswith("_block")


def _sync_project_info(project_data: Dict[str, Any], answers: Dict[str, Any]) -> None:
    project_info = project_data.get("project_info", {})
    if not isinstance(project_info, dict):
        project_info = {}
    for key in ("client_name", "site_address", "building_name", "report_date", "prepared_by"):
        value = answers.get(key)
        if value is not None:
            project_info[key] = value
    project_data["project_info"] = project_info


def normalize_placeholder_id(placeholder: str, used_ids: set[str]) -> str:
    inner = placeholder.strip("{}").strip()
    normalized = re.sub(r"[^a-z0-9]+", "_", inner.lower()).strip("_")
    candidate = normalized or "placeholder"
    counter = 2
    while candidate in used_ids:
        candidate = f"{normalized}_{counter}"
        counter += 1
    used_ids.add(candidate)
    return candidate
