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

BLOCK_PLACEHOLDERS = ["{Central Ventilation System Block}"]
EXPECTED_INPUTS = {
    "{Central Ventilation System Block}": {
        "section": "ventilation",
        "fields": [
            "ventilation_block_override",
            "ventilation_block",
            "ventilation.system_type",
            "ventilation_system_type",
            "ventilation_notes",
        ],
    }
}


@dataclass(frozen=True)
class VentilationContext:
    audit_level: str
    confidence: str
    unknown_policy: str
    override_text: str | None
    system_type_raw: Any
    system_type_values: List[str]
    location_text: str | None
    condition_text: str | None
    bas_present: Any
    notes_text: str | None

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
        return cls(
            audit_level="L1",
            confidence="low",
            unknown_policy="soft",
            override_text=override_text,
            system_type_raw=system_type_raw,
            system_type_values=system_type_values,
            location_text=location_text,
            condition_text=condition_text,
            bas_present=bas_present,
            notes_text=stringify_value(notes_value),
        )

    def system_unknown(self) -> bool:
        return (
            not self.system_type_values
            or contains_unknown(self.system_type_values)
            or is_unknown_selection(self.system_type_raw)
        )


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = VentilationContext.from_project(project, mapping=mapping)
    if context.override_text:
        return context.override_text

    paragraphs: list[str] = []
    sentences: list[str] = []
    system_unknown = context.system_unknown()

    if not system_unknown:
        system_type = human_join(context.system_type_values)
        location = ""
        if context.location_text and context.location_text.strip():
            location = f" located in {context.location_text.strip()}"
        sentences.append(f"Ventilation is primarily provided by {system_type}{location}.")
    else:
        sentences.append(not_confirmed_sentence("The central ventilation system type"))
        sentences.append(further_investigation_sentence("the primary ventilation strategy"))

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

    return "\n\n".join(paragraphs)
