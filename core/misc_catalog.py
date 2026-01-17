import json
import os
from dataclasses import dataclass
from typing import Dict, List

from core.paths import CATALOGS_DIR


DEFAULT_MISC_CATALOG = os.path.join(CATALOGS_DIR, "misc_catalog.json")


@dataclass(frozen=True)
class MiscCatalog:
    categories: List[dict]
    items: Dict[str, dict]
    order: List[str]


def load_misc_catalog(path: str = DEFAULT_MISC_CATALOG) -> MiscCatalog:
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"Misc catalog not found: {path}")

    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Misc catalog must be a JSON object.")

    categories = data.get("categories", [])
    if categories is None:
        categories = []
    if not isinstance(categories, list):
        raise ValueError("Misc catalog categories must be a list.")

    items_data = data.get("items", [])
    if not isinstance(items_data, list):
        raise ValueError("Misc catalog items must be a list.")

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

    return MiscCatalog(categories=categories, items=items, order=order)
