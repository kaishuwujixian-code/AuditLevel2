from dataclasses import dataclass
from typing import Any, Dict, List

from reporting.narratives import (
    coerce_bool,
    contains_unknown,
    ensure_sentence,
    first_meaningful_text,
    format_option_values,
    format_distribution_values,
    further_investigation_sentence,
    get_answer_value,
    human_join,
    is_unknown_selection,
    not_confirmed_sentence,
    stringify_value,
    uncertainty_sentence,
)
from reporting.narratives.checklists import render_block_appendix
from reporting.rulesets.engine import render_ruleset_block

BLOCK_PLACEHOLDERS = ["{Central Heating Systems block}"]
EXPECTED_INPUTS = {
    "{Central Heating Systems block}": {
        "section": "heating",
        "fields": [
            "heating_block_override",
            "heating_block",
            "hvac.heating_system_type",
            "heating_system_type",
            "hvac.system_combos",
            "hvac_system_combos",
            "boilers",
            "number_of_boilers",
            "boiler_capacity_mbh",
            "bas_integration_level",
            "outdoor_reset_present",
            "boiler_type",
            "boiler_install_year",
            "boiler_condition",
            "boiler_pumps_have_vfd",
            "distribution_pumps_operating_normally",
            "circulation_issues_reported",
            "hvac.heating_serves",
            "heating_serves",
            "heating_distribution",
            "boiler_serves_secondary_dhw",
            "boiler_serves_misc_loops",
            "heating_notes",
        ],
    }
}

COMBO_HEATING_TYPE_MAP = {
    "condensing_boiler_ps": "condensing_boiler",
    "high_temp_heating_loop": "high_temp_heating_loop",
    "wshp_loop": "wshp_central",
    "wshp_fluid_cooler": "wshp_fluid_cooler",
}

HEAT_SOURCE_TYPE_MAP = {
    "central_hydronic_boiler_plant": "central_hydronic_boiler_plant",
    "wshp_loop": "wshp_central",
    "ashp": "ashp",
    "electric_resistance_central": "electric_resistance",
}


