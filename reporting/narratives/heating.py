from typing import Any, Dict

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


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = {"audit_level": "L1", "confidence": "moderate", "unknown_policy": "soft"}
    override_text = first_meaningful_text(
        [
            get_answer_value(project, ["heating_block_override", "heating_block"]),
        ]
    )
    if override_text:
        return override_text

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

    sentences: list[str] = []
    system_unknown = (
        not system_type_values
        or contains_unknown(system_type_values)
        or is_unknown_selection(system_type_raw)
    )
    distribution_unknown = (
        not serves_values
        or contains_unknown(serves_values)
        or is_unknown_selection(distribution_raw)
    )

    if not system_unknown:
        system_type = human_join(system_type_values)
        sentences.append(f"The building is served by a {system_type} heating plant.")
    else:
        sentences.append(not_confirmed_sentence("The heating plant type"))
        sentences.append(further_investigation_sentence("the central heating plant configuration"))

    if not distribution_unknown:
        serves = human_join(serves_values)
        sentences.append(f"Heat is distributed through {serves}.")
    else:
        sentences.append(not_confirmed_sentence("Distribution details"))
        sentences.append(further_investigation_sentence("the serving distribution systems"))

    sentences.append(
        uncertainty_sentence(
            f"equipment condition and control sequences were not fully assessed for this {context['audit_level']} review"
        )
    )

    notes_text = stringify_value(notes_value)
    if notes_text and notes_text.strip():
        sentences.append(ensure_sentence(notes_text))

    return " ".join(sentences[:6])
