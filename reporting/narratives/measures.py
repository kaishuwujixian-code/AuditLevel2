from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Mapping

from core.measure_catalog import MeasureCatalog, get_measure, load_measure_catalog
from reporting.narratives import (
    ensure_sentence,
    extract_first_sentence,
    further_investigation_sentence,
    has_meaningful_value,
)

BLOCK_PLACEHOLDERS = ["{MEASURE_BLOCK}", "{MEASURE_SUMMARY_ROW}"]
EXPECTED_INPUTS = {
    "{MEASURE_BLOCK}": {
        "fields": [
            "measures_block_override",
            "measure_overrides",
            "measures_selected",
            "selected_measures",
            "measures",
        ]
    },
    "{MEASURE_SUMMARY_ROW}": {
        "fields": [
            "measures_selected",
            "selected_measures",
            "measures",
        ]
    },
}


@dataclass(frozen=True)
class MeasuresContext:
    audit_level: str
    override_text: str | None
    selected_measures: List[str]
    measure_overrides: Dict[str, Dict[str, str]]

    @classmethod
    def from_project(
        cls,
        project: Dict[str, Any],
        *,
        catalog: MeasureCatalog,
        placeholders: Mapping[str, Any] | None = None,
    ) -> "MeasuresContext":
        selected_measures = _collect_selected_measures(project, catalog)
        return cls(
            audit_level="Level 1",
            override_text=_first_override_text(project, placeholders=placeholders),
            selected_measures=selected_measures,
            measure_overrides=_collect_measure_overrides(project, catalog),
        )


def render_block(
    project: Dict[str, Any],
    *,
    schema: Dict[str, Any] | None = None,
    mapping: Dict[str, Any] | None = None,
    catalog: MeasureCatalog | None = None,
    placeholders: Mapping[str, Any] | None = None,
) -> str:
    catalog = catalog or _load_measure_catalog_safe()
    context = MeasuresContext.from_project(project, catalog=catalog, placeholders=placeholders)
    if context.override_text:
        return context.override_text

    if not context.selected_measures:
        return (
            "No energy conservation measures are proposed as part of this Level 1 walk-through "
            "energy audit. Opportunities identified during the site visit may be further "
            "evaluated as part of a future detailed assessment."
        )

    ordered = _order_selected_measures(context.selected_measures, catalog)

    sections: List[str] = []
    for index, measure_id in enumerate(ordered, start=1):
        override = context.measure_overrides.get(measure_id, {})
        title = _resolve_measure_title(measure_id, override, catalog)
        narrative = _render_measure_narrative(
            measure_id,
            override,
            catalog,
        )
        sections.append(f"3.{index} {title}\n{narrative}")

    return "\n\n".join(sections)


def render_summary_row(
    project: Dict[str, Any],
    *,
    schema: Dict[str, Any] | None = None,
    mapping: Dict[str, Any] | None = None,
    catalog: MeasureCatalog | None = None,
    placeholders: Mapping[str, Any] | None = None,
) -> str:
    catalog = catalog or _load_measure_catalog_safe()
    count = count_selected_measures(project, catalog=catalog)
    if not count:
        return "Measures summary: none identified at this time."
    opportunities_label = "opportunity" if count == 1 else "opportunities"
    summary = ensure_sentence(f"Measures summary: {count} {opportunities_label} identified")
    follow_up = further_investigation_sentence("measure feasibility and savings potential")
    return " ".join([summary, follow_up])


def count_selected_measures(project: Dict[str, Any], *, catalog: MeasureCatalog | None = None) -> int:
    catalog = catalog or _load_measure_catalog_safe()
    return len(_collect_selected_measures(project, catalog))


def _load_measure_catalog_safe() -> MeasureCatalog:
    try:
        return _load_measure_catalog()
    except FileNotFoundError:
        return MeasureCatalog(measures={}, order=[], categories=[], legacy_key_map={})


@lru_cache(maxsize=1)
def _load_measure_catalog() -> MeasureCatalog:
    return load_measure_catalog()


def _first_override_text(
    project: Dict[str, Any],
    *,
    placeholders: Mapping[str, Any] | None = None,
) -> str | None:
    answers = project.get("answers", {}) if isinstance(project, dict) else {}
    override_text = None
    if isinstance(answers, dict):
        override_text = answers.get("measures_block_override") or answers.get("measures")
    if not override_text:
        override_text = project.get("measures_block_override")
    if not override_text and placeholders:
        override_text = placeholders.get("{MEASURE_BLOCK}")
    return str(override_text).strip() if override_text else None


