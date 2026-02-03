from dataclasses import dataclass
from typing import Any, Dict, List

from reporting.narratives import (
    contains_unknown,
    ensure_sentence,
    first_meaningful_text,
    format_option_values,
    further_investigation_sentence,
    get_answer_value,
    has_meaningful_value,
    human_join,
    is_unknown_selection,
    not_confirmed_sentence,
    stringify_value,
    uncertainty_sentence,
)
from reporting.narratives.checklists import render_block_appendix

BLOCK_PLACEHOLDERS = ["{DHW System Block}"]
EXPECTED_INPUTS = {
    "{DHW System Block}": {
        "section": "dhw",
        "fields": [
            "dhw_block_override",
            "dhw_block",
            "dhw.system_type",
            "dhw_system_type",
            "hvac.system_combos",
            "hvac_system_combos",
            "number_of_dhw_boilers",
            "dhw_boiler_capacity_mbh",
            "number_of_dhw_tanks",
            "dhw_tank_capacity_gal",
            "dhw_heat_source",
            "dhw_recirc",
            "dhw_recirc_pumps",
            "dhw_storage_notes",
            "dhw_distribution_notes",
        ],
    }
}

COMBO_DHW_TYPE_MAP = {
    "separate_dhw_boilers": "dhw_boilers",
    "dhw_from_heating_hx": "hx_from_heating_ps",
}


