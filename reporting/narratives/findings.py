from typing import Any, Dict, List

from reporting.narratives import ensure_sentence

BLOCK_PLACEHOLDERS = ["{FINDINGS_BLOCK}"]


def render_block(
    project: Dict[str, Any],
    *,
    schema: Dict[str, Any] | None = None,
    mapping: Dict[str, Any] | None = None,
) -> str:
    selections = project.get("checklist_selections", {}) if isinstance(project, dict) else {}
    if not selections:
        return ""
    if not isinstance(selections, dict):
        return ""
    paragraphs: List[str] = []
    group_names = sorted(selections.keys())
    include_group = len(group_names) > 1
    for group_name in group_names:
        categories = selections.get(group_name, {})
        if not isinstance(categories, dict):
            continue
        for category_name in sorted(categories.keys()):
            items = categories.get(category_name, [])
            if not isinstance(items, list):
                continue
            sentences = [
                ensure_sentence(str(item).strip())
                for item in items
                if str(item).strip()
            ]
            if not sentences:
                continue
            if include_group and group_name:
                label = f"{group_name} - {category_name}"
            else:
                label = category_name
            paragraph = f"{label}: " + " ".join(sentences)
            paragraphs.append(paragraph)
    return "\n\n".join(paragraphs)