def _collect_selected_measures(
    project: Dict[str, Any],
    catalog: MeasureCatalog,
) -> List[str]:
    raw = _collect_raw_measure_selections(project)
    return _normalize_measure_ids(raw, catalog)


def _collect_raw_measure_selections(project: Dict[str, Any]) -> List[Any]:
    selections: List[Any] = []
    answers = project.get("answers", {}) if isinstance(project, dict) else {}
    if isinstance(answers, dict):
        for key in ("measures_selected", "selected_measures", "measures"):
            value = answers.get(key)
            if value is not None:
                return _expand_measure_input(value)
    for key in ("selected_measures", "measures"):
        value = project.get(key)
        if value is not None:
            return _expand_measure_input(value)
    return selections


def _expand_measure_input(value: Any) -> List[Any]:
    if isinstance(value, list):
        return [item for item in value if has_meaningful_value(item)]
    if isinstance(value, str):
        return [item.strip() for item in _split_lines(value) if item.strip()]
    return []


def _normalize_measure_ids(
    selections: List[Any],
    catalog: MeasureCatalog,
) -> List[str]:
    normalized: List[str] = []
    seen = set()
    title_map = {
        str(measure.get("title", "")).strip().lower(): measure_id
        for measure_id, measure in catalog.measures.items()
        if str(measure.get("title", "")).strip()
    }
    for item in selections:
        measure_id = _extract_measure_id(item)
        if not measure_id:
            continue
        normalized_id = _map_measure_id(measure_id, catalog, title_map)
        if normalized_id and normalized_id not in seen:
            seen.add(normalized_id)
            normalized.append(normalized_id)
    return normalized


def _extract_measure_id(item: Any) -> str | None:
    if isinstance(item, dict):
        for key in ("id", "measure_id", "key", "name", "title"):
            value = item.get(key)
            if value:
                return str(value).strip()
        return None
    if isinstance(item, str):
        return item.strip()
    return None


def _map_measure_id(
    measure_id: str,
    catalog: MeasureCatalog,
    title_map: Dict[str, str],
) -> str:
    if measure_id in catalog.measures:
        return measure_id
    legacy_match = catalog.legacy_key_map.get(measure_id)
    if legacy_match:
        return legacy_match
    title_match = title_map.get(measure_id.lower())
    if title_match:
        return title_match
    return measure_id


def _order_selected_measures(
    selected: List[str],
    catalog: MeasureCatalog,
) -> List[str]:
    if not selected:
        return []
    return list(selected)


def _collect_measure_overrides(
    project: Dict[str, Any],
    catalog: MeasureCatalog,
) -> Dict[str, Dict[str, str]]:
    overrides: Dict[str, Dict[str, str]] = {}
    answers = project.get("answers", {}) if isinstance(project, dict) else {}
    title_map = {
        str(measure.get("title", "")).strip().lower(): measure_id
        for measure_id, measure in catalog.measures.items()
        if str(measure.get("title", "")).strip()
    }
    for source in (
        answers.get("measure_overrides") if isinstance(answers, dict) else None,
        project.get("measure_overrides"),
    ):
        if not isinstance(source, dict):
            continue
        for key, value in source.items():
            if not has_meaningful_value(key):
                continue
            normalized_key = _map_measure_id(str(key).strip(), catalog, title_map)
            overrides[normalized_key] = _normalize_override_entry(value)
    return overrides


def _normalize_override_entry(value: Any) -> Dict[str, str]:
    if isinstance(value, dict):
        title = value.get("title")
        narrative = value.get("narrative")
        notes = value.get("notes") or value.get("justification")
        payload = {
            "title": str(title).strip() if has_meaningful_value(title) else "",
            "narrative": str(narrative).strip() if has_meaningful_value(narrative) else "",
            "notes": str(notes).strip() if has_meaningful_value(notes) else "",
        }
        return {key: val for key, val in payload.items() if val}
    if has_meaningful_value(value):
        return {"narrative": str(value).strip()}
    return {}


def _resolve_measure_title(
    measure_id: str,
    override: Dict[str, str],
    catalog: MeasureCatalog,
) -> str:
    if override.get("title"):
        return override["title"]
    measure = get_measure(measure_id, catalog)
    return measure.get("title") or measure.get("name") or measure_id


