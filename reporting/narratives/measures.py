import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Tuple

from reporting.narratives import (
    ensure_sentence,
    extract_first_sentence,
    further_investigation_sentence,
    has_meaningful_value,
    uncertainty_sentence,
)

DEFAULT_MEASURE_CATALOG_PATH = os.path.join("templates", "template.level1.json")

BLOCK_PLACEHOLDERS = ["{MEASURE_BLOCK}", "{MEASURE_SUMMARY_ROW}"]
EXPECTED_INPUTS = {
    "{MEASURE_BLOCK}": {
        "fields": [
            "measures_block_override",
            "measures",
            "selected_measures",
        ]
    },
    "{MEASURE_SUMMARY_ROW}": {
        "fields": [
            "selected_measures",
            "measures",
        ]
    },
}


@dataclass(frozen=True)
class MeasuresContext:
    audit_level: str
    confidence: str
    unknown_policy: str
    override_text: str | None
    measures: List[Any]

    @classmethod
    def from_project(cls, project: Dict[str, Any]) -> "MeasuresContext":
        return cls(
            audit_level="L1",
            confidence="moderate",
            unknown_policy="soft",
            override_text=_first_override_text(project),
            measures=_collect_measures(project),
        )


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = MeasuresContext.from_project(project)
    if context.override_text:
        return context.override_text

    if not context.measures:
        return uncertainty_sentence(
            f"no energy conservation measures were identified for this {context.audit_level} review"
        )

    catalog = _load_measure_catalog()
    lines = ["The following measures are recommended for consideration:"]
    for measure in context.measures:
        title, justification = _split_measure_entry(measure, catalog)
        lines.append(f"• {title} — {justification}")

    return "\n".join(lines)


def render_summary_row(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = MeasuresContext.from_project(project)
    if not context.measures:
        return "Measures summary: none identified at this time."
    count = len(context.measures)
    opportunities_label = "opportunity" if count == 1 else "opportunities"
    summary = ensure_sentence(f"Measures summary: {count} {opportunities_label} identified")
    follow_up = further_investigation_sentence("measure feasibility and savings potential")
    return " ".join([summary, follow_up])


def _first_override_text(project: Dict[str, Any]) -> str | None:
    answers = project.get("answers", {}) if isinstance(project, dict) else {}
    override_text = None
    if isinstance(answers, dict):
        override_text = answers.get("measures_block_override") or answers.get("measures")
    if not override_text:
        override_text = project.get("measures_block_override")
    return str(override_text).strip() if override_text else None


def _collect_measures(project: Dict[str, Any]) -> list[Any]:
    measures = []
    selected_measures = project.get("selected_measures") if isinstance(project, dict) else None
    if isinstance(selected_measures, list):
        measures = [item for item in selected_measures if has_meaningful_value(item)]
    if not measures:
        answers = project.get("answers", {}) if isinstance(project, dict) else {}
        if isinstance(answers, dict):
            answer_measures = answers.get("selected_measures") or answers.get("measures")
            if isinstance(answer_measures, list):
                measures = [item for item in answer_measures if has_meaningful_value(item)]
            elif isinstance(answer_measures, str):
                measures = [
                    item.strip()
                    for item in _split_lines(answer_measures)
                    if item.strip()
                ]
    return measures


def _split_lines(value: str) -> list[str]:
    return [item for item in value.replace(",", "\n").splitlines()]


@lru_cache(maxsize=1)
def _load_measure_catalog(
    catalog_path: str = DEFAULT_MEASURE_CATALOG_PATH,
) -> Dict[str, Dict[str, str]]:
    if not catalog_path or not os.path.isfile(catalog_path):
        return {}
    with open(catalog_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    measures = data.get("measures", {}) if isinstance(data, dict) else {}
    if not isinstance(measures, dict):
        return {}
    catalog: Dict[str, Dict[str, str]] = {}
    for key, entry in measures.items():
        if isinstance(entry, dict):
            summary = entry.get("summary") or ""
            retrofit = entry.get("retrofit") or ""
            catalog[str(key)] = {"summary": str(summary), "retrofit": str(retrofit)}
    return catalog


def _split_measure_entry(
    measure: Any, catalog: Dict[str, Dict[str, str]]
) -> Tuple[str, str]:
    if isinstance(measure, dict):
        title = str(measure.get("title") or measure.get("name") or "").strip()
        justification = str(
            measure.get("justification") or measure.get("summary") or measure.get("notes") or ""
        ).strip()
    else:
        title = str(measure).strip()
        justification = ""

    if title in catalog and not justification:
        summary = catalog[title].get("summary", "")
        justification = summary.strip()
        if not justification:
            retrofit = catalog[title].get("retrofit", "")
            justification = extract_first_sentence(retrofit)

    if not justification:
        justification = ensure_sentence(
            uncertainty_sentence("justification was not documented for this measure")
        )

    return title or "Untitled measure", justification
