import argparse
import json
import os
import re
from typing import Iterable, List, Sequence


DEFAULT_TEMPLATE_PATH = os.path.join("templates", "template.level1.json")


def _load_template(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Template JSON must be an object.")
    return data


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "project"


def _prompt(label: str) -> str:
    return input(f"{label}: ").strip()


def _parse_selection(selection: str, options: Sequence[str]) -> List[str]:
    if not selection.strip():
        return []
    indices = []
    for raw in selection.split(","):
        raw = raw.strip()
        if not raw:
            continue
        if not raw.isdigit():
            raise ValueError(f"Invalid selection: {raw}")
        index = int(raw)
        if index < 1 or index > len(options):
            raise ValueError(f"Selection out of range: {raw}")
        indices.append(index)
    seen = set()
    selected = []
    for index in indices:
        key = options[index - 1]
        if key not in seen:
            selected.append(key)
            seen.add(key)
    return selected


def _select_from_list(title: str, options: Sequence[str]) -> List[str]:
    print(f"\n{title}")
    for idx, option in enumerate(options, start=1):
        print(f"{idx}. {option}")
    selection = input("Select (comma-separated) or press Enter to skip: ")
    return _parse_selection(selection, options)


def _build_project_info() -> dict:
    print("Enter project info:")
    return {
        "client_name": _prompt("Client name"),
        "site_address": _prompt("Site address"),
        "building_name": _prompt("Building name"),
        "report_date": _prompt("Report date"),
        "prepared_by": _prompt("Prepared by"),
    }


def _build_notes() -> dict:
    return {
        "general_site_notes": "",
        "safety_hazards_observed": [],
        "maintenance_issues_observed": [],
        "comfort_complaints_reported": [],
    }


def _select_measures(template_data: dict) -> List[str]:
    measures = template_data.get("measures", {})
    if not isinstance(measures, dict):
        raise ValueError("Template JSON measures must be an object.")
    options = sorted(measures.keys())
    return _select_from_list("Select measures", options)


def _select_checklists(template_data: dict) -> dict:
    checklists = template_data.get("checklists", {})
    if not isinstance(checklists, dict):
        raise ValueError("Template JSON checklists must be an object.")
    selections = {}
    for group_name in checklists:
        categories = checklists[group_name]
        if not isinstance(categories, dict):
            continue
        group_selection = {}
        print(f"\nChecklist group: {group_name}")
        for category_name in categories:
            items = categories[category_name]
            if not isinstance(items, list):
                continue
            selected_items = _select_from_list(f"{category_name}", list(items))
            if selected_items:
                group_selection[category_name] = selected_items
        if group_selection:
            selections[group_name] = group_selection
    return selections


def _default_output_path(project_info: dict) -> str:
    slug_source = project_info.get("building_name") or project_info.get("site_address", "")
    slug = _slugify(slug_source)
    return os.path.join("projects", slug, "project.json")


def _ensure_output_dir(path: str) -> None:
    output_dir = os.path.dirname(path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)


def _write_project(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a new Level 1 project.json.")
    parser.add_argument(
        "--template",
        default=DEFAULT_TEMPLATE_PATH,
        help="Path to template.level1.json",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional output path for project.json",
    )
    parser.add_argument(
        "--no-checklists",
        action="store_true",
        help="Skip checklist selection prompts",
    )
    parser.add_argument(
        "--no-measures",
        action="store_true",
        help="Skip measures selection prompts",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    template_data = _load_template(args.template)

    project_info = _build_project_info()
    project_data = {
        "project_info": project_info,
        "selected_measures": [],
        "notes": _build_notes(),
    }

    if not args.no_measures:
        project_data["selected_measures"] = _select_measures(template_data)

    if not args.no_checklists:
        checklist_selections = _select_checklists(template_data)
        if checklist_selections:
            project_data["checklist_selections"] = checklist_selections

    output_path = args.out or _default_output_path(project_info)
    _ensure_output_dir(output_path)
    _write_project(output_path, project_data)
    print(f"Created: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
