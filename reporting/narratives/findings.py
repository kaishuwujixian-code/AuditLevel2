from typing import Any, Dict, Iterable, List, Tuple

BLOCK_PLACEHOLDERS = ["{FINDINGS_BLOCK}"]


def render_block(
    project: Dict[str, Any],
    *,
    schema: Dict[str, Any] | None = None,
    mapping: Dict[str, Any] | None = None,
) -> str:
    override = _extract_override(project)
    if override:
        return override

    selections = project.get("checklist_selections", {}) if isinstance(project, dict) else {}
    if not selections or not isinstance(selections, dict):
        return ""

    grouped_items = _collect_findings(selections)
    if not grouped_items:
        return ""

    lines: List[str] = [
        "Based on the walkthrough, the following observations were noted during the site visit:"
    ]
    for group_name, items in grouped_items:
        if group_name:
            lines.append(group_name)
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(line for line in lines if line.strip())


def _extract_override(project: Dict[str, Any]) -> str | None:
    answers = project.get("answers", {}) if isinstance(project, dict) else {}
    override = None
    if isinstance(answers, dict):
        override = answers.get("findings_block_override") or answers.get("findings_block")
    if not override:
        override = project.get("findings_block_override") or project.get("findings_block")
    if override:
        override = str(override).strip()
    return override or None


def _collect_findings(selections: Dict[str, Any]) -> List[Tuple[str, List[str]]]:
    grouped: List[Tuple[str, List[str]]] = []
    for group_name, group_value in selections.items():
        if _is_generic_group(group_name) and isinstance(group_value, dict):
            for category_name, items in group_value.items():
                normalized_items = _normalize_items(items)
                if normalized_items:
                    grouped.append((str(category_name).strip(), normalized_items))
            continue

        items = list(_flatten_group_items(group_value))
        if items:
            grouped.append((str(group_name).strip(), items))
    return grouped


def _flatten_group_items(group_value: Any) -> Iterable[str]:
    if isinstance(group_value, list):
        for item in group_value:
            item_text = _stringify_item(item)
            if item_text:
                yield item_text
        return

    if isinstance(group_value, dict):
        for category_name, items in group_value.items():
            normalized_items = _normalize_items(items)
            for item_text in normalized_items:
                yield f"{category_name}: {item_text}"


def _stringify_item(item: Any) -> str:
    if item is None:
        return ""
    text = str(item).strip()
    return text


def _normalize_items(items: Any) -> List[str]:
    normalized: List[str] = []
    if isinstance(items, list):
        for item in items:
            item_text = _stringify_item(item)
            if item_text:
                normalized.append(item_text)
        return normalized
    item_text = _stringify_item(items)
    if item_text:
        normalized.append(item_text)
    return normalized


def _is_generic_group(group_name: Any) -> bool:
    if not group_name:
        return False
    normalized = str(group_name).strip().lower()
    return normalized in {"walkthrough findings", "walkthrough", "findings"}
