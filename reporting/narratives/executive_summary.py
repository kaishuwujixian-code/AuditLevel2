from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from reporting.narratives.library_items import collect_items, render_items

BLOCK_PLACEHOLDERS = ["{Executive Summary Block}"]
EXPECTED_INPUTS = {
    "{Executive Summary Block}": {
        "description": "Executive summary narrative assembled from library selections or manual override.",
        "fields": [
            "executive_summary_block_override",
            "executive_summary_block",
            "executive_summary_notes",
            "executive_summary_items",
        ],
    }
}


@dataclass
class ExecutiveSummaryContext:
    override_text: str = ""
    items: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_project(cls, project: Dict[str, Any]) -> "ExecutiveSummaryContext":
        answers = project.get("answers", {}) if isinstance(project, dict) else {}
        override_text = ""
        if isinstance(answers, dict):
            for key in (
                "executive_summary_block_override",
                "executive_summary_block",
                "executive_summary_notes",
            ):
                candidate = answers.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    override_text = candidate.strip()
                    break
        return cls(
            override_text=override_text,
            items=collect_items(project, "executive_summary_items"),
        )


def render_block(
    project_data: Dict[str, Any],
    *,
    schema: Optional[Dict[str, Any]] = None,
    mapping: Optional[Dict[str, Any]] = None,
) -> str:
    context = ExecutiveSummaryContext.from_project(project_data)
    blocks: List[str] = []
    if context.items:
        blocks.append(render_items(context.items))
    if context.override_text:
        blocks.append(context.override_text)
    return "\n\n".join(block for block in blocks if isinstance(block, str) and block.strip()).strip()
