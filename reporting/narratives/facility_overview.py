from dataclasses import dataclass
from typing import Any, Dict

from reporting.narratives import (
    ensure_sentence,
    format_option_values,
    has_meaningful_value,
    human_join,
    stringify_value,
)

PROVINCE_ABBREVIATIONS = {
    "alberta": "AB",
    "british columbia": "BC",
    "manitoba": "MB",
    "new brunswick": "NB",
    "newfoundland and labrador": "NL",
    "nova scotia": "NS",
    "northwest territories": "NT",
    "nunavut": "NU",
    "ontario": "ON",
    "prince edward island": "PE",
    "quebec": "QC",
    "saskatchewan": "SK",
    "yukon": "YT",
}

BLOCK_PLACEHOLDERS: list[str] = []


@dataclass(frozen=True)
class FacilityOverviewContext:
    answers: Dict[str, Any]

    @classmethod
    def from_project(cls, project: Dict[str, Any]) -> "FacilityOverviewContext":
        answers = project.get("answers", {}) if isinstance(project, dict) else {}
        if not isinstance(answers, dict):
            answers = {}
        return cls(answers=answers)


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = FacilityOverviewContext.from_project(project)
    if not context.answers:
        return ""
    return _build_facility_overview(context.answers, mapping=mapping)


def apply_facility_placeholders(
    project: Dict[str, Any], placeholder_map: Dict[str, str]
) -> None:
    if not isinstance(project, dict):
        return
    answers = project.get("answers", {})
    if not isinstance(answers, dict):
        return

    def set_if_missing(placeholder: str, value: Any) -> None:
        if not has_meaningful_value(value):
            return
        existing = placeholder_map.get(placeholder, "")
        if not existing.strip():
            placeholder_map[placeholder] = stringify_value(value) or ""

    set_if_missing("{Property Address1}", answers.get("site_address"))

    district_value = answers.get("district") or answers.get("city")
    if not has_meaningful_value(district_value):
        district_value = "the surrounding area"
    set_if_missing("{District}", district_value)

    set_if_missing("{Province}", answers.get("province"))

    province_abbreviation = answers.get("province_abbreviation")
    if not has_meaningful_value(province_abbreviation):
        province = answers.get("province")
        if isinstance(province, str):
            province_abbreviation = PROVINCE_ABBREVIATIONS.get(province.strip().lower())
    set_if_missing("{Province Abbreviation}", province_abbreviation)

    set_if_missing("{Number of Floors}", answers.get("number_of_floors"))
    set_if_missing("{Number of Suites}", answers.get("number_of_suites"))
    set_if_missing("{Date Constructed}", answers.get("date_constructed") or "an unknown year")

    arch_condition_value = answers.get("architectural_condition")
    if has_meaningful_value(arch_condition_value):
        labels = format_option_values("building.arch_condition", arch_condition_value)
        if labels and not _contains_unknown(labels):
            set_if_missing("{Architectural Condition}", human_join(labels))
        else:
            set_if_missing("{Architectural Condition}", arch_condition_value)
    else:
        set_if_missing("{Architectural Condition}", "Based on a visual review.")

    facility_overview = _build_facility_overview(answers)
    set_if_missing("{Facility Overview}", facility_overview)


def _build_facility_overview(answers: Dict[str, Any], mapping: Dict[str, Any] | None = None) -> str:
    address_parts = [
        str(value).strip()
        for value in [
            answers.get("site_address"),
            answers.get("district") or answers.get("city"),
            answers.get("province"),
        ]
        if has_meaningful_value(value)
    ]
    if address_parts:
        location_text = "at " + ", ".join(address_parts)
    else:
        location_text = "at the facility location"

    date_constructed = answers.get("date_constructed")
    date_text = "constructed in an unknown year"
    if has_meaningful_value(date_constructed):
        date_str = str(date_constructed).strip()
        if _is_year(date_str):
            date_text = f"constructed in {date_str}"
        else:
            date_text = f"constructed in {date_str}"

    arch_condition_value = answers.get("architectural_condition")
    if has_meaningful_value(arch_condition_value):
        labels = format_option_values("building.arch_condition", arch_condition_value, mapping=mapping)
        if labels and not _contains_unknown(labels):
            condition_text = f"The architectural condition is described as {human_join(labels)}."
        else:
            condition_text = ensure_sentence(str(arch_condition_value))
    else:
        condition_text = "Architectural condition observations are based on a visual review only."

    return " ".join(
        [
            ensure_sentence(f"The facility is located {location_text}"),
            ensure_sentence(f"It was {date_text}"),
            condition_text,
        ]
    )


def _contains_unknown(values: list[str]) -> bool:
    return any("unknown" in value.lower() for value in values)


def _is_year(value: str) -> bool:
    return bool(value.isdigit() and len(value) == 4)
