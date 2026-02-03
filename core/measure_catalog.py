import json
import os
import shutil
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List

from core.paths import DEFAULT_MEASURE_CATALOG


@dataclass(frozen=True)
class MeasureCatalog:
    measures: Dict[str, dict]
    order: List[str]
    categories: List[dict]
    legacy_key_map: Dict[str, str]


def get_measure(measure_id: str, catalog: MeasureCatalog | None = None) -> dict:
    if catalog is None:
        catalog = load_measure_catalog()
    measure = catalog.measures.get(measure_id, {})
    title = str(measure.get("title") or measure.get("name") or "").strip()
    return {
        "id": measure_id,
        "name": title,
        "title": title,
        "category": str(measure.get("category") or "").strip(),
        "existing": str(measure.get("existing") or ""),
        "retrofit": str(measure.get("retrofit") or ""),
        "summary": str(measure.get("summary") or ""),
    }


def load_measure_catalog(path: str = DEFAULT_MEASURE_CATALOG) -> MeasureCatalog:
    data = load_measure_catalog_data(path)
    categories = data["categories"]
    measures_data = data["measures"]

    measures: Dict[str, dict] = {}
    order: List[str] = []
    legacy_key_map: Dict[str, str] = {}
    for entry in measures_data:
        if not isinstance(entry, dict):
            continue
        measure_id = str(entry.get("id", "")).strip()
        if not measure_id:
            continue
        title = str(entry.get("title", "")).strip()
        category = str(entry.get("category", "")).strip()
        measure = {
            "id": measure_id,
            "name": title,
            "title": title,
            "category": category,
            "existing": str(entry.get("existing", "")),
            "retrofit": str(entry.get("retrofit", "")),
            "summary": str(entry.get("summary", "")),
        }
        measures[measure_id] = measure
        order.append(measure_id)
        legacy_key = entry.get("legacy_key")
        if isinstance(legacy_key, str) and legacy_key.strip():
            legacy_key_map[legacy_key.strip()] = measure_id

    return MeasureCatalog(
        measures=measures,
        order=order,
        categories=categories,
        legacy_key_map=legacy_key_map,
    )


def load_measure_catalog_data(path: str = DEFAULT_MEASURE_CATALOG) -> dict:
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"Measure catalog not found: {path}")

    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    normalized = normalize_measure_catalog_data(data)
    validate_measure_catalog_data(normalized)
    return normalized


def save_measure_catalog_data(
    data: dict,
    path: str = DEFAULT_MEASURE_CATALOG,
    *,
    backup: bool = True,
) -> None:
    normalized = normalize_measure_catalog_data(data)
    validate_measure_catalog_data(normalized)
    if backup and path and os.path.isfile(path):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = f"{path}.backup-{timestamp}"
        shutil.copy2(path, backup_path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def normalize_measure_catalog_data(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Measure catalog must be a JSON object.")

    categories = data.get("categories", [])
    if categories is None:
        categories = []
    measures = data.get("measures", [])
    if measures is None:
        measures = []
    return {
        "categories": categories,
        "measures": measures,
    }


def validate_measure_catalog_data(data: dict) -> None:
    errors: List[str] = []
    categories = data.get("categories", [])
    if not isinstance(categories, list):
        errors.append("Measure catalog categories must be a list.")
        categories = []

    category_codes: set[str] = set()
    for idx, entry in enumerate(categories):
        if not isinstance(entry, dict):
            errors.append(f"Category entry {idx + 1} must be an object.")
            continue
        code = str(entry.get("code", "")).strip()
        title = str(entry.get("tab_title", "")).strip()
        if not code:
            errors.append(f"Category entry {idx + 1} is missing a code.")
        if not title:
            errors.append(f"Category entry {idx + 1} is missing a tab_title.")
        if code and code in category_codes:
            errors.append(f"Category code '{code}' is duplicated.")
        if code:
            category_codes.add(code)

    measures = data.get("measures", [])
    if not isinstance(measures, list):
        errors.append("Measure catalog measures must be a list.")
        measures = []

    measure_ids: set[str] = set()
    legacy_keys: set[str] = set()
    for idx, entry in enumerate(measures):
        if not isinstance(entry, dict):
            errors.append(f"Measure entry {idx + 1} must be an object.")
            continue
        measure_id = str(entry.get("id", "")).strip()
        if not measure_id:
            errors.append(f"Measure entry {idx + 1} is missing an id.")
        elif measure_id in measure_ids:
            errors.append(f"Measure id '{measure_id}' is duplicated.")
        else:
            measure_ids.add(measure_id)

        category = str(entry.get("category", "")).strip()
        if category and category not in category_codes:
            errors.append(
                f"Measure '{measure_id or f'entry {idx + 1}'}' uses unknown category '{category}'."
            )

        legacy_key = entry.get("legacy_key")
        if isinstance(legacy_key, str) and legacy_key.strip():
            if legacy_key.strip() in legacy_keys:
                errors.append(f"Legacy key '{legacy_key.strip()}' is duplicated.")
            legacy_keys.add(legacy_key.strip())

    if errors:
        raise ValueError("Measure catalog validation failed:\n" + "\n".join(errors))
