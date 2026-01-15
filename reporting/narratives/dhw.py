from typing import Any, Dict

from reporting.narratives import (
    contains_unknown,
    ensure_sentence,
    first_meaningful_text,
    format_option_values,
    get_answer_value,
    has_meaningful_value,
    human_join,
    is_unknown_selection,
    stringify_value,
)

BLOCK_PLACEHOLDERS = ["{DHW System Block}"]


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    override_text = first_meaningful_text(
        [
            get_answer_value(project, ["dhw_block_override", "dhw_block"]),
        ]
    )
    if override_text:
        return override_text

    system_type_raw = get_answer_value(
        project,
        ["dhw.system_type", "dhw_system_type", "system_type"],
        section="dhw",
    )
    system_type_values = format_option_values("dhw.system_type", system_type_raw, mapping=mapping)
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

    sentences: list[str] = []
    system_unknown = (
        not system_type_values
        or contains_unknown(system_type_values)
        or is_unknown_selection(system_type_raw)
    )

    if not system_unknown:
        system_type = human_join(system_type_values)
        sentences.append(f"Domestic hot water is provided by {system_type}.")
    else:
        sentences.append(
            "The domestic hot water plant type was not confirmed during the site visit and should be verified."
        )
    heat_source_text = stringify_value(heat_source_value)
    if heat_source_text and heat_source_text.strip():
        sentences.append(f"The heat source is {heat_source_text}.")
    if isinstance(recirc_value, bool):
        if recirc_value:
            sentences.append("A recirculation loop with circulation pumps was observed.")
        else:
            sentences.append("No domestic hot water recirculation loop was observed.")
    elif has_meaningful_value(recirc_value):
        sentences.append(ensure_sentence(str(recirc_value)))
    storage_notes_text = stringify_value(storage_notes_value)
    if storage_notes_text and storage_notes_text.strip():
        sentences.append(ensure_sentence(storage_notes_text))

    if len(sentences) < 3:
        sentences.append(
            "Additional domestic hot water distribution details should be confirmed during detailed review."
        )

    return " ".join(sentences[:5])
