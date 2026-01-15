from dataclasses import dataclass
from typing import Any, Dict, List

from reporting.narratives import (
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

BLOCK_PLACEHOLDERS = ["{Central Heating/Cooling Systems block}"]
EXPECTED_INPUTS = {
    "{Central Heating/Cooling Systems block}": {
        "section": "heating",
        "fields": [
            "heating_block_override",
            "heating_block",
            "hvac.heating_system_type",
            "heating_system_type",
            "hvac.heating_serves",
            "heating_serves",
            "heating_notes",
        ],
    }
}


@dataclass(frozen=True)
class HeatingContext:
    audit_level: str
    confidence: str
    unknown_policy: str
    override_text: str | None
    system_type_raw: Any
    system_type_values: List[str]
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

    @classmethod
    def from_project(
        cls, project: Dict[str, Any], mapping: Dict[str, Any] | None = None
    ) -> "HeatingContext":
        override_text = first_meaningful_text(
            [get_answer_value(project, ["heating_block_override", "heating_block"])]
        )
        system_type_raw = get_answer_value(
            project,
            ["hvac.heating_system_type", "heating_system_type", "system_type"],
            section="heating",
        )
        system_type_values = format_option_values(
            "hvac.heating_system_type", system_type_raw, mapping=mapping
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
        return cls(
            audit_level="L1",
            confidence="moderate",
            unknown_policy="soft",
            override_text=override_text,
            system_type_raw=system_type_raw,
            system_type_values=system_type_values,
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


def _article_for(text: str) -> str:
    if not text:
        return "a"
    return "an" if text[0].lower() in {"a", "e", "i", "o", "u"} else "a"


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = HeatingContext.from_project(project, mapping=mapping)
    if context.override_text:
        return context.override_text

    paragraphs: list[str] = []
    heating_sentences: list[str] = []
    system_unknown = context.system_unknown()
    distribution_unknown = context.distribution_unknown()

    if not system_unknown:
        system_type = human_join(context.system_type_values)
        location = ""
        if context.heating_location_text and context.heating_location_text.strip():
            location = f" located in {context.heating_location_text.strip()}"
        if len(context.system_type_values) > 1:
            heating_sentences.append(f"Heating is provided by {system_type} systems{location}.")
        else:
            article = _article_for(system_type)
            heating_sentences.append(
                f"The primary heating source for the building is {article} {system_type} system{location}."
            )
    else:
        heating_sentences.append(not_confirmed_sentence("The heating plant type"))

    if not distribution_unknown:
        serves = human_join(context.serves_values)
        heating_sentences.append(f"Heating is distributed through {serves}.")
    else:
        heating_sentences.append(further_investigation_sentence("the heating distribution systems"))

    if context.condition_text:
        heating_sentences.append(
            f"The heating equipment appears to be in {context.condition_text} condition based on walkthrough observations."
        )
    else:
        heating_sentences.append(
            uncertainty_sentence(
                f"equipment condition and sequence of operations were not fully verified for this {context.audit_level} review"
            )
        )

    if context.controls_notes_text and context.controls_notes_text.strip():
        heating_sentences.append(ensure_sentence(context.controls_notes_text))
    elif not system_unknown or not distribution_unknown:
        heating_sentences.append(
            not_confirmed_sentence("Control sequences for the heating systems")
        )

    if context.notes_text and context.notes_text.strip():
        heating_sentences.append(ensure_sentence(context.notes_text))

    paragraphs.append(" ".join(heating_sentences[:5]))

    cooling_sentences: list[str] = []
    cooling_unknown = context.cooling_unknown()
    cooling_distribution_unknown = context.cooling_distribution_unknown()

    if not cooling_unknown:
        cooling_type = human_join(context.cooling_type_values)
        if "none" in cooling_type.lower():
            cooling_sentences.append(
                "No central cooling plant was identified during the walkthrough."
            )
        else:
            location = ""
            if context.cooling_location_text and context.cooling_location_text.strip():
                location = f" located in {context.cooling_location_text.strip()}"
            if len(context.cooling_type_values) > 1:
                cooling_sentences.append(f"Cooling is provided by {cooling_type} systems{location}.")
            else:
                article = _article_for(cooling_type)
                cooling_sentences.append(
                    f"The primary cooling system is {article} {cooling_type} plant{location}."
                )
    else:
        cooling_sentences.append(not_confirmed_sentence("The central cooling system type"))

    if not cooling_distribution_unknown:
        serves = human_join(context.cooling_serves_values)
        cooling_sentences.append(f"Cooling is distributed through {serves}.")
    elif not cooling_unknown:
        cooling_sentences.append(
            further_investigation_sentence("the cooling distribution systems")
        )

    if context.cooling_notes_text and context.cooling_notes_text.strip():
        cooling_sentences.append(ensure_sentence(context.cooling_notes_text))
    elif not cooling_unknown:
        cooling_sentences.append(
            uncertainty_sentence(
                f"cooling equipment condition and controls were not fully verified for this {context.audit_level} review"
            )
        )

    if cooling_sentences:
        paragraphs.append(" ".join(cooling_sentences[:4]))

    if not paragraphs:
        return not_confirmed_sentence("Heating and cooling system details")

    return "\n\n".join(paragraphs)
