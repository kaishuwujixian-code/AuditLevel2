from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Mapping, Sequence

from core.measure_catalog import MeasureCatalog, get_measure, load_measure_catalog
from reporting.narratives import (
    ensure_sentence,
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
        ]
    },
    "{MEASURE_SUMMARY_ROW}": {
        "fields": [
            "measures_selected",
            "selected_measures",
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

    structured_measures = collect_structured_measures(project)
    if structured_measures:
        return _render_structured_text_block(structured_measures)

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
        narrative = _render_measure_narrative(measure_id, override, catalog)
        block = _format_measure_block(index, title, narrative)
        sections.append(block)

    return "\n\n".join(section for section in sections if section)


def render_summary_row(
    project: Dict[str, Any],
    *,
    schema: Dict[str, Any] | None = None,
    mapping: Dict[str, Any] | None = None,
    catalog: MeasureCatalog | None = None,
    placeholders: Mapping[str, Any] | None = None,
) -> str:
    catalog = catalog or _load_measure_catalog_safe()
    structured_measures = collect_structured_measures(project)
    if structured_measures:
        summary = _render_summary_from_notes(structured_measures)
        if summary:
            return summary
    count = count_selected_measures(project, catalog=catalog)
    if not count:
        return "Measures summary: none identified at this time."
    opportunities_label = "opportunity" if count == 1 else "opportunities"
    summary = ensure_sentence(f"Measures summary: {count} {opportunities_label} identified")
    follow_up = further_investigation_sentence("measure feasibility and savings potential")
    return " ".join([summary, follow_up])


def count_selected_measures(project: Dict[str, Any], *, catalog: MeasureCatalog | None = None) -> int:
    catalog = catalog or _load_measure_catalog_safe()
    structured = collect_structured_measures(project)
    if structured:
        return len(structured)
    return len(_collect_selected_measures(project, catalog))


def collect_selected_measure_ids(
    project: Dict[str, Any],
    *,
    catalog: MeasureCatalog | None = None,
) -> List[str]:
    catalog = catalog or _load_measure_catalog_safe()
    return _collect_selected_measures(project, catalog)


def collect_structured_measures(project: Dict[str, Any]) -> List[Dict[str, Any]]:
    answers = project.get("answers", {}) if isinstance(project, dict) else {}
    measures = None
    if isinstance(answers, dict):
        measures = answers.get("measures")
    if measures is None:
        measures = project.get("measures") if isinstance(project, dict) else None
    if not isinstance(measures, list):
        return []
    normalized = [item for item in measures if isinstance(item, dict)]
    return [item for item in normalized if _has_measure_content(item)]


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
        override_text = answers.get("measures_block_override")
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
        for key in ("measures_selected", "selected_measures"):
            value = answers.get(key)
            if value is not None:
                return _expand_measure_input(value)
    for key in ("selected_measures", "measures"):
        value = project.get(key)
        if value is not None:
            return _expand_measure_input(value)
    return selections


def _has_measure_content(measure: Mapping[str, Any]) -> bool:
    for value in measure.values():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) == 0:
            continue
        return True
    return False


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
    category_order = [
        str(item.get("code", "")).strip()
        for item in catalog.categories
        if isinstance(item, dict)
    ]
    category_index = {code: idx for idx, code in enumerate(category_order)}
    catalog_index = {measure_id: idx for idx, measure_id in enumerate(catalog.order)}
    selected_index = {measure_id: idx for idx, measure_id in enumerate(selected)}

    def sort_key(measure_id: str) -> tuple:
        measure = catalog.measures.get(measure_id, {})
        category = measure.get("category", "") or ""
        return (
            category_index.get(category, len(category_index)),
            selected_index.get(measure_id, catalog_index.get(measure_id, len(catalog_index))),
            measure_id.lower(),
        )

    return sorted(selected, key=sort_key)


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
        existing = value.get("existing")
        retrofit = value.get("retrofit")
        notes = value.get("notes") or value.get("justification")
        payload = {
            "title": str(title).strip() if has_meaningful_value(title) else "",
            "narrative": str(narrative).strip() if has_meaningful_value(narrative) else "",
            "existing": str(existing).strip() if has_meaningful_value(existing) else "",
            "retrofit": str(retrofit).strip() if has_meaningful_value(retrofit) else "",
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
    existing_override = override.get("existing")
    retrofit_override = override.get("retrofit")
    if narrative_override:
        narrative = narrative_override
    else:
        measure = get_measure(measure_id, catalog)
        existing_text = existing_override or measure.get("existing", "")
        retrofit_text = retrofit_override or measure.get("retrofit", "")
        narrative = _build_catalog_narrative(existing_text, retrofit_text)
    if notes_override:
        notes_section = _build_notes_section(notes_override)
        if notes_section:
            narrative = "\n\n".join([narrative, notes_section]) if narrative else notes_section
    return narrative


def _build_catalog_narrative(existing: str, retrofit: str) -> str:
    sections: List[str] = []
    existing_text = existing.strip() if existing else ""
    retrofit_text = retrofit.strip() if retrofit else ""
    if existing_text:
        sections.append(f"Existing Conditions: {existing_text}")
    if retrofit_text:
        sections.append(f"Retrofit Recommendation: {retrofit_text}")
    return "\n\n".join(sections)


def _build_notes_section(notes_override: str) -> str:
    if not notes_override:
        return ""
    return "Notes: " + ensure_sentence(str(notes_override).strip())




def _format_measure_heading(index: int, title: str) -> str:
    clean_title = title.strip() if isinstance(title, str) else ""
    if not clean_title:
        clean_title = "Measure"
    return f"Measure {index} – {clean_title}"


def _format_measure_block(index: int, title: str, narrative: str) -> str:
    heading = _format_measure_heading(index, title)
    if narrative and narrative.strip():
        return "\n\n".join([heading, narrative.strip()])
    return heading


def _render_structured_text_block(measures: List[Dict[str, Any]]) -> str:
    sections = []
    for index, measure in enumerate(measures, start=1):
        title = str(measure.get("measure_title", "")).strip() or "Measure"
        existing = str(measure.get("existing_conditions", "")).strip()
        retrofit = str(measure.get("retrofit_conditions", "")).strip()
        parts = [_format_measure_heading(index, title)]
        if existing:
            parts.append(f"Existing Conditions: {existing}")
        if retrofit:
            parts.append(f"Retrofit Conditions: {retrofit}")
        sections.append("\n\n".join(parts))
    return "\n\n".join(section for section in sections if section)


def _render_summary_from_notes(measures: List[Dict[str, Any]]) -> str:
    notes: List[str] = []
    for measure in measures:
        note = str(measure.get("notes", "")).strip()
        if note:
            notes.append(note)
    return "\n".join(notes)


def _split_lines(value: str) -> list[str]:
    return [item for item in value.replace(",", "\n").splitlines()]
