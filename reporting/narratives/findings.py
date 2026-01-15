from typing import Any, Dict, List

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
    lines: List[str] = []
    for group_name in sorted(selections.keys()):
        categories = selections.get(group_name, {})
        if not isinstance(categories, dict):
            continue
        lines.append(group_name)
        for category_name in sorted(categories.keys()):
            items = categories.get(category_name, [])
            if not isinstance(items, list):
                continue
            if items:
                items_text = ", ".join(str(item) for item in items)
            else:
                items_text = "(none)"
            lines.append(f"- {category_name}: {items_text}")
        lines.append("")
    return "\n".join(line for line in lines if line.strip())
