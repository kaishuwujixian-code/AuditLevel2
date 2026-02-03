from dataclasses import dataclass
from typing import Any, Dict, List

from reporting.narratives import (
    contains_unknown,
    ensure_sentence,
    first_meaningful_text,
    format_option_values,
    further_investigation_sentence,
    get_answer_value,
    human_join,
    is_unknown_selection,
    not_confirmed_sentence,
    stringify_value,
    uncertainty_sentence,
)
from reporting.narratives.checklists import render_block_appendix

BLOCK_PLACEHOLDERS = ["{Central Ventilation System Block}"]
EXPECTED_INPUTS = {
    "{Central Ventilation System Block}": {
        "section": "ventilation",
        "fields": [
            "ventilation_block_override",
            "ventilation_block",
            "ventilation.system_type",
            "ventilation_system_type",
            "hvac.system_combos",
            "hvac_system_combos",
            "number_of_mua_units",
            "ventilation_airflow_cfm",
            "ventilation_notes",
        ],
    }
}

COMBO_VENTILATION_TYPE_MAP = {
    "central_ventilation_mua_doas": "central_ventilation_mua_doas",
    "suite_erv_hrv": "suite_erv_hrv",
    "exhaust_only": "exhaust_only",
}


@dataclass(frozen=True)
class VentilationContext:
    audit_level: str
    confidence: str
    unknown_policy: str
    override_text: str | None
    system_type_raw: Any
    system_type_values: List[str]
    system_combos_raw: Any
    system_combos_values: List[str]
    location_text: str | None
    condition_text: str | None
    bas_present: Any
    notes_text: str | None
    number_of_mua_units: Any
    ventilation_airflow_cfm: Any

    @classmethod
    def from_project(
        cls, project: Dict[str, Any], mapping: Dict[str, Any] | None = None
    ) -> "VentilationContext":
        override_text = first_meaningful_text(
            [get_answer_value(project, ["ventilation_block_override", "ventilation_block"])]
        )
        system_type_raw = get_answer_value(
            project,
            ["ventilation.system_type", "ventilation_system_type", "system_type"],
            section="ventilation",
        )
        system_type_values = format_option_values(
            "ventilation.system_type", system_type_raw, mapping=mapping
        )
        system_combos_raw = get_answer_value(
            project,
            ["hvac.system_combos", "hvac_system_combos", "system_combos"],
        )
        system_combos_values = format_option_values(
            "hvac.system_combos", system_combos_raw, mapping=mapping
        )
        location_text = stringify_value(
            get_answer_value(project, ["ventilation_location", "location"], section="ventilation")
        )
        condition_value = get_answer_value(project, ["architectural_condition", "condition"])
        condition_text = None
        condition_values = format_option_values(
            "building.arch_condition", condition_value, mapping=mapping
        )
        if condition_values and not contains_unknown(condition_values):
            condition_text = human_join(condition_values)
        bas_present = get_answer_value(project, ["bas_present", "building_automation_system"])
        notes_value = get_answer_value(
            project,
            ["ventilation_notes", "ventilation_block", "notes"],
            section="ventilation",
        )
        number_of_mua_units = get_answer_value(
            project,
            ["number_of_mua_units", "mua_count"],
            section="ventilation",
        )
        ventilation_airflow_cfm = get_answer_value(
            project,
            ["ventilation_airflow_cfm", "ventilation_cfm"],
            section="ventilation",
        )
        return cls(
            audit_level="L1",
            confidence="low",
            unknown_policy="soft",
            override_text=override_text,
            system_type_raw=system_type_raw,
            system_type_values=system_type_values,
            system_combos_raw=system_combos_raw,
            system_combos_values=system_combos_values,
            location_text=location_text,
            condition_text=condition_text,
            bas_present=bas_present,
            notes_text=stringify_value(notes_value),
            number_of_mua_units=number_of_mua_units,
            ventilation_airflow_cfm=ventilation_airflow_cfm,
        )

    def system_unknown(self) -> bool:
        if self.system_combos_values:
            return False
        return (
            not self.system_type_values
            or contains_unknown(self.system_type_values)
            or is_unknown_selection(self.system_type_raw)
        )


