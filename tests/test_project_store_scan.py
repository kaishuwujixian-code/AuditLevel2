import json

from core.project_store import scan_project_summaries


def _write_project(path, *, building_name="", site_address=""):
    data = {
        "project_info": {
            "building_name": building_name,
            "site_address": site_address,
        },
        "answers": {},
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_scan_project_summaries_includes_flat_json_and_project_json(tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    _write_project(projects_dir / "8 Hillcrest Ave.json", building_name="8 Hillcrest")
    _write_project(projects_dir / "example.json", building_name="Example Building")

    nested = projects_dir / "_example"
    nested.mkdir()
    _write_project(nested / "project.json", building_name="Nested Project")

    summaries, errors = scan_project_summaries(str(projects_dir))

    assert not errors
    names = {item.name for item in summaries}
    assert "8 Hillcrest" in names
    assert "Example Building" in names
    assert "Nested Project" in names


def test_scan_project_summaries_uses_filename_for_flat_json_without_building_name(tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()

    _write_project(projects_dir / "8 Hillcrest Ave.json", building_name="")

    summaries, errors = scan_project_summaries(str(projects_dir))

    assert not errors
    assert len(summaries) == 1
    assert summaries[0].name == "8 Hillcrest Ave"
