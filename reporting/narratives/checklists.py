from __future__ import annotations

from typing import Any, Dict, List

from core.checklist_store import load_template_checklists
from reporting.narratives import ensure_sentence


def render_block_appendix(project: Dict[str, Any], target_block: str) -> str:
    selections = project.get("checklist_selections", {}) if isinstance(project, dict) else {}
    if not isinstance(selections, dict) or not selections:
        return ""
    try:
        template_checklists = load_template_checklists()
    except Exception:
        template_checklists = {}
    if not isinstance(template_checklists, dict) or not template_checklists:
        return ""

    paragraphs: List[str] = []
    for group_name, categories in selections.items():
        if not isinstance(categories, dict):
            continue
        template_categories = template_checklists.get(group_name, {})
        for category_name, items in categories.items():
            if not isinstance(items, list):
                continue
            if not _category_matches_target(template_categories, category_name, target_block):
                continue
            sentences = [
                ensure_sentence(_resolve_item_text(template_categories, category_name, item))
                for item in items
                if str(item).strip()
            ]
            if not sentences:
                continue
            paragraph = f"{category_name}: " + " ".join(sentences)
            paragraphs.append(paragraph)
    return "\n\n".join(paragraphs)


def _category_matches_target(
    template_categories: object, category_name: str, target_block: str
) -> bool:
    if not isinstance(template_categories, dict):
        return False
    category_data = template_categories.get(category_name)
    if isinstance(category_data, dict):
        target = str(category_data.get("target_block", "")).strip().lower()
        return target == target_block
    if isinstance(category_data, list):
        return target_block == "misc"
    return False


def _resolve_item_text(
    template_categories: object, category_name: str, selected_item: object
) -> str:
    label = str(selected_item).strip()
    if not label:
        return ""
    if not isinstance(template_categories, dict):
        return label
    category_data = template_categories.get(category_name)
    if isinstance(category_data, dict):
        items = category_data.get("items", [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    item_label = item.get("label")
                    if isinstance(item_label, str) and item_label.strip() == label:
                        text = item.get("text")
                        return str(text).strip() if text is not None else label
                elif isinstance(item, str) and item.strip() == label:
                    return label
    return label
