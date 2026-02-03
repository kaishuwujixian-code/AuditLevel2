import argparse
import json
import os
import sys

from core.measure_catalog import load_measure_catalog
from reporting.word_renderer import render_word


def _ensure_file(path: str, label: str) -> None:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{label} not found: {path}")


def _load_json(path: str, label: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the Level 1 walkthrough report.")
    parser.add_argument("--project", default="project.json", help="Path to project.json")
    parser.add_argument(
        "--template",
        default="templates/template.level1.json",
        help="Path to the template JSON configuration",
    )
    parser.add_argument(
        "--docx-template",
        default="templates/level1.docx",
        help="Path to the Word (.docx) template",
    )
    parser.add_argument(
        "--out",
        default="output/level1_walkthrough.docx",
        help="Output path for the generated Word report",
    )
    parser.add_argument(
        "--list-measures",
        action="store_true",
        help="List all available measure keys from the template and exit",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate inputs only without generating the report",
    )
    return parser


def _list_measures(template_path: str) -> int:
    catalog = load_measure_catalog()
    for key in catalog.order:
        print(key)
    return 0


def _validate_inputs(project_path: str, template_path: str, docx_template_path: str) -> int:
    _ensure_file(project_path, "Project file")
    _ensure_file(template_path, "Template JSON file")
    _ensure_file(docx_template_path, "Docx template file")

    project_data = _load_json(project_path, "Project JSON file")
    template_data = _load_json(template_path, "Template JSON file")

    selected_measures = project_data.get("selected_measures", [])
    if selected_measures is None:
        selected_measures = []
    if not isinstance(selected_measures, list):
        raise ValueError("project.json selected_measures must be a list.")
    if not all(isinstance(item, str) for item in selected_measures):
        raise ValueError("project.json selected_measures must contain only strings.")

    catalog = load_measure_catalog()
    measures = catalog.measures
    overrides = template_data.get("category_by_measure_overrides", {})
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        raise ValueError("Template JSON category_by_measure_overrides must be an object.")

    missing = sorted(
        {
            key
            for key in selected_measures
            if key not in measures and key not in overrides and key not in catalog.legacy_key_map
        }
    )
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"Missing measures in template: {missing_list}")

    checklist_selections = project_data.get("checklist_selections", {})
    if checklist_selections is None:
        checklist_selections = {}
    if not isinstance(checklist_selections, dict):
        raise ValueError("project.json checklist_selections must be an object.")

    for group_name in sorted(checklist_selections.keys()):
        categories = checklist_selections[group_name]
        if not isinstance(categories, dict):
            raise ValueError("checklist_selections groups must be objects.")
        for category_name in sorted(categories.keys()):
            items = categories[category_name]
            if not isinstance(items, list):
                raise ValueError("checklist_selections categories must be lists.")
            if not all(isinstance(item, str) for item in items):
                raise ValueError("checklist_selections items must be strings.")

    print("OK")
    return 0


def main() -> int:
    print(
        "DEPRECATED: use python -m tools.render_level1 ... or python app_retscreen.py",
        file=sys.stderr,
    )
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.list_measures:
            return _list_measures(args.template)
        if args.validate:
            return _validate_inputs(args.project, args.template, args.docx_template)

        _ensure_file(args.project, "Project file")
        _ensure_file(args.template, "Template JSON file")
        _ensure_file(args.docx_template, "Docx template file")

        output_dir = os.path.dirname(args.out)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        render_word(
            template_path=args.docx_template,
            project_json_path=args.project,
            out_path=args.out,
        )

        print(f"Generated: {args.out}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
