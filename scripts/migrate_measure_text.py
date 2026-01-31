#!/usr/bin/env python3
"""Migrate existing/retrofit text from measure and summary config to measure_catalog.json."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Dict, Tuple


def load_measure_templates(config_path: pathlib.Path) -> Dict[str, Dict[str, Any]]:
    namespace: Dict[str, Any] = {}
    config_code = config_path.read_text(encoding="utf-8")
    exec(compile(config_code, str(config_path), "exec"), namespace)
    templates = namespace.get("MEASURE_TEMPLATES")
    if not isinstance(templates, dict):
        raise RuntimeError("MEASURE_TEMPLATES not found or not a dict in config file.")
    return templates


def load_measure_catalog(catalog_path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def update_catalog(
    catalog: Dict[str, Any],
    templates: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Any], list[str]]:
    measures = catalog.get("measures")
    if not isinstance(measures, list):
        raise RuntimeError("measure_catalog.json missing measures list")

    unmatched: list[str] = []
    for measure in measures:
        legacy_key = measure.get("legacy_key")
        if legacy_key in templates:
            template = templates[legacy_key]
            if "existing" in template:
                measure["existing"] = template["existing"]
            if "retrofit" in template:
                measure["retrofit"] = template["retrofit"]
        else:
            unmatched.append(str(legacy_key))
    return catalog, unmatched


def write_catalog(catalog_path: pathlib.Path, catalog: Dict[str, Any]) -> None:
    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate existing/retrofit text into measure_catalog.json",
    )
    parser.add_argument(
        "--config",
        default="catalogs/measure and summary.json",
        help="Path to measure and summary config file.",
    )
    parser.add_argument(
        "--catalog",
        default="catalogs/measure_catalog.json",
        help="Path to measure catalog JSON.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary without writing changes.",
    )
    args = parser.parse_args()

    config_path = pathlib.Path(args.config)
    catalog_path = pathlib.Path(args.catalog)

    templates = load_measure_templates(config_path)
    catalog = load_measure_catalog(catalog_path)
    updated_catalog, unmatched = update_catalog(catalog, templates)

    if not args.dry_run:
        write_catalog(catalog_path, updated_catalog)

    print("Migration complete.")
    print(f"Total measures in catalog: {len(updated_catalog.get('measures', []))}")
    print(f"Unmatched legacy_keys: {len(unmatched)}")
    if unmatched:
        for key in unmatched:
            print(f"- {key}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
