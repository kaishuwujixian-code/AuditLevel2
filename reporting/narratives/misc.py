from dataclasses import dataclass
from typing import Any, Dict, List

from reporting.narratives import (
    first_meaningful_text,
    further_investigation_sentence,
    get_answer_value,
)
from reporting.narratives.checklists import render_block_appendix

BLOCK_PLACEHOLDERS = ["{Miscellaneous Block}"]
EXPECTED_INPUTS = {
    "{Miscellaneous Block}": {
        "section": "misc",
        "fields": ["misc_block_override", "misc_block", "misc_notes", "misc_items"],
    }
}


@dataclass(frozen=True)
class MiscContext:
    override_text: str | None
    items: List[Dict[str, Any]]

    @classmethod
    def from_project(cls, project: Dict[str, Any]) -> "MiscContext":
        override_text = first_meaningful_text(
            [get_answer_value(project, ["misc_block_override", "misc_block", "misc_notes"])]
        )
        return cls(override_text=override_text, items=_collect_misc_items(project))


def render_block(
    project: Dict[str, Any], *, schema: Dict[str, Any] | None = None, mapping: Dict[str, Any] | None = None
) -> str:
    context = MiscContext.from_project(project)
    checklist_text = render_block_appendix(project, target_block="misc")
    if context.override_text and context.items:
        blocks = [_render_misc_items(context.items), context.override_text]
        if checklist_text:
            blocks.append(checklist_text)
        return "\n\n".join(blocks)
    if context.override_text:
        if checklist_text:
            return "\n\n".join([context.override_text, checklist_text])
        return context.override_text

    if context.items:
        blocks = [_render_misc_items(context.items)]
        if checklist_text:
            blocks.append(checklist_text)
        return "\n\n".join(blocks)

    sentences = [
        "No additional miscellaneous systems were noted based on available information.",
        further_investigation_sentence("any supplementary equipment or scope items"),
    ]
    text = " ".join(sentences)
    if checklist_text:
        return "\n\n".join([text, checklist_text])
    return text


def _collect_misc_items(project: Dict[str, Any]) -> List[Dict[str, Any]]:
    answers = project.get("answers", {}) if isinstance(project, dict) else {}
    items = None
    if isinstance(answers, dict):
        items = answers.get("misc_items")
    if items is None:
        items = project.get("misc_items") if isinstance(project, dict) else None
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and _has_content(item)]


def _has_content(item: Dict[str, Any]) -> bool:
    for value in item.values():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False


def _render_misc_items(items: List[Dict[str, Any]]) -> str:
    blocks: List[str] = []
    for item in items:
        title = str(item.get("title", "")).strip()
        text = str(item.get("text", "")).strip()
        if title and text:
            blocks.append(f"{title}: {text}")
        elif text:
            blocks.append(text)
        elif title:
            blocks.append(title)
    return "\n\n".join(blocks)
