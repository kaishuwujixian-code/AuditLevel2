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
    distribution_raw: Any
    serves_values: List[str]
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
        distribution_raw = get_answer_value(
            project,
            ["hvac.heating_serves", "heating_serves", "serves"],
            section="heating",
        )
        serves_values = format_distribution_values(distribution_raw, mapping=mapping)
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
            distribution_raw=distribution_raw,
            serves_values=serves_values,
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


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = HeatingContext.from_project(project, mapping=mapping)
    if context.override_text:
        return context.override_text

    sentences: list[str] = []
    system_unknown = context.system_unknown()
    distribution_unknown = context.distribution_unknown()

    if not system_unknown and not distribution_unknown:
        system_type = human_join(context.system_type_values)
        serves = human_join(context.serves_values)
        if len(context.system_type_values) > 1 or len(context.serves_values) > 1:
            sentences.append(f"Heating is provided by {system_type} systems serving {serves}.")
        else:
            sentences.append(
                f"The building is served by a {system_type} heating plant with distribution through {serves}."
            )
    elif not system_unknown:
        system_type = human_join(context.system_type_values)
        sentences.append(f"The building is served by a {system_type} heating plant.")
        sentences.append(further_investigation_sentence("the serving distribution systems"))
    elif not distribution_unknown:
        serves = human_join(context.serves_values)
        sentences.append(f"Heat is distributed through {serves}.")
        sentences.append(not_confirmed_sentence("The heating plant type"))
        sentences.append(further_investigation_sentence("the central heating plant configuration"))
    else:
        sentences.append(not_confirmed_sentence("The heating plant type and distribution details"))
        sentences.append(further_investigation_sentence("the central heating plant configuration"))

    sentences.append(
        uncertainty_sentence(
            f"equipment condition and control sequences were not fully assessed for this {context.audit_level} review"
        )
    )

    if context.notes_text and context.notes_text.strip():
        sentences.append(ensure_sentence(context.notes_text))

    return " ".join(sentences[:6])
