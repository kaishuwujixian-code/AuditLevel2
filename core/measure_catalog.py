import json
import os
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
        "notes": str(measure.get("notes") or ""),
        "dependencies": str(measure.get("dependencies") or ""),
    }


def load_measure_catalog(path: str = DEFAULT_MEASURE_CATALOG) -> MeasureCatalog:
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"Measure catalog not found: {path}")

    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Measure catalog must be a JSON object.")

    categories = data.get("categories", [])
    if categories is None:
        categories = []
    if not isinstance(categories, list):
        raise ValueError("Measure catalog categories must be a list.")

    measures_data = data.get("measures", [])
    if not isinstance(measures_data, list):
        raise ValueError("Measure catalog measures must be a list.")

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
            "notes": str(entry.get("notes", "")),
            "dependencies": str(entry.get("dependencies", "")),
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
