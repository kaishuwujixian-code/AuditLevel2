from typing import Any, Dict

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


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = {"audit_level": "L1", "confidence": "low", "unknown_policy": "soft"}
    override_text = first_meaningful_text(
        [
            get_answer_value(project, ["ventilation_block_override", "ventilation_block"]),
        ]
    )
    if override_text:
        return override_text

    system_type_raw = get_answer_value(
        project,
        ["ventilation.system_type", "ventilation_system_type", "system_type"],
        section="ventilation",
    )
    system_type_values = format_option_values(
        "ventilation.system_type", system_type_raw, mapping=mapping
    )
    notes_value = get_answer_value(
        project,
        ["ventilation_notes", "ventilation_block", "notes"],
        section="ventilation",
    )

    sentences: list[str] = []
    system_unknown = (
        not system_type_values
        or contains_unknown(system_type_values)
        or is_unknown_selection(system_type_raw)
    )

    if not system_unknown:
        system_type = human_join(system_type_values)
        sentences.append(f"Central ventilation is primarily served by {system_type}.")
    else:
        sentences.append(not_confirmed_sentence("The central ventilation system type"))
        sentences.append(further_investigation_sentence("the primary ventilation strategy"))

    sentences.append(
        uncertainty_sentence(
            f"operating schedules, air-change rates, and control sequences were not verified for this {context['audit_level']} review"
        )
    )

    notes_text = stringify_value(notes_value)
    if notes_text and notes_text.strip():
        sentences.append(ensure_sentence(notes_text))

    return " ".join(sentences[:5])
