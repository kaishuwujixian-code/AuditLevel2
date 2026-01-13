import argparse
import json
import os
import re
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_TEMPLATE_PATH = os.path.join("templates", "template.level1.json")


def _load_json(path: str) -> dict:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON must be an object: {path}")
    return data


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "project"


def _prompt(label: str, default: str = "", non_interactive: bool = False) -> str:
    if non_interactive:
        return default
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def _prompt_yes_no(
    label: str, default: bool = True, non_interactive: bool = False
) -> bool:
    if non_interactive:
        return default
    hint = "Y/n" if default else "y/N"
    value = input(f"{label} ({hint}): ").strip().lower()
    if not value:
        return default
    if value in {"y", "yes"}:
        return True
    if value in {"n", "no"}:
        return False
    print("Please enter y or n.")
    return _prompt_yes_no(label, default=default, non_interactive=non_interactive)


def _parse_selection(
    selection: str, options: Sequence[str], defaults: Sequence[str]
) -> List[str]:
    selection = selection.strip()
    if not selection:
        return list(defaults)

    raw_tokens = [token.strip() for token in selection.split(",") if token.strip()]
    if not raw_tokens:
        return list(defaults)

    toggle_mode = any(token.startswith(("+", "-")) for token in raw_tokens)
    if toggle_mode:
        selected = list(defaults)
        seen = set(selected)
        for token in raw_tokens:
            if not token.startswith(("+", "-")):
                raise ValueError("Toggle selections must use + or - prefixes.")
            sign = token[0]
            index_text = token[1:]
            if not index_text.isdigit():
                raise ValueError(f"Invalid selection: {token}")
            index = int(index_text)
            if index < 1 or index > len(options):
                raise ValueError(f"Selection out of range: {token}")
            key = options[index - 1]
            if sign == "+":
                if key not in seen:
                    selected.append(key)
                    seen.add(key)
            else:
                if key in seen:
                    selected = [item for item in selected if item != key]
                    seen.discard(key)
        return selected

    indices: List[int] = []
    for token in raw_tokens:
        if not token.isdigit():
            raise ValueError(f"Invalid selection: {token}")
        index = int(token)
        if index < 1 or index > len(options):
            raise ValueError(f"Selection out of range: {token}")
        indices.append(index)
    seen = set()
    selected: List[str] = []
    for index in indices:
        key = options[index - 1]
        if key not in seen:
            selected.append(key)
            seen.add(key)
    return selected


def _select_from_list(
    title: str,
    options: Sequence[str],
    defaults: Sequence[str],
    non_interactive: bool,
) -> List[str]:
    if non_interactive:
        return list(defaults)
    print(f"\n{title}")
    for idx, option in enumerate(options, start=1):
        marker = "*" if option in defaults else " "
        print(f"{idx}. [{marker}] {option}")
    prompt = "Select numbers, Enter to keep defaults, or use +N/-N to toggle: "
    selection = input(prompt)
    return _parse_selection(selection, options, defaults)


def _build_project_info(defaults: Optional[dict], non_interactive: bool) -> dict:
    defaults = defaults or {}
    print("Enter project info:") if not non_interactive else None
    return {
        "client_name": _prompt(
            "Client name", defaults.get("client_name", ""), non_interactive
        ),
        "site_address": _prompt(
            "Site address", defaults.get("site_address", ""), non_interactive
        ),
        "building_name": _prompt(
            "Building name", defaults.get("building_name", ""), non_interactive
        ),
        "report_date": _prompt(
            "Report date", defaults.get("report_date", ""), non_interactive
        ),
        "prepared_by": _prompt(
            "Prepared by", defaults.get("prepared_by", ""), non_interactive
        ),
    }


def _build_notes() -> dict:
    return {
        "general_site_notes": "",
        "safety_hazards_observed": [],
        "maintenance_issues_observed": [],
        "comfort_complaints_reported": [],
    }


def _select_measures(
    template_data: dict,
    defaults: Optional[Sequence[str]] = None,
    non_interactive: bool = False,
) -> List[str]:
    measures = template_data.get("measures", {})
    if not isinstance(measures, dict):
        raise ValueError("Template JSON measures must be an object.")
    options = sorted(measures.keys())
    return _select_from_list(
        "Select measures",
        options,
        list(defaults or []),
        non_interactive,
    )


