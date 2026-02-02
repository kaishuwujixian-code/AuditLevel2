import json
import os
import shutil
from datetime import datetime
from typing import Dict, List

from core.paths import DEFAULT_TEMPLATE_JSON


def load_template_checklists(path: str = DEFAULT_TEMPLATE_JSON) -> Dict[str, dict]:
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"Template JSON not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    checklists = data.get("checklists", {}) or {}
    validate_checklists(checklists)
    return checklists


def save_template_checklists(
    checklists: Dict[str, dict],
    path: str = DEFAULT_TEMPLATE_JSON,
    *,
    backup: bool = True,
) -> None:
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"Template JSON not found: {path}")
    validate_checklists(checklists)
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(path, f"{path}.backup-{timestamp}")
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    data["checklists"] = checklists
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def validate_checklists(checklists: Dict[str, dict]) -> None:
    if not isinstance(checklists, dict):
        raise ValueError("checklists must be an object.")
    errors: List[str] = []
    for group_name, categories in checklists.items():
        if not isinstance(categories, dict):
            errors.append(f"Checklist group '{group_name}' must be an object.")
            continue
        for category_name, items in categories.items():
            if not isinstance(items, list):
                errors.append(
                    f"Checklist category '{group_name} / {category_name}' must be a list."
                )
                continue
            for item in items:
                if not isinstance(item, str):
                    errors.append(
                        f"Checklist item in '{group_name} / {category_name}' must be a string."
                    )
    if errors:
        raise ValueError("Checklist validation failed:\n" + "\n".join(errors))
