from typing import Any, Dict, List


def collect_items(project: Dict[str, Any], storage_key: str) -> List[Dict[str, Any]]:
    answers = project.get("answers", {}) if isinstance(project, dict) else {}
    items = None
    if isinstance(answers, dict):
        items = answers.get(storage_key)
    if items is None:
        items = project.get(storage_key) if isinstance(project, dict) else None
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and has_content(item)]


def has_content(item: Dict[str, Any]) -> bool:
    for value in item.values():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return True
    return False


def render_items(items: List[Dict[str, Any]]) -> str:
    blocks: List[str] = []
    for item in items:
        title = str(item.get("title", "")).strip()
        text = str(item.get("text", "")).strip()
        if title and text:
            blocks.append(f"{underline_text(title + ':')}\n\n{text}")
        elif text:
            blocks.append(text)
        elif title:
            blocks.append(underline_text(title + ":"))
    return "\n\n".join(blocks)


def underline_text(text: str) -> str:
    return f"<u>{text}</u>"