def _select_checklists(
    template_data: dict,
    defaults: Optional[dict] = None,
    non_interactive: bool = False,
) -> dict:
    checklists = template_data.get("checklists", {})
    if not isinstance(checklists, dict):
        raise ValueError("Template JSON checklists must be an object.")
    defaults = defaults or {}
    selections: Dict[str, dict] = {}
    for group_name in sorted(checklists.keys()):
        categories = checklists[group_name]
        if not isinstance(categories, dict):
            continue
        group_selection: Dict[str, list] = {}
        if not non_interactive:
            print(f"\nChecklist group: {group_name}")
        group_defaults = defaults.get(group_name, {})
        for category_name in sorted(categories.keys()):
            items = categories[category_name]
            if not isinstance(items, list):
                continue
            default_items = list(group_defaults.get(category_name, []))
            selected_items = _select_from_list(
                f"{category_name}",
                list(items),
                default_items,
                non_interactive,
            )
            if selected_items:
                group_selection[category_name] = selected_items
        if group_selection:
            selections[group_name] = group_selection
    return selections


def _default_output_path(project_info: dict, slug_override: str = "") -> str:
    if slug_override:
        slug = _slugify(slug_override)
    else:
        slug_source = project_info.get("building_name") or project_info.get(
            "site_address", ""
        )
        slug = _slugify(slug_source)
    return os.path.join("projects", slug, "project.json")


def _ensure_output_dir(path: str) -> None:
    output_dir = os.path.dirname(path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)