def _render_measure_narrative(
    measure_id: str,
    override: Dict[str, str],
    catalog: MeasureCatalog,
) -> str:
    narrative_override = override.get("narrative")
    notes_override = override.get("notes")
    if narrative_override:
        narrative = narrative_override
    else:
        measure = get_measure(measure_id, catalog)
        narrative = _build_default_narrative(measure)
    notes_payload = notes_override or _extract_measure_notes(measure_id, catalog)
    if notes_payload:
        notes_section = _build_notes_section(notes_payload)
        if notes_section:
            narrative = "\n\n".join([narrative, notes_section]) if narrative else notes_section
    return narrative


def _build_default_narrative(measure: Dict[str, str]) -> str:
    existing = extract_first_sentence(measure.get("existing", ""))
    existing_detail = existing or "operates with conditions that were not fully confirmed"
    general_condition = _infer_general_condition(existing)
    existing_lead_in = _build_existing_lead_in(existing_detail)
    existing_paragraph = (
        f"{existing_lead_in} The existing system appears to be {general_condition}, "
        "with limited optimization or modern control strategies in place."
    )

    recommendation = extract_first_sentence(measure.get("retrofit", ""))
    recommendation_detail = _normalize_recommendation(recommendation)
    if not recommendation_detail:
        recommendation_detail = "targeted efficiency upgrades"
    recommendation_paragraph = (
        "Mann recommends implementing "
        f"{recommendation_detail} to improve system efficiency, operational reliability, "
        "and overall energy performance. This measure is considered appropriate for a "
        "Level 1 walk-through assessment and does not require detailed engineering at this stage."
    )

    key_inefficiency = _normalize_key_inefficiency(
        extract_first_sentence(measure.get("summary", ""))
    )
    rationale_paragraph = (
        "This measure is expected to reduce energy consumption by addressing "
        f"{key_inefficiency}, while also improving system controllability and long-term "
        "maintainability. Additional benefits may include reduced operating costs and improved "
        "occupant comfort."
    )

    sections = [
        "Existing Conditions\n" + ensure_sentence(existing_paragraph),
        "Recommended Retrofit / Scope\n" + ensure_sentence(recommendation_paragraph),
        "Rationale / Expected Benefit\n" + ensure_sentence(rationale_paragraph),
    ]
    return "\n\n".join(sections)


def _normalize_recommendation(recommendation: str) -> str:
    if not recommendation:
        return ""
    lowered = recommendation.strip()
    lowered_clean = lowered.lower()
    for prefix in (
        "mann recommends",
        "mann recommended",
        "mann proposes",
        "mann propose",
    ):
        if lowered_clean.startswith(prefix):
            lowered = lowered[len(prefix) :].strip(" :.-")
            lowered_clean = lowered.lower()
            break
    if lowered_clean.startswith("implementing "):
        lowered = lowered[len("implementing ") :].strip()
    if lowered.lower().startswith("that "):
        lowered = lowered[5:].strip()
    return lowered


def _normalize_key_inefficiency(summary: str) -> str:
    if not summary:
        return "identified operational inefficiencies"
    trimmed = summary.strip()
    lowered = trimmed.lower()
    if lowered.startswith(
        (
            "modernise",
            "modernize",
            "upgrade",
            "replace",
            "install",
            "implement",
            "retrofit",
            "optimize",
        )
    ):
        return "identified operational inefficiencies"
    return trimmed.rstrip(".")


def _infer_general_condition(existing: str) -> str:
    if not existing:
        return "functional"
    lowered = existing.lower()
    if any(term in lowered for term in ("aging", "aged", "obsolete", "past its", "end of life")):
        return "aging"
    if "fair" in lowered:
        return "fair"
    return "functional"


def _build_notes_section(notes_override: str) -> str:
    if not notes_override:
        return ""
    return "Notes / Dependencies\n" + ensure_sentence(str(notes_override).strip())


def _build_existing_lead_in(existing_detail: str) -> str:
    detail = existing_detail.strip()
    lowered = detail.lower()
    if lowered.startswith(("the building", "building", "there is", "there are")):
        return f"Based on the site walk-through, {detail}"
    return f"Based on the site walk-through, the building currently {detail}."


def _split_lines(value: str) -> list[str]:
    return [item for item in value.replace(",", "\n").splitlines()]


def _extract_measure_notes(
    measure_id: str,
    catalog: MeasureCatalog,
) -> str:
    measure = get_measure(measure_id, catalog)
    notes = measure.get("notes") or measure.get("dependencies")
    if not notes:
        return ""
    return str(notes).strip()