@dataclass(frozen=True)
class HeatingContext:
    audit_level: str
    confidence: str
    unknown_policy: str
    override_text: str | None
    system_type_raw: Any
    system_type_values: List[str]
    system_combos_raw: Any
    system_combos_values: List[str]
    cooling_type_raw: Any
    cooling_type_values: List[str]
    distribution_raw: Any
    serves_values: List[str]
    cooling_distribution_raw: Any
    cooling_serves_values: List[str]
    heating_location_text: str | None
    cooling_location_text: str | None
    controls_notes_text: str | None
    cooling_notes_text: str | None
    condition_text: str | None
    notes_text: str | None
    number_of_boilers: Any
    boiler_capacity_mbh: Any
    bas_integration_level: Any
    outdoor_reset_present: Any
    boiler_type_values: List[str]
    boiler_install_year: Any
    boiler_condition_values: List[str]
    boiler_pumps_have_vfd: Any
    boiler_supply_temp_f: Any
    boiler_return_temp_f: Any
    distribution_pumps_operating_normally: Any
    circulation_issues_reported: Any
    heating_distribution_values: List[str]
    boiler_serves_secondary_dhw: Any
    boiler_serves_misc_loops: Any

    @classmethod
    def from_project(
        cls, project: Dict[str, Any], mapping: Dict[str, Any] | None = None
    ) -> "HeatingContext":
        override_text = first_meaningful_text(
            [get_answer_value(project, ["heating_block_override", "heating_block"])]
        )
        system_type_raw = get_answer_value(
            project,
            [
                "hvac.heating_system_type",
                "heating_system_type",
                "system_type",
                "heating_heat_source",
            ],
            section="heating",
        )
        system_type_values = format_option_values(
            "hvac.heating_system_type", system_type_raw, mapping=mapping
        )
        system_combos_raw = get_answer_value(
            project,
            ["hvac.system_combos", "hvac_system_combos", "system_combos"],
        )
        system_combos_values = format_option_values(
            "hvac.system_combos", system_combos_raw, mapping=mapping
        )
        cooling_type_raw = get_answer_value(
            project,
            ["cooling.system_type", "cooling_system_type", "system_type"],
            section="cooling",
        )
        cooling_type_values = format_option_values(
            "cooling.system_type", cooling_type_raw, mapping=mapping
        )
        distribution_raw = get_answer_value(
            project,
            ["hvac.heating_serves", "heating_serves", "serves"],
            section="heating",
        )
        serves_values = format_distribution_values(distribution_raw, mapping=mapping)
        cooling_distribution_raw = get_answer_value(
            project,
            ["cooling_serves", "cooling.serves", "serves"],
            section="cooling",
        )
        cooling_serves_values = format_distribution_values(
            cooling_distribution_raw, mapping=mapping
        )
        heating_location_text = stringify_value(
            get_answer_value(project, ["heating_location", "location"], section="heating")
        )
        cooling_location_text = stringify_value(
            get_answer_value(project, ["cooling_location", "location"], section="cooling")
        )
        controls_notes_text = stringify_value(
            get_answer_value(
                project,
                ["heating_controls_notes", "heating_controls", "controls_notes"],
                section="heating",
            )
        )
        cooling_notes_text = stringify_value(
            get_answer_value(
                project,
                ["cooling_controls_notes", "cooling_notes", "controls_notes"],
                section="cooling",
            )
        )
        condition_value = get_answer_value(project, ["architectural_condition", "condition"])
        condition_text = None
        condition_values = format_option_values(
            "building.arch_condition", condition_value, mapping=mapping
        )
        if condition_values and not contains_unknown(condition_values):
            condition_text = human_join(condition_values)
        notes_value = get_answer_value(
            project,
            ["heating_notes", "heating_block", "notes"],
            section="heating",
        )
        notes_text = stringify_value(notes_value)
        number_of_boilers = get_answer_value(
            project,
            ["number_of_boilers", "heating_boiler_count", "boiler_count"],
            section="heating",
        )
        boiler_capacity_mbh = get_answer_value(
            project,
            ["boiler_capacity_mbh", "boiler_capacity", "boiler_capacity_mbh_each"],
            section="heating",
        )
        bas_integration_level = get_answer_value(
            project,
            ["bas_integration_level", "bas_integration", "bas_level"],
            section="heating",
        )
        outdoor_reset_present = get_answer_value(
            project,
            ["outdoor_reset_present", "outdoor_air_reset"],
            section="heating",
        )
        boiler_type_value = get_answer_value(
            project,
            ["boiler_type", "heating_boiler_type"],
            section="heating",
        )
        boiler_type_values = format_option_values(
            "heating.boiler_type", boiler_type_value, mapping=mapping
        )
        boiler_install_year = get_answer_value(
            project,
            ["boiler_install_year", "boiler_year_installed"],
            section="heating",
        )
        boiler_condition_value = get_answer_value(
            project,
            ["boiler_condition", "heating_boiler_condition"],
            section="heating",
        )
        boiler_condition_values = format_option_values(
            "boiler.condition", boiler_condition_value, mapping=mapping
        )
        boiler_pumps_have_vfd = get_answer_value(
            project,
            ["boiler_pumps_have_vfd", "boiler_pumps_vfd"],
            section="heating",
        )
        boiler_supply_temp_f = get_answer_value(
            project,
            ["boiler_supply_temp_f", "boiler_supply_temp"],
            section="heating",
        )
        boiler_return_temp_f = get_answer_value(
            project,
            ["boiler_return_temp_f", "boiler_return_temp"],
            section="heating",
        )
        distribution_pumps_operating_normally = get_answer_value(
            project,
            ["distribution_pumps_operating_normally", "distribution_pumps_ok"],
            section="heating",
        )
        circulation_issues_reported = get_answer_value(
            project,
            ["circulation_issues_reported", "circulation_issues"],
            section="heating",
        )
        heating_distribution_value = get_answer_value(
            project,
            ["heating_distribution", "heating_distribution_type"],
            section="heating",
        )
        heating_distribution_values = format_option_values(
            "heating.distribution", heating_distribution_value, mapping=mapping
        )
        boiler_serves_secondary_dhw = get_answer_value(
            project,
            ["boiler_serves_secondary_dhw", "boiler_serves_dhw"],
            section="heating",
        )
        boiler_serves_misc_loops = get_answer_value(
            project,
            ["boiler_serves_misc_loops", "boiler_serves_misc"],
            section="heating",
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
            cooling_type_raw=cooling_type_raw,
            cooling_type_values=cooling_type_values,
            distribution_raw=distribution_raw,
            serves_values=serves_values,
            cooling_distribution_raw=cooling_distribution_raw,
            cooling_serves_values=cooling_serves_values,
            heating_location_text=heating_location_text,
            cooling_location_text=cooling_location_text,
            controls_notes_text=controls_notes_text,
            cooling_notes_text=cooling_notes_text,
            condition_text=condition_text,
            notes_text=notes_text,
            number_of_boilers=number_of_boilers,
            boiler_capacity_mbh=boiler_capacity_mbh,
            bas_integration_level=bas_integration_level,
            outdoor_reset_present=outdoor_reset_present,
            boiler_type_values=boiler_type_values,
            boiler_install_year=boiler_install_year,
            boiler_condition_values=boiler_condition_values,
            boiler_pumps_have_vfd=boiler_pumps_have_vfd,
            boiler_supply_temp_f=boiler_supply_temp_f,
            boiler_return_temp_f=boiler_return_temp_f,
            distribution_pumps_operating_normally=distribution_pumps_operating_normally,
            circulation_issues_reported=circulation_issues_reported,
            heating_distribution_values=heating_distribution_values,
            boiler_serves_secondary_dhw=boiler_serves_secondary_dhw,
            boiler_serves_misc_loops=boiler_serves_misc_loops,
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

    def cooling_unknown(self) -> bool:
        return (
            not self.cooling_type_values
            or contains_unknown(self.cooling_type_values)
            or is_unknown_selection(self.cooling_type_raw)
        )

    def cooling_distribution_unknown(self) -> bool:
        return (
            not self.cooling_serves_values
            or contains_unknown(self.cooling_serves_values)
            or is_unknown_selection(self.cooling_distribution_raw)
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


def _render_heating_system(system_type: str, context: HeatingContext) -> str:
    location = (
        f" located in {context.heating_location_text.strip()}"
        if context.heating_location_text and context.heating_location_text.strip()
        else ""
    )
    if system_type in {"condensing_boiler", "condensing_boiler_ps"}:
        boiler_desc = _format_count_capacity(
            context.number_of_boilers,
            context.boiler_capacity_mbh,
            "MBH",
            "condensing boiler",
        )
        return f"The building is heated by {boiler_desc}{location}."
    if system_type == "atmospheric_boiler":
        boiler_desc = _format_count_capacity(
            context.number_of_boilers,
            context.boiler_capacity_mbh,
            "MBH",
            "atmospheric boiler",
        )
        return f"The building is heated by {boiler_desc}{location}."
    if system_type == "high_temp_heating_loop":
        boiler_desc = _format_count_capacity(
            context.number_of_boilers,
            context.boiler_capacity_mbh,
            "MBH",
            "boiler",
        )
        if boiler_desc:
            return f"The building is served by a high-temperature heating loop supported by {boiler_desc}{location}."
        return f"The building is served by a high-temperature heating loop{location}."
    if system_type == "central_hydronic_boiler_plant":
        boiler_desc = _format_count_capacity(
            context.number_of_boilers,
            context.boiler_capacity_mbh,
            "MBH",
            "boiler",
        )
        if boiler_desc:
            return f"Heating is provided by a central hydronic boiler plant with {boiler_desc}{location}."
        return f"Heating is provided by a central hydronic boiler plant{location}."
    if system_type == "electric_resistance":
        return f"Heating is provided by electric resistance equipment{location}."
    if system_type in {"wshp_central", "wshp_fluid_cooler"}:
        boiler_desc = _format_count_capacity(
            context.number_of_boilers,
            context.boiler_capacity_mbh,
            "MBH",
            "boiler",
        )
        return (
            "Heating is provided by a water-source heat pump loop." + (
                f" The loop temperature is maintained by {boiler_desc}{location}."
                if boiler_desc
                else f" Central plant equipment maintains loop temperature{location}."
            )
        )
    if system_type == "ashp":
        return f"Heating is provided by air-source heat pump equipment{location}."
    return ""


def _resolve_system_types(system_type_raw: Any) -> List[str]:
    values = _coerce_list(system_type_raw)
    resolved: List[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        if "unknown" in value.lower():
            continue
        resolved.append(HEAT_SOURCE_TYPE_MAP.get(value, value))
    return resolved


def _resolve_combo_systems(system_combos_raw: Any) -> List[str]:
    combos = _resolve_system_types(system_combos_raw)
    systems: List[str] = []
    for combo in combos:
        mapped = COMBO_HEATING_TYPE_MAP.get(combo)
        if mapped:
            systems.append(mapped)
        elif combo:
            systems.append(combo)
    return systems


def render(system_type: Any, context: Dict[str, Any], mapping: Dict[str, Any] | None = None) -> str:
    project = context if isinstance(context, dict) and "answers" in context else {"answers": context}
    ctx = HeatingContext.from_project(project, mapping=mapping)
    system_types = _resolve_system_types(system_type or ctx.system_type_raw)
    combo_types = _resolve_combo_systems(ctx.system_combos_raw)
    system_types = list(dict.fromkeys(system_types + combo_types))
    if not system_types:
        return not_confirmed_sentence("The heating plant type")
    sentences = [_render_heating_system(system_type, ctx) for system_type in system_types]
    return " ".join(sentence for sentence in sentences if sentence)


def _render_heating_paragraph(context: HeatingContext) -> str:
    system_types = _resolve_system_types(context.system_type_raw)
    combo_types = _resolve_combo_systems(context.system_combos_raw)
    system_types = list(dict.fromkeys(system_types + combo_types))
    sentences: list[str] = []
    if system_types:
        sentences.extend(
            sentence for sentence in (_render_heating_system(value, context) for value in system_types) if sentence
        )
    else:
        sentences.append(not_confirmed_sentence("The heating plant type"))

    if context.boiler_type_values:
        boiler_type_text = human_join(context.boiler_type_values)
        sentences.append(f"The boiler plant is composed of {boiler_type_text} boilers.")

    if not any(
        system_type
        in {
            "condensing_boiler",
            "condensing_boiler_ps",
            "atmospheric_boiler",
            "high_temp_heating_loop",
            "central_hydronic_boiler_plant",
        }
        for system_type in system_types
    ):
        boiler_desc = _format_count_capacity(
            context.number_of_boilers,
            context.boiler_capacity_mbh,
            "MBH",
            "boiler",
        )
        if boiler_desc:
            sentences.append(f"The boiler plant includes {boiler_desc}.")

    if context.boiler_install_year:
        sentences.append(
            f"Boilers were installed around {stringify_value(context.boiler_install_year)}."
        )

    distribution_unknown = context.distribution_unknown()
    if context.heating_distribution_values:
        distribution_text = human_join(context.heating_distribution_values)
        sentences.append(f"Space heating is delivered via {distribution_text}.")
    elif not distribution_unknown:
        serves = human_join(context.serves_values)
        sentences.append(f"Heating is distributed through {serves}.")
    else:
        sentences.append(further_investigation_sentence("the heating distribution systems"))

    boiler_condition_text = (
        human_join(context.boiler_condition_values) if context.boiler_condition_values else None
    )
    if boiler_condition_text:
        sentences.append(
            f"The boilers were observed to be in {boiler_condition_text} condition at the time of the site visit."
        )
    elif context.condition_text:
        sentences.append(
            f"The heating equipment appears to be in {context.condition_text} condition based on walkthrough observations."
        )
    else:
        sentences.append(
            uncertainty_sentence(
                f"equipment condition and sequence of operations were not fully verified for this {context.audit_level} review"
            )
        )

    bas_level = first_meaningful_text([context.bas_integration_level])
    if bas_level:
        bas_level_text = human_join(format_option_values("bas.integration_level", bas_level))
        sentences.append(f"BAS integration for the heating plant is {bas_level_text}.")

    outdoor_reset = coerce_bool(context.outdoor_reset_present)
    if outdoor_reset is True:
        sentences.append("Outdoor-air reset controls are provided for the heating plant.")
    elif outdoor_reset is False:
        sentences.append("Outdoor-air reset controls were not observed for the heating plant.")

    boiler_pump_vfd = coerce_bool(context.boiler_pumps_have_vfd)
    if boiler_pump_vfd is True:
        sentences.append("Boiler pumps are equipped with variable frequency drives (VFDs).")
    elif boiler_pump_vfd is False:
        sentences.append("Boiler pumps appear to be constant-speed (no VFDs observed).")

    pumps_ok = coerce_bool(context.distribution_pumps_operating_normally)
    circulation_issues = coerce_bool(context.circulation_issues_reported)
    if pumps_ok is True and circulation_issues is False:
        sentences.append(
            "Distribution pumps and associated hydronic piping appear to be operating normally, and no circulation issues were reported."
        )
    elif circulation_issues is True:
        sentences.append("Circulation issues were reported during the walkthrough.")

    serves_dhw = coerce_bool(context.boiler_serves_secondary_dhw)
    if serves_dhw is True:
        sentences.append("The boiler plant also serves secondary DHW loads.")

    serves_misc = coerce_bool(context.boiler_serves_misc_loops)
    if serves_misc is True:
        sentences.append("The boiler plant also serves miscellaneous or secondary hydronic loops.")

    if context.boiler_supply_temp_f and context.boiler_return_temp_f:
        sentences.append(
            "During the site visit, boiler supply and return temperatures were observed to be "
            f"approximately {stringify_value(context.boiler_supply_temp_f)}°F and "
            f"{stringify_value(context.boiler_return_temp_f)}°F, respectively."
        )

    if context.controls_notes_text and context.controls_notes_text.strip():
        sentences.append(ensure_sentence(context.controls_notes_text))
    elif system_types or not distribution_unknown:
        sentences.append(not_confirmed_sentence("Control sequences for the heating systems"))

    if context.notes_text and context.notes_text.strip():
        sentences.append(ensure_sentence(context.notes_text))

    return " ".join(sentences[:8])


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = HeatingContext.from_project(project, mapping=mapping)
    if context.override_text:
        return context.override_text

    ruleset_text = render_ruleset_block(
        project,
        ruleset_filename="heating.rules.json",
        target_block="heating",
        block_ref="{Central Heating Systems block}",
    )
    if ruleset_text:
        paragraphs: list[str] = [ruleset_text]
    else:
        paragraphs = [_render_heating_paragraph(context)]
        if not paragraphs or not paragraphs[0]:
            return not_confirmed_sentence("Heating system details")

    checklist_text = render_block_appendix(project, target_block="heating")
    if checklist_text:
        paragraphs.append(checklist_text)
    return "\n\n".join(paragraphs)