def _write_project(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def _warn_unknown_measures(selected: Iterable[str], template_data: dict) -> None:
    measures = template_data.get("measures", {})
    if not isinstance(measures, dict):
        return
    unknown = [item for item in selected if item not in measures]
    if unknown:
        print(
            "Warning: measures not found in template: " + ", ".join(unknown),
            file=sys.stderr,
        )


def _warn_unknown_checklists(selections: dict, template_data: dict) -> None:
    checklists = template_data.get("checklists", {})
    if not isinstance(checklists, dict):
        return
    unknown_items: List[str] = []
    for group_name, group_selection in selections.items():
        group_template = checklists.get(group_name, {})
        if not isinstance(group_template, dict):
            for category, items in group_selection.items():
                unknown_items.extend(
                    f"{group_name}/{category}/{item}" for item in items
                )
            continue
        for category, items in group_selection.items():
            category_template = group_template.get(category, [])
            if not isinstance(category_template, list):
                unknown_items.extend(
                    f"{group_name}/{category}/{item}" for item in items
                )
                continue
            for item in items:
                if item not in category_template:
                    unknown_items.append(f"{group_name}/{category}/{item}")
    if unknown_items:
        print(
            "Warning: checklist selections not found in template: "
            + ", ".join(unknown_items),
            file=sys.stderr,
        )


def _merge_unknown_defaults(
    selected: List[str], defaults: Sequence[str], options: Sequence[str]
) -> List[str]:
    unknown = [item for item in defaults if item not in options]
    return selected + [item for item in unknown if item not in selected]


def _merge_unknown_checklists(selected: dict, defaults: dict, template_data: dict) -> dict:
    checklists = template_data.get("checklists", {})
    if not isinstance(checklists, dict):
        return selected
    merged = json.loads(json.dumps(selected))
    for group_name, group_defaults in defaults.items():
        if group_name not in merged:
            merged[group_name] = {}
        group_template = checklists.get(group_name, {})
        for category, items in group_defaults.items():
            if category not in merged[group_name]:
                merged[group_name][category] = []
            category_template = group_template.get(category, []) if isinstance(group_template, dict) else []
            for item in items:
                if item not in category_template and item not in merged[group_name][category]:
                    merged[group_name][category].append(item)
    cleaned = {
        group: {category: items for category, items in categories.items() if items}
        for group, categories in merged.items()
        if categories
    }
    return cleaned


def _parse_overrides(values: Optional[Sequence[str]]) -> Tuple[dict, dict]:
    project_info_overrides: Dict[str, str] = {}
    notes_overrides: Dict[str, str] = {}
    for entry in values or []:
        if "=" not in entry:
            raise ValueError(f"Invalid --set value (expected key=value): {entry}")
        key, value = entry.split("=", 1)
        value = value.strip().strip('"')
        key = key.strip()
        if key.startswith("project_info."):
            field = key.split(".", 1)[1]
            project_info_overrides[field] = value
        elif key == "notes.general_site_notes":
            notes_overrides["general_site_notes"] = value
        else:
            raise ValueError(
                "Only project_info.* and notes.general_site_notes can be set via --set."
            )
    return project_info_overrides, notes_overrides


def _apply_overrides(project_info: dict, notes: dict, overrides: Tuple[dict, dict]) -> None:
    project_info_overrides, notes_overrides = overrides
    for key, value in project_info_overrides.items():
        project_info[key] = value
    for key, value in notes_overrides.items():
        notes[key] = value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or reuse a Level 1 project.json.")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--new", action="store_true", help="Create a new project")
    mode_group.add_argument(
        "--clone", metavar="PROJECT", help="Clone an existing project.json"
    )
    mode_group.add_argument(
        "--reuse", metavar="PROJECT", help="Reuse selections from an existing project.json"
    )
    parser.add_argument(
        "--template",
        default=DEFAULT_TEMPLATE_PATH,
        help="Path to template.level1.json",
    )
    parser.add_argument("--out", default="", help="Optional output path for project.json")
    parser.add_argument("--slug", default="", help="Override slug for projects/<slug>")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not prompt; rely on defaults and --set",
    )
    parser.add_argument(
        "--set",
        dest="set_values",
        action="append",
        help="Override fields (e.g., --set project_info.client_name=ABC)",
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


def _run_new(args: argparse.Namespace, template_data: dict) -> dict:
    project_info = _build_project_info({}, args.non_interactive)
    notes = _build_notes()
    project_data = {
        "project_info": project_info,
        "selected_measures": [],
        "notes": notes,
    }

    if not args.no_measures:
        project_data["selected_measures"] = _select_measures(
            template_data, non_interactive=args.non_interactive
        )

    if not args.no_checklists:
        checklist_selections = _select_checklists(
            template_data, non_interactive=args.non_interactive
        )
        if checklist_selections:
            project_data["checklist_selections"] = checklist_selections

    return project_data


def _run_clone(args: argparse.Namespace, template_data: dict) -> dict:
    existing = _load_json(args.clone)
    existing_info = existing.get("project_info", {})
    project_info = _build_project_info(existing_info, args.non_interactive)

    keep_measures = _prompt_yes_no(
        "Keep selected measures?", True, args.non_interactive
    )
    keep_checklists = _prompt_yes_no(
        "Keep checklist selections?", True, args.non_interactive
    )
    keep_notes = _prompt_yes_no(
        "Keep notes?", False, args.non_interactive
    )

    project_data = {
        "project_info": project_info,
        "selected_measures": existing.get("selected_measures", []) if keep_measures else [],
        "notes": existing.get("notes", {}) if keep_notes else _build_notes(),
    }

    if keep_checklists:
        existing_checklists = existing.get("checklist_selections", {})
        if existing_checklists:
            project_data["checklist_selections"] = existing_checklists

    _warn_unknown_measures(project_data.get("selected_measures", []), template_data)
    if "checklist_selections" in project_data:
        _warn_unknown_checklists(project_data["checklist_selections"], template_data)

    return project_data


def _run_reuse(args: argparse.Namespace, template_data: dict) -> dict:
    existing = _load_json(args.reuse)
    existing_info = existing.get("project_info", {})
    project_info = _build_project_info(existing_info, args.non_interactive)
    notes = _build_notes()

    project_data = {
        "project_info": project_info,
        "selected_measures": [],
        "notes": notes,
    }

    existing_measures = existing.get("selected_measures", [])
    existing_checklists = existing.get("checklist_selections", {})

    if not args.no_measures:
        measures = template_data.get("measures", {})
        options = sorted(measures.keys()) if isinstance(measures, dict) else []
        selected = _select_measures(
            template_data, defaults=existing_measures, non_interactive=args.non_interactive
        )
        project_data["selected_measures"] = _merge_unknown_defaults(
            selected, existing_measures, options
        )

    if not args.no_checklists:
        selected_checklists = _select_checklists(
            template_data,
            defaults=existing_checklists,
            non_interactive=args.non_interactive,
        )
        merged_checklists = _merge_unknown_checklists(
            selected_checklists, existing_checklists, template_data
        )
        if merged_checklists:
            project_data["checklist_selections"] = merged_checklists

    _warn_unknown_measures(project_data.get("selected_measures", []), template_data)
    if "checklist_selections" in project_data:
        _warn_unknown_checklists(project_data["checklist_selections"], template_data)

    return project_data


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.new and not args.clone and not args.reuse:
        args.new = True

    template_data = _load_json(args.template)

    if args.new:
        project_data = _run_new(args, template_data)
    elif args.clone:
        project_data = _run_clone(args, template_data)
    else:
        project_data = _run_reuse(args, template_data)

    overrides = _parse_overrides(args.set_values)
    _apply_overrides(project_data["project_info"], project_data["notes"], overrides)

    output_path = args.out or _default_output_path(
        project_data["project_info"], slug_override=args.slug
    )
    _ensure_output_dir(output_path)
    _write_project(output_path, project_data)
    print(f"Created: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
