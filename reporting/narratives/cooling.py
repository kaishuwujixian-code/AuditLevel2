from dataclasses import dataclass
from typing import Any, Dict, List

from reporting.narratives import (
    coerce_bool,
    contains_unknown,
    ensure_sentence,
    first_meaningful_text,
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
from reporting.narratives.checklists import render_block_appendix
from reporting.narratives.library_items import collect_items, render_items

BLOCK_PLACEHOLDERS = ["{Central Cooling Systems block}"]
EXPECTED_INPUTS = {
    "{Central Cooling Systems block}": {
        "section": "cooling",
        "fields": [
            "cooling_block_override",
            "cooling_block",
            "cooling.system_type",
            "cooling_system_type",
            "hvac.system_combos",
            "hvac_system_combos",
            "cooling_central_system_present",
            "cooling_serves",
            "cooling.serves",
            "cooling_distribution",
            "suite_cooling_type",
            "fluid_cooler_present",
            "wshp_install_year",
            "wshp_deficiencies_reported",
            "cooling_issues_reported",
            "site_visit_season",
            "cooling_location",
            "cooling_controls_notes",
            "cooling_notes",
            "cooling_items",
            "chiller_manufacturer",
            "chiller_install_year",
            "cooling_equipment_condition",
            "condenser_pump_has_vfd",
            "cooling_tower_present",
            "cooling_tower_has_vfd",
            "number_of_chillers",
            "chiller_tonnage",
            "number_of_fluid_coolers",
            "number_of_rooftop_units",
        ],
    }
}

COMBO_COOLING_TYPE_MAP = {
    "chiller_cooling_tower": "chiller_cooling_tower",
    "air_cooled_chiller": "chiller_air",
    "wshp_fluid_cooler": "fluid_cooler",
    "wshp_loop": "wshp_cooling",
}


@dataclass(frozen=True)
class CoolingContext:
    audit_level: str
    system_type_raw: Any
    system_type_values: List[str]
    system_combos_raw: Any
    system_combos_values: List[str]
    distribution_raw: Any
    serves_values: List[str]
    location_text: str | None
    controls_notes_text: str | None
    notes_text: str | None
    number_of_chillers: Any
    chiller_tonnage: Any
    number_of_fluid_coolers: Any
    number_of_rooftop_units: Any
    cooling_central_system_present: Any
    cooling_distribution_values: List[str]
    suite_cooling_type_values: List[str]
    chiller_manufacturer: Any
    chiller_install_year: Any
    cooling_equipment_condition_values: List[str]
    condenser_pump_has_vfd: Any
    cooling_tower_present: Any
    cooling_tower_has_vfd: Any

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
        system_combos_raw = get_answer_value(
            project,
            ["hvac.system_combos", "hvac_system_combos", "system_combos"],
        )
        system_combos_values = format_option_values(
            "hvac.system_combos", system_combos_raw, mapping=mapping
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
        cooling_central_system_present = get_answer_value(
            project,
            ["cooling_central_system_present", "central_cooling_present"],
            section="cooling",
        )
        cooling_distribution_value = get_answer_value(
            project,
            ["cooling_distribution", "cooling_distribution_type"],
            section="cooling",
        )
        cooling_distribution_values = format_option_values(
            "cooling.distribution", cooling_distribution_value, mapping=mapping
        )
        suite_cooling_type_value = get_answer_value(
            project,
            ["suite_cooling_type"],
            section="cooling",
        )
        suite_cooling_type_values = format_option_values(
            "suite.cooling_type", suite_cooling_type_value, mapping=mapping
        )
        chiller_manufacturer = get_answer_value(
            project,
            ["chiller_manufacturer"],
            section="cooling",
        )
        chiller_install_year = get_answer_value(
            project,
            ["chiller_install_year"],
            section="cooling",
        )
        cooling_equipment_condition_value = get_answer_value(
            project,
            ["cooling_equipment_condition"],
            section="cooling",
        )
        cooling_equipment_condition_values = format_option_values(
            "cooling.equipment_condition", cooling_equipment_condition_value, mapping=mapping
        )
        condenser_pump_has_vfd = get_answer_value(
            project,
            ["condenser_pump_has_vfd"],
            section="cooling",
        )
        cooling_tower_present = get_answer_value(
            project,
            ["cooling_tower_present"],
            section="cooling",
        )
        cooling_tower_has_vfd = get_answer_value(
            project,
            ["cooling_tower_has_vfd"],
            section="cooling",
        )
        return cls(
            audit_level="L1",
            system_type_raw=system_type_raw,
            system_type_values=system_type_values,
            system_combos_raw=system_combos_raw,
            system_combos_values=system_combos_values,
            distribution_raw=distribution_raw,
            serves_values=serves_values,
            location_text=location_text,
            controls_notes_text=controls_notes_text,
            notes_text=notes_text,
            number_of_chillers=number_of_chillers,
            chiller_tonnage=chiller_tonnage,
            number_of_fluid_coolers=number_of_fluid_coolers,
            number_of_rooftop_units=number_of_rooftop_units,
            cooling_central_system_present=cooling_central_system_present,
            cooling_distribution_values=cooling_distribution_values,
            suite_cooling_type_values=suite_cooling_type_values,
            chiller_manufacturer=chiller_manufacturer,
            chiller_install_year=chiller_install_year,
            cooling_equipment_condition_values=cooling_equipment_condition_values,
            condenser_pump_has_vfd=condenser_pump_has_vfd,
            cooling_tower_present=cooling_tower_present,
            cooling_tower_has_vfd=cooling_tower_has_vfd,
        )

    def system_unknown(self) -> bool:
        if self.system_combos_values:
            return False
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


def _resolve_combo_systems(system_combos_raw: Any) -> List[str]:
    combos = _resolve_system_types(system_combos_raw)
    systems: List[str] = []
    for combo in combos:
        mapped = COMBO_COOLING_TYPE_MAP.get(combo)
        if mapped:
            systems.append(mapped)
        elif combo:
            systems.append(combo)
    return systems


def render(system_type: Any, context: Dict[str, Any], mapping: Dict[str, Any] | None = None) -> str:
    project = context if isinstance(context, dict) and "answers" in context else {"answers": context}
    ctx = CoolingContext.from_project(project, mapping=mapping, system_type_override=system_type)
    system_types = _resolve_system_types(system_type or ctx.system_type_raw)
    combo_types = _resolve_combo_systems(ctx.system_combos_raw)
    system_types = list(dict.fromkeys(system_types + combo_types))
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
    combo_types = _resolve_combo_systems(context.system_combos_raw)
    system_types = list(dict.fromkeys(system_types + combo_types))
    if system_types:
        sentences.extend(
            sentence for sentence in (_render_cooling_system(value, context) for value in system_types) if sentence
        )
    else:
        central_present = coerce_bool(context.cooling_central_system_present)
        if central_present is False:
            sentences.append("No central cooling plant was identified during the walkthrough.")
        else:
            sentences.append(not_confirmed_sentence("The central cooling system type"))

    if context.cooling_distribution_values:
        distribution_text = human_join(context.cooling_distribution_values)
        sentences.append(f"Cooling is distributed through {distribution_text}.")
    elif not context.distribution_unknown():
        serves = human_join(context.serves_values)
        sentences.append(f"Cooling is distributed through {serves}.")
    elif not context.system_unknown():
        sentences.append(further_investigation_sentence("the cooling distribution systems"))

    if context.suite_cooling_type_values:
        suite_cooling = human_join(context.suite_cooling_type_values)
        sentences.append(f"Suite-level cooling is primarily provided by {suite_cooling}.")

    if context.chiller_manufacturer or context.chiller_install_year:
        manufacturer = stringify_value(context.chiller_manufacturer)
        install_year = stringify_value(context.chiller_install_year)
        if manufacturer and install_year:
            sentences.append(f"The chiller plant includes {manufacturer} equipment installed around {install_year}.")
        elif manufacturer:
            sentences.append(f"The chiller plant includes {manufacturer} equipment.")
        elif install_year:
            sentences.append(f"The chiller plant was installed around {install_year}.")

    if context.cooling_equipment_condition_values:
        condition_text = human_join(context.cooling_equipment_condition_values)
        sentences.append(
            f"Central cooling equipment appears to be in {condition_text} condition based on walkthrough observations."
        )

    condenser_vfd = coerce_bool(context.condenser_pump_has_vfd)
    if condenser_vfd is True:
        sentences.append("Condenser water pumps are equipped with variable frequency drives (VFDs).")
    elif condenser_vfd is False:
        sentences.append("Condenser water pumps appear to be constant-speed (no VFDs observed).")

    tower_present = coerce_bool(context.cooling_tower_present)
    tower_vfd = coerce_bool(context.cooling_tower_has_vfd)
    if tower_present is True:
        if tower_vfd is True:
            sentences.append("Cooling tower fans are equipped with variable frequency drives (VFDs).")
        elif tower_vfd is False:
            sentences.append("Cooling tower fans appear to be constant-speed (no VFDs observed).")
    elif tower_present is False:
        sentences.append("No cooling tower was observed during the walkthrough.")

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

    return " ".join(sentence for sentence in sentences[:7] if sentence)


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    override_text = first_meaningful_text(
        [get_answer_value(project, ["cooling_block_override", "cooling_block"])]
    )
    library_items = collect_items(project, "cooling_items")
    if override_text and library_items:
        paragraphs = [render_items(library_items), override_text]
    elif override_text:
        paragraphs = [override_text]
    elif library_items:
        paragraphs = [render_items(library_items)]
    else:
        paragraph = render_paragraph(project, mapping=mapping)
        if not paragraph:
            return not_confirmed_sentence("Central cooling system details")
        paragraphs = [paragraph]
    checklist_text = render_block_appendix(project, target_block="cooling")
    if checklist_text:
        paragraphs.append(checklist_text)
    return "\n\n".join(paragraphs)
