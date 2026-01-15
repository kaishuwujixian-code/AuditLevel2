from dataclasses import dataclass
from typing import Any, Dict

from reporting.narratives import (
    first_meaningful_text,
    further_investigation_sentence,
    get_answer_value,
)

BLOCK_PLACEHOLDERS = ["{Miscellaneous Block}"]
EXPECTED_INPUTS = {
    "{Miscellaneous Block}": {
        "section": "misc",
        "fields": ["misc_block_override", "misc_block", "misc_notes"],
    }
}


@dataclass(frozen=True)
class MiscContext:
    override_text: str | None

    @classmethod
    def from_project(cls, project: Dict[str, Any]) -> "MiscContext":
        override_text = first_meaningful_text(
            [get_answer_value(project, ["misc_block_override", "misc_block", "misc_notes"])]
        )
        return cls(override_text=override_text)


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = MiscContext.from_project(project)
    if context.override_text:
        return context.override_text

    sentences = [
        "No additional miscellaneous systems were noted based on available information.",
        further_investigation_sentence("any supplementary equipment or scope items"),
    ]
    return " ".join(sentences)