@dataclass(frozen=True)
class DHWContext:
    audit_level: str
    confidence: str
    unknown_policy: str
    override_text: str | None
    system_type_raw: Any
    system_type_values: List[str]
    system_combos_raw: Any
    system_combos_values: List[str]
    heat_source_text: str | None
    storage_notes_text: str | None
    location_text: str | None
    condition_text: str | None
    recirc_value: Any
    number_of_dhw_boilers: Any
    dhw_boiler_capacity_mbh: Any
    number_of_dhw_tanks: Any
    dhw_tank_capacity_gal: Any

    @classmethod
    def from_project(
        cls, project: Dict[str, Any], mapping: Dict[str, Any] | None = None
    ) -> "DHWContext":
        override_text = first_meaningful_text(
            [get_answer_value(project, ["dhw_block_override", "dhw_block"])]
        )
        system_type_raw = get_answer_value(
            project,
            ["dhw.system_type", "dhw_system_type", "system_type"],
            section="dhw",
        )
        system_type_values = format_option_values(
            "dhw.system_type", system_type_raw, mapping=mapping
        )
        system_combos_raw = get_answer_value(
            project,
            ["hvac.system_combos", "hvac_system_combos", "system_combos"],
        )
        system_combos_values = format_option_values(
            "hvac.system_combos", system_combos_raw, mapping=mapping
        )
        heat_source_value = get_answer_value(
            project,
            ["dhw_heat_source", "heat_source", "dhw_source"],
            section="dhw",
        )
        storage_notes_value = get_answer_value(
            project,
            ["dhw_storage_notes", "dhw_distribution_notes", "dhw_notes", "notes", "dhw_block"],
            section="dhw",
        )
        location_text = stringify_value(
            get_answer_value(project, ["dhw_location", "location"], section="dhw")
        )
        condition_value = get_answer_value(project, ["architectural_condition", "condition"])
        condition_text = None
        condition_values = format_option_values(
            "building.arch_condition", condition_value, mapping=mapping
        )
        if condition_values and not contains_unknown(condition_values):
            condition_text = human_join(condition_values)
        recirc_value = get_answer_value(
            project,
            [
                "dhw_recirc",
                "dhw_recirculation",
                "dhw_circulation",
                "dhw_recirc_pumps",
                "dhw_circulation_pumps",
                "dhw_pumps",
            ],
            section="dhw",
        )
        number_of_dhw_boilers = get_answer_value(
            project,
            ["number_of_dhw_boilers", "dhw_boiler_count"],
            section="dhw",
        )
        dhw_boiler_capacity_mbh = get_answer_value(
            project,
            ["dhw_boiler_capacity_mbh", "dhw_boiler_capacity"],
            section="dhw",
        )
        number_of_dhw_tanks = get_answer_value(
            project,
            ["number_of_dhw_tanks", "dhw_tank_count"],
            section="dhw",
        )
        dhw_tank_capacity_gal = get_answer_value(
            project,
            ["dhw_tank_capacity_gal", "dhw_storage_capacity_gal"],
            section="dhw",
        )
        return cls(
            audit_level="L1",
            confidence="moderate",
            unknown_policy="soft",
            override_text=override_text,
            system_type_raw=system_type_raw,
            system_type_values=system_type_values,
            system_combos_raw=system_combos_raw,
            system_combos_values=system_combos_values,
            heat_source_text=stringify_value(heat_source_value),
            storage_notes_text=stringify_value(storage_notes_value),
            location_text=location_text,
            condition_text=condition_text,
            recirc_value=recirc_value,
            number_of_dhw_boilers=number_of_dhw_boilers,
            dhw_boiler_capacity_mbh=dhw_boiler_capacity_mbh,
            number_of_dhw_tanks=number_of_dhw_tanks,
            dhw_tank_capacity_gal=dhw_tank_capacity_gal,
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


def _format_count_capacity(
    count: Any, capacity: Any, unit: str, singular: str, plural: str | None = None
) -> str:
    count_text = stringify_value(count)
    capacity_text = stringify_value(capacity)
    is_single = False
    if isinstance(count, (int, float)):
        is_single = count == 1
    item_label = singular if is_single else (plural or f"{singular}s")
    if count_text and capacity_text:
        return f"{count_text} {item_label} rated at {capacity_text} {unit} each"
    if count_text:
        return f"{count_text} {item_label}"
    if capacity_text:
        return f"{item_label} rated at {capacity_text} {unit} each"
    return item_label


def _render_dhw_system(system_type: str, context: DHWContext) -> str:
    location = (
        f" located in {context.location_text.strip()}"
        if context.location_text and context.location_text.strip()
        else ""
    )
    if system_type in {"dhw_boiler_condensing", "dhw_boiler_atmospheric", "dhw_boilers"}:
        boiler_desc = _format_count_capacity(
            context.number_of_dhw_boilers,
            context.dhw_boiler_capacity_mbh,
            "MBH",
            "central DHW boiler",
        )
        return f"Domestic hot water is generated by {boiler_desc}{location}."
    if system_type == "hx_from_heating_ps":
        return f"Domestic hot water is produced via a heat exchanger tied to the heating plant{location}."
    if system_type == "dhw_electric":
        return f"Domestic hot water is provided by electric water heating equipment{location}."
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
        mapped = COMBO_DHW_TYPE_MAP.get(combo)
        if mapped:
            systems.append(mapped)
        elif combo:
            systems.append(combo)
    return systems


def render(system_type: Any, context: Dict[str, Any], mapping: Dict[str, Any] | None = None) -> str:
    project = context if isinstance(context, dict) and "answers" in context else {"answers": context}
    ctx = DHWContext.from_project(project, mapping=mapping)
    system_types = _resolve_system_types(system_type or ctx.system_type_raw)
    combo_types = _resolve_combo_systems(ctx.system_combos_raw)
    system_types = list(dict.fromkeys(system_types + combo_types))
    if not system_types:
        return not_confirmed_sentence("The domestic hot water plant type")
    sentences = [_render_dhw_system(value, ctx) for value in system_types]
    return " ".join(sentence for sentence in sentences if sentence)


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = DHWContext.from_project(project, mapping=mapping)
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
            sentence for sentence in (_render_dhw_system(value, context) for value in system_types) if sentence
        )
    else:
        sentences.append(not_confirmed_sentence("The domestic hot water plant type"))
        sentences.append(further_investigation_sentence("the domestic hot water plant configuration"))

    if context.heat_source_text and context.heat_source_text.strip():
        sentences.append(f"The heat source is {context.heat_source_text}.")
    if isinstance(context.recirc_value, bool):
        if context.recirc_value:
            sentences.append("A recirculation loop with circulation pumps was observed.")
        else:
            sentences.append("No domestic hot water recirculation loop was observed.")
    elif has_meaningful_value(context.recirc_value):
        sentences.append(ensure_sentence(str(context.recirc_value)))
    if context.number_of_dhw_tanks or context.dhw_tank_capacity_gal:
        tank_desc = _format_count_capacity(
            context.number_of_dhw_tanks,
            context.dhw_tank_capacity_gal,
            "gallons",
            "storage tank",
        )
        sentences.append(f"Storage is provided by {tank_desc}.")
    if context.storage_notes_text and context.storage_notes_text.strip():
        sentences.append(ensure_sentence(context.storage_notes_text))

    if context.condition_text:
        sentences.append(
            f"The DHW equipment appears to be in {context.condition_text} condition based on walkthrough observations."
        )
    else:
        sentences.append(
            uncertainty_sentence(
                f"additional domestic hot water distribution details were not confirmed for this {context.audit_level} review"
            )
        )

    paragraphs.append(" ".join(sentences[:5]))

    recommendations: list[str] = []
    if not system_unknown:
        recommendations.append(
            ensure_sentence(
                "Further review of temperature controls, recirculation schedules, and storage sizing could be considered as part of a detailed audit"
            )
        )
    if recommendations:
        paragraphs.append(" ".join(recommendations))

    checklist_text = render_block_appendix(project, target_block="dhw")
    if checklist_text:
        paragraphs.append(checklist_text)
    return "\n\n".join(paragraphs)