def _coerce_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _render_ventilation_system(system_type: str, context: VentilationContext) -> str:
    location = (
        f" located in {context.location_text.strip()}"
        if context.location_text and context.location_text.strip()
        else ""
    )
    if system_type in {"mua_gas_rooftop", "mua_hydronic_coil", "mua_corridor"}:
        system_label = {
            "mua_gas_rooftop": "gas-fired rooftop make-up air units",
            "mua_hydronic_coil": "hydronic-coil make-up air units",
            "mua_corridor": "corridor make-up air units",
        }.get(system_type, "make-up air units")
        count_text = stringify_value(context.number_of_mua_units)
        if count_text:
            return (
                f"Ventilation is primarily provided by {count_text} units of {system_label}{location}."
            )
        return f"Ventilation is primarily provided by {system_label}{location}."
    if system_type == "central_ventilation_mua_doas":
        count_text = stringify_value(context.number_of_mua_units)
        if count_text:
            return (
                f"Central ventilation is provided by approximately {count_text} make-up air units or DOAS equipment{location}."
            )
        return f"Central ventilation is provided by make-up air units or DOAS equipment{location}."
    if system_type == "heat_recovery_ventilator":
        return f"Ventilation is provided by a heat recovery ventilator system{location}."
    if system_type == "doas":
        return f"Ventilation is provided by a dedicated outdoor air system{location}."
    if system_type == "suite_erv_hrv":
        return f"Ventilation is delivered via suite-level ERV/HRV units{location}."
    if system_type == "exhaust_only":
        return f"Ventilation is provided by exhaust-only systems{location}."
    return ""


def _resolve_system_types(system_type_raw: Any) -> List[str]:
    values = _coerce_list(system_type_raw)
    return [
        value
        for value in values
        if isinstance(value, str) and "unknown" not in value.lower()
    ]


def _resolve_combo_systems(system_combos_raw: Any) -> List[str]:
    combos = _resolve_system_types(system_combos_raw)
    systems: List[str] = []
    for combo in combos:
        mapped = COMBO_VENTILATION_TYPE_MAP.get(combo)
        if mapped:
            systems.append(mapped)
        elif combo:
            systems.append(combo)
    return systems


def render(system_type: Any, context: Dict[str, Any], mapping: Dict[str, Any] | None = None) -> str:
    project = context if isinstance(context, dict) and "answers" in context else {"answers": context}
    ctx = VentilationContext.from_project(project, mapping=mapping)
    system_types = _resolve_system_types(system_type or ctx.system_type_raw)
    combo_types = _resolve_combo_systems(ctx.system_combos_raw)
    system_types = list(dict.fromkeys(system_types + combo_types))
    if not system_types:
        return not_confirmed_sentence("The central ventilation system type")
    sentences = [_render_ventilation_system(value, ctx) for value in system_types]
    return " ".join(sentence for sentence in sentences if sentence)


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = VentilationContext.from_project(project, mapping=mapping)
    if context.override_text:
        return context.override_text

    paragraphs: list[str] = []
    sentences: list[str] = []
    system_unknown = context.system_unknown()
    system_types = _resolve_system_types(context.system_type_raw)
    combo_types = _resolve_combo_systems(context.system_combos_raw)
    system_types = list(dict.fromkeys(system_types + combo_types))

    if system_types:
        sentences.extend(
            sentence for sentence in (_render_ventilation_system(value, context) for value in system_types) if sentence
        )
    else:
        sentences.append(not_confirmed_sentence("The central ventilation system type"))
        sentences.append(further_investigation_sentence("the primary ventilation strategy"))

    if context.ventilation_airflow_cfm:
        sentences.append(
            f"Reported ventilation airflow is approximately {stringify_value(context.ventilation_airflow_cfm)} CFM."
        )

    if context.condition_text:
        sentences.append(
            f"The ventilation equipment appears to be in {context.condition_text} condition based on walkthrough observations."
        )
    else:
        sentences.append(
            uncertainty_sentence(
                f"operating schedules, air-change rates, and control sequences were not verified for this {context.audit_level} review"
            )
        )

    if context.notes_text and context.notes_text.strip():
        sentences.append(ensure_sentence(context.notes_text))

    paragraphs.append(" ".join(sentences[:5]))

    bas_sentences: list[str] = []
    if isinstance(context.bas_present, bool):
        if context.bas_present:
            bas_sentences.append(
                "The ventilation systems appear to have some level of building automation system oversight."
            )
        else:
            bas_sentences.append(
                "The ventilation systems appear to be locally controlled without a centralized building automation system."
            )
    if bas_sentences:
        bas_sentences.append(
            ensure_sentence(
                "Additional review of scheduling, demand control, and setback strategies could be considered as part of a future detailed assessment"
            )
        )
        paragraphs.append(" ".join(bas_sentences))

    checklist_text = render_block_appendix(project, target_block="ventilation")
    if checklist_text:
        paragraphs.append(checklist_text)
    return "\n\n".join(paragraphs)
