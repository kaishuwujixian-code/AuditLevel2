import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class ProjectRecord:
    path: str
    building_name: str
    address: str
    report_date: str
    measures_count: int
    project_dir: str


@dataclass(frozen=True)
class ProjectSummary:
    name: str
    path: str
    folder: str


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "project"


def _find_project_files(projects_dir: str) -> List[str]:
    project_files: List[str] = []
    fallback_json_files: List[str] = []
    if not os.path.isdir(projects_dir):
        return project_files

    for root, _dirs, files in os.walk(projects_dir):
        for filename in files:
            lower_name = filename.lower()
            if lower_name == "project.json":
                project_files.append(os.path.join(root, filename))
                continue
            if lower_name.endswith(".json"):
                fallback_json_files.append(os.path.join(root, filename))

    all_candidates = {path for path in project_files}
    all_candidates.update(path for path in fallback_json_files if os.path.basename(path).lower() != "project.json")
    return sorted(all_candidates)


def _load_project(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("project.json must contain a JSON object.")
    normalize_measures_data(data)
    return data


def _build_record(path: str, project_data: dict) -> ProjectRecord:
    project_info = project_data.get("project_info", {})
    if not isinstance(project_info, dict):
        project_info = {}

    building_name = str(project_info.get("building_name", "")).strip()
    address = str(project_info.get("site_address", "")).strip()
    report_date = str(project_info.get("report_date", "")).strip()

    measures_count = _count_measures(project_data)

    project_dir = os.path.dirname(path)
    return ProjectRecord(
        path=path,
        building_name=building_name,
        address=address,
        report_date=report_date,
        measures_count=measures_count,
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


def default_output_path_for_summary(summary: ProjectSummary, output_dir: str) -> str:
    slug = _slugify(summary.name or os.path.basename(summary.folder))
    filename = f"{slug}_level1_walkthrough.docx"
    return os.path.join(output_dir, filename)


def default_output_path_for_project(project_data: Dict, project_path: str, output_dir: str) -> str:
    project_info = project_data.get("project_info", {})
    if not isinstance(project_info, dict):
        project_info = {}
    name = str(project_info.get("building_name") or "").strip()
    if not name:
        name = os.path.basename(os.path.dirname(project_path))
    slug = _slugify(name)
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


def scan_project_summaries(projects_dir: str) -> Tuple[List[ProjectSummary], List[str]]:
    summaries: List[ProjectSummary] = []
    errors: List[str] = []
    for path in _find_project_files(projects_dir):
        try:
            data = _load_project(path)
            project_info = data.get("project_info", {})
            if not isinstance(project_info, dict):
                project_info = {}
            name = str(project_info.get("building_name") or "").strip()
            folder = os.path.dirname(path)
            if not name:
                filename = os.path.basename(path)
                if filename.lower() == "project.json":
                    name = os.path.basename(folder)
                else:
                    name = os.path.splitext(filename)[0].strip() or os.path.basename(folder)
            summaries.append(ProjectSummary(name=name, path=path, folder=folder))
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"{path}: {exc}")
    return summaries, errors


def load_project(path: str) -> Dict:
    return _load_project(path)


def normalize_measures_data(project_data: Dict) -> None:
    answers = project_data.get("answers", {})
    if not isinstance(answers, dict):
        answers = {}

    measures = _extract_measures_list(project_data, answers)
    if not measures:
        legacy = answers.get("measures")
        if not legacy:
            legacy = project_data.get("measures")
        if isinstance(legacy, str) and legacy.strip():
            measures = [
                {
                    "measure_title": "Legacy measure",
                    "existing_conditions": legacy.strip(),
                }
            ]

    project_data["measures"] = measures
    answers["measures"] = measures
    project_data["answers"] = answers


def _extract_measures_list(project_data: Dict, answers: Dict) -> List[Dict]:
    for source in (project_data.get("measures"), answers.get("measures")):
        if isinstance(source, list):
            return [item for item in source if isinstance(item, dict)]
    return []


def _count_measures(project_data: Dict) -> int:
    measures = project_data.get("measures")
    if isinstance(measures, list):
        return len([item for item in measures if isinstance(item, dict)])
    selected_measures = project_data.get("selected_measures", [])
    if not isinstance(selected_measures, list):
        return 0
    return len(selected_measures)


def save_project(path: str, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
