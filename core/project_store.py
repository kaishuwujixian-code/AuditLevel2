import json
import os
import re
from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class ProjectRecord:
    path: str
    building_name: str
    address: str
    report_date: str
    measures_count: int
    project_dir: str


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "project"


def _find_project_files(projects_dir: str) -> List[str]:
    project_files: List[str] = []
    if not os.path.isdir(projects_dir):
        return project_files
    for root, _dirs, files in os.walk(projects_dir):
        for filename in files:
            if filename == "project.json":
                project_files.append(os.path.join(root, filename))
    return sorted(project_files)


def _load_project(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("project.json must contain a JSON object.")
    return data


def _build_record(path: str, project_data: dict) -> ProjectRecord:
    project_info = project_data.get("project_info", {})
    if not isinstance(project_info, dict):
        project_info = {}

    building_name = str(project_info.get("building_name", "")).strip()
    address = str(project_info.get("site_address", "")).strip()
    report_date = str(project_info.get("report_date", "")).strip()

    selected_measures = project_data.get("selected_measures", [])
    if not isinstance(selected_measures, list):
        selected_measures = []

    project_dir = os.path.dirname(path)
    return ProjectRecord(
        path=path,
        building_name=building_name,
        address=address,
        report_date=report_date,
        measures_count=len(selected_measures),
        project_dir=project_dir,
    )


def scan_projects(projects_dir: str) -> Tuple[List[ProjectRecord], List[str]]:
    records: List[ProjectRecord] = []
    errors: List[str] = []
    for path in _find_project_files(projects_dir):
        try:
            project_data = _load_project(path)
            records.append(_build_record(path, project_data))
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"{path}: {exc}")
    return records, errors


def _fallback_slug(record: ProjectRecord) -> str:
    if record.building_name:
        return record.building_name
    return os.path.basename(record.project_dir)


def default_output_path(record: ProjectRecord, output_dir: str) -> str:
    slug_source = _fallback_slug(record)
    slug = _slugify(slug_source)
    filename = f"{slug}_level1_walkthrough.docx"
    return os.path.join(output_dir, filename)


def summarize_records(records: Sequence[ProjectRecord]) -> List[Tuple[str, str, str, int, str]]:
    return [
        (
            record.building_name,
            record.address,
            record.report_date,
            record.measures_count,
            record.path,
        )
        for record in records
    ]
