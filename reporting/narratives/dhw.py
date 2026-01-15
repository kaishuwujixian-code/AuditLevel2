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

BLOCK_PLACEHOLDERS = ["{DHW System Block}"]
EXPECTED_INPUTS = {
    "{DHW System Block}": {
        "section": "dhw",
        "fields": [
            "dhw_block_override",
            "dhw_block",
            "dhw.system_type",
            "dhw_system_type",
            "dhw_heat_source",
            "dhw_recirc",
            "dhw_recirc_pumps",
            "dhw_storage_notes",
            "dhw_distribution_notes",
        ],
    }
}


@dataclass(frozen=True)
class DHWContext:
    audit_level: str
    confidence: str
    unknown_policy: str
    override_text: str | None
    system_type_raw: Any
    system_type_values: List[str]
    heat_source_text: str | None
    storage_notes_text: str | None
    recirc_value: Any

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
        return cls(
            audit_level="L1",
            confidence="moderate",
            unknown_policy="soft",
            override_text=override_text,
            system_type_raw=system_type_raw,
            system_type_values=system_type_values,
            heat_source_text=stringify_value(heat_source_value),
            storage_notes_text=stringify_value(storage_notes_value),
            recirc_value=recirc_value,
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
    context = DHWContext.from_project(project, mapping=mapping)
    if context.override_text:
        return context.override_text

    sentences: list[str] = []
    system_unknown = context.system_unknown()

    if not system_unknown:
        system_type = human_join(context.system_type_values)
        sentences.append(f"Domestic hot water is provided by {system_type}.")
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
    if context.storage_notes_text and context.storage_notes_text.strip():
        sentences.append(ensure_sentence(context.storage_notes_text))

    if len(sentences) < 3:
        sentences.append(
            uncertainty_sentence(
                f"additional domestic hot water distribution details were not confirmed for this {context.audit_level} review"
            )
        )

    return " ".join(sentences[:5])
