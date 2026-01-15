from dataclasses import dataclass
from typing import Any, Dict, List

from reporting.narratives import (
    contains_unknown,
    ensure_sentence,
    format_distribution_values,
    format_option_values,
    further_investigation_sentence,
    get_answer_value,
    human_join,
    is_unknown_selection,
    not_confirmed_sentence,
    stringify_value,
    uncertainty_sentence,
)


@dataclass(frozen=True)
class CoolingContext:
    audit_level: str
    system_type_raw: Any
    system_type_values: List[str]
    distribution_raw: Any
    serves_values: List[str]
    location_text: str | None
    controls_notes_text: str | None
    notes_text: str | None
    number_of_chillers: Any
    chiller_tonnage: Any
    number_of_fluid_coolers: Any
    number_of_rooftop_units: Any

    @classmethod
    def from_project(
        cls,
        project: Dict[str, Any],
        mapping: Dict[str, Any] | None = None,
        *,
        system_type_override: Any = None,
    ) -> "CoolingContext":
        system_type_raw = system_type_override
        if system_type_raw is None:
            system_type_raw = get_answer_value(
                project,
                ["cooling.system_type", "cooling_system_type", "system_type"],
                section="cooling",
            )
        system_type_values = format_option_values(
            "cooling.system_type", system_type_raw, mapping=mapping
        )
        distribution_raw = get_answer_value(
            project,
            ["cooling_serves", "cooling.serves", "serves"],
            section="cooling",
        )
        serves_values = format_distribution_values(distribution_raw, mapping=mapping)
        location_text = stringify_value(
            get_answer_value(project, ["cooling_location", "location"], section="cooling")
        )
        controls_notes_text = stringify_value(
            get_answer_value(
                project,
                ["cooling_controls_notes", "cooling_notes", "controls_notes"],
                section="cooling",
            )
        )
        notes_text = stringify_value(
            get_answer_value(project, ["cooling_notes", "notes"], section="cooling")
        )
        number_of_chillers = get_answer_value(
            project,
            ["number_of_chillers", "chiller_count"],
            section="cooling",
        )
        chiller_tonnage = get_answer_value(
            project,
            ["chiller_tonnage", "chiller_capacity_tons", "chiller_capacity"],
            section="cooling",
        )
        number_of_fluid_coolers = get_answer_value(
            project,
            ["number_of_fluid_coolers", "fluid_cooler_count"],
            section="cooling",
        )
        number_of_rooftop_units = get_answer_value(
            project,
            ["number_of_rooftop_units", "rtu_count"],
            section="cooling",
        )
        return cls(
            audit_level="L1",
            system_type_raw=system_type_raw,
            system_type_values=system_type_values,
            distribution_raw=distribution_raw,
            serves_values=serves_values,
            location_text=location_text,
            controls_notes_text=controls_notes_text,
            notes_text=notes_text,
            number_of_chillers=number_of_chillers,
            chiller_tonnage=chiller_tonnage,
            number_of_fluid_coolers=number_of_fluid_coolers,
            number_of_rooftop_units=number_of_rooftop_units,
        )

    def system_unknown(self) -> bool:
        return (
            not self.system_type_values
            or contains_unknown(self.system_type_values)
            or is_unknown_selection(self.system_type_raw)
        )

    def distribution_unknown(self) -> bool:
        return (
            not self.serves_values
            or contains_unknown(self.serves_values)
            or is_unknown_selection(self.distribution_raw)
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


def _render_cooling_system(system_type: str, context: CoolingContext) -> str:
    location = (
        f" located in {context.location_text.strip()}"
        if context.location_text and context.location_text.strip()
        else ""
    )
    if system_type in {"chiller_cooling_tower", "chiller_water"}:
        chiller_desc = _format_count_capacity(
            context.number_of_chillers,
            context.chiller_tonnage,
            "tons",
            "water-cooled chiller",
        )
        return f"Cooling is provided by {chiller_desc} with an associated cooling tower{location}."
    if system_type == "chiller_air":
        chiller_desc = _format_count_capacity(
            context.number_of_chillers,
            context.chiller_tonnage,
            "tons",
            "air-cooled chiller",
        )
        return f"Cooling is provided by {chiller_desc}{location}."
    if system_type in {"fluid_cooler", "wshp_cooling"}:
        cooler_desc = _format_count_capacity(
            context.number_of_fluid_coolers,
            None,
            "",
            "fluid cooler",
        )
        return f"Heat rejection for the cooling loop is handled by {cooler_desc}{location}."
    if system_type == "packaged_rooftop_dx":
        rtu_desc = _format_count_capacity(
            context.number_of_rooftop_units,
            None,
            "",
            "packaged rooftop DX unit",
        )
        return f"Cooling is provided by {rtu_desc}{location}."
    if system_type == "split_dx":
        return f"Cooling is provided by split DX equipment{location}."
    if system_type == "ptac":
        return f"Cooling is provided by packaged terminal air-conditioning units{location}."
    if system_type == "none":
        return "No central cooling plant was identified during the walkthrough."
    return ""


def _resolve_system_types(system_type_raw: Any) -> List[str]:
    values = _coerce_list(system_type_raw)
    return [
        value
        for value in values
        if isinstance(value, str) and "unknown" not in value.lower()
    ]


def render(system_type: Any, context: Dict[str, Any], mapping: Dict[str, Any] | None = None) -> str:
    project = context if isinstance(context, dict) and "answers" in context else {"answers": context}
    ctx = CoolingContext.from_project(project, mapping=mapping, system_type_override=system_type)
    system_types = _resolve_system_types(system_type or ctx.system_type_raw)
    if not system_types:
        return not_confirmed_sentence("The central cooling system type")
    sentences = [_render_cooling_system(value, ctx) for value in system_types]
    return " ".join(sentence for sentence in sentences if sentence)


def render_paragraph(
    project: Dict[str, Any], *, mapping: Dict[str, Any] | None = None, system_type_override: Any = None
) -> str:
    context = CoolingContext.from_project(
        project, mapping=mapping, system_type_override=system_type_override
    )
    sentences: list[str] = []
    system_types = _resolve_system_types(context.system_type_raw)
    if system_types:
        sentences.extend(
            sentence for sentence in (_render_cooling_system(value, context) for value in system_types) if sentence
        )
    else:
        sentences.append(not_confirmed_sentence("The central cooling system type"))

    if not context.distribution_unknown():
        serves = human_join(context.serves_values)
        sentences.append(f"Cooling is distributed through {serves}.")
    elif not context.system_unknown():
        sentences.append(further_investigation_sentence("the cooling distribution systems"))

    if context.controls_notes_text and context.controls_notes_text.strip():
        sentences.append(ensure_sentence(context.controls_notes_text))
    elif not context.system_unknown():
        sentences.append(
            uncertainty_sentence(
                f"cooling equipment condition and controls were not fully verified for this {context.audit_level} review"
            )
        )

    if context.notes_text and context.notes_text.strip():
        sentences.append(ensure_sentence(context.notes_text))

    return " ".join(sentence for sentence in sentences[:5] if sentence)
