from typing import Any, Dict

from reporting.narratives import (
    ensure_sentence,
    first_meaningful_text,
    further_investigation_sentence,
    get_answer_value,
)

BLOCK_PLACEHOLDERS = ["{Miscellaneous Block}"]


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    override_text = first_meaningful_text(
        [
            get_answer_value(project, ["misc_block_override", "misc_block", "misc_notes"]),
        ]
    )
    if override_text:
        return ensure_sentence(override_text)

    sentences = [
        "No additional miscellaneous systems were noted based on available information.",
        further_investigation_sentence("any supplementary equipment or scope items"),
    ]
    return " ".join(sentences)
