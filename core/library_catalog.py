import json
import os
from dataclasses import dataclass
from typing import Dict, List

from core.paths import CATALOGS_DIR


@dataclass(frozen=True)
class LibraryCatalog:
    categories: List[dict]
    items: Dict[str, dict]
    order: List[str]


def load_library_catalog(filename: str) -> LibraryCatalog:
    path = os.path.join(CATALOGS_DIR, filename)
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"Library catalog not found: {path}")

    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Library catalog must be a JSON object.")

    categories = data.get("categories", [])
    if categories is None:
        categories = []
    if not isinstance(categories, list):
        raise ValueError("Library catalog categories must be a list.")

    items_data = data.get("items", [])
    if not isinstance(items_data, list):
        raise ValueError("Library catalog items must be a list.")

    items: Dict[str, dict] = {}
    order: List[str] = []
    for entry in items_data:
        if not isinstance(entry, dict):
            continue
        item_id = str(entry.get("id", "")).strip()
        if not item_id:
            continue
        item = {
            "id": item_id,
            "title": str(entry.get("title", "")),
            "category": str(entry.get("category", "")),
            "text": str(entry.get("text", "")),
        }
        items[item_id] = item
        order.append(item_id)

    return LibraryCatalog(categories=categories, items=items, order=order)


def validate_library_catalog_data(data: dict) -> None:
    errors: List[str] = []
    categories = data.get("categories", [])
    if not isinstance(categories, list):
        errors.append("Library catalog categories must be a list.")
        categories = []

    category_codes: set[str] = set()
    for idx, entry in enumerate(categories):
        if not isinstance(entry, dict):
            errors.append(f"Category entry {idx + 1} must be an object.")
            continue
        code = str(entry.get("code", "")).strip()
        title = str(entry.get("title", "")).strip()
        if not code:
            errors.append(f"Category entry {idx + 1} is missing a code.")
        if not title:
            errors.append(f"Category entry {idx + 1} is missing a title.")
        if code and code in category_codes:
            errors.append(f"Category code '{code}' is duplicated.")
        if code:
            category_codes.add(code)

    items = data.get("items", [])
    if not isinstance(items, list):
        errors.append("Library catalog items must be a list.")
        items = []

    item_ids: set[str] = set()
    for idx, entry in enumerate(items):
        if not isinstance(entry, dict):
            errors.append(f"Item entry {idx + 1} must be an object.")
            continue
        item_id = str(entry.get("id", "")).strip()
        if not item_id:
            errors.append(f"Item entry {idx + 1} is missing an id.")
        elif item_id in item_ids:
            errors.append(f"Item id '{item_id}' is duplicated.")
        else:
            item_ids.add(item_id)
        category = str(entry.get("category", "")).strip()
        if category and category not in category_codes:
            errors.append(
                f"Item '{item_id or f'entry {idx + 1}'}' uses unknown category '{category}'."
            )

    if errors:
        raise ValueError("Library catalog validation failed:\n" + "\n".join(errors))


def save_library_catalog_data(
    filename: str,
    data: dict,
    *,
    backup: bool = True,
) -> None:
    if not isinstance(data, dict):
        raise ValueError("Library catalog must be a JSON object.")
    normalized = {
        "categories": data.get("categories", []) or [],
        "items": data.get("items", []) or [],
    }
    validate_library_catalog_data(normalized)
    path = os.path.join(CATALOGS_DIR, filename)
    if backup and path and os.path.isfile(path):
        backup_path = f"{path}.backup"
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(path, backup_path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
