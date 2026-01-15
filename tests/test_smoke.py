from __future__ import annotations

import json
import zipfile
from pathlib import Path

from docx import Document

from core.project_store import load_project, save_project
from core.questionnaire import apply_answers_to_project, load_questionnaire_schema
from reporting.word_renderer import render_word


def test_project_roundtrip_and_render(tmp_path: Path) -> None:
    schema = load_questionnaire_schema("schemas/level1_questionnaire.schema.json")
    source_path = Path("projects/_example/project.json")
    project = json.loads(source_path.read_text(encoding="utf-8"))
    project["unknown_payload"] = {"keep": True}

    answers = project.get("answers", {})
    if not isinstance(answers, dict):
        answers = {}
    answers.update(
        {
            "client_name": "Acme Client",
            "site_address": "123 Main St",
            "building_name": "Test Tower",
            "architectural_condition": "fair",
            "heating_block": "Central plant observed; verify controls.",
        }
    )

    apply_answers_to_project(project, answers, schema, {"{ClientName}": "Acme Client"})
    project["selected_measures"] = ["BAS Upgrade", "Condensing Boiler Retrofit"]
    project["measure_overrides"] = {"BAS Upgrade": "Override narrative for BAS upgrade."}

    project_path = tmp_path / "project.json"
    save_project(str(project_path), project)

    reloaded = load_project(str(project_path))
    assert reloaded["unknown_payload"]["keep"] is True
    assert reloaded["answers"]["client_name"] == "Acme Client"

    output_path = tmp_path / "rendered.docx"
    render_word(
        template_path="templates/level1.docx",
        project_json_path=str(project_path),
        out_path=str(output_path),
    )
    assert output_path.exists()

    doc = Document(str(output_path))
    doc_text = "\n".join(_collect_doc_text(doc))
    assert "Building Automation System Upgrade" in doc_text
    assert "Hydronic balancing review" in doc_text

    with zipfile.ZipFile(output_path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    assert "{MEASURE_BLOCK}" not in xml
    assert "{FINDINGS_BLOCK}" not in xml


def _collect_doc_text(doc: Document) -> list[str]:
    paragraphs = []
    for paragraph in doc.paragraphs:
        if paragraph.text:
            paragraphs.append(paragraph.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if paragraph.text:
                        paragraphs.append(paragraph.text)
                paragraphs.extend(_collect_table_text(cell.tables))
    return paragraphs


def _collect_table_text(tables: list) -> list[str]:
    paragraphs = []
    for table in tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if paragraph.text:
                        paragraphs.append(paragraph.text)
                paragraphs.extend(_collect_table_text(cell.tables))
    return paragraphs
