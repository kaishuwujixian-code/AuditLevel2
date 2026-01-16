import json
import os
import re
import zipfile
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from core.measure_catalog import load_measure_catalog
from reporting.narratives import facility_overview, measures as measure_narratives
from reporting.narratives.registry import KNOWN_BLOCK_PLACEHOLDERS, get_block_renderer


PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}")
DEFAULT_MAPPING_PATH = os.path.join("schemas", "level1_placeholders.map.json")
DEFAULT_EMPTY_BLOCK_TEXT = ""


def _normalize_key(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", text.strip().lower())
    return normalized.strip("_")


def _iter_paragraphs_in_tables(tables: Iterable) -> Iterable:
    for table in tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    yield paragraph
                for paragraph in _iter_paragraphs_in_tables(cell.tables):
                    yield paragraph


def _iter_all_paragraphs(doc: Document) -> Iterable:
    for paragraph in doc.paragraphs:
        yield paragraph
    for paragraph in _iter_paragraphs_in_tables(doc.tables):
        yield paragraph
    for section in doc.sections:
        for paragraph in section.header.paragraphs:
            yield paragraph
        for paragraph in _iter_paragraphs_in_tables(section.header.tables):
            yield paragraph
        for paragraph in section.footer.paragraphs:
            yield paragraph
        for paragraph in _iter_paragraphs_in_tables(section.footer.tables):
            yield paragraph


def _stringify_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)


def _has_meaningful_value(value: Any) -> bool:
    string_value = _stringify_value(value)
    return string_value is not None and bool(string_value.strip())


def _is_block_placeholder(placeholder: str) -> bool:
    if not placeholder.startswith("{") or not placeholder.endswith("}"):
        return False
    inner_text = placeholder[1:-1].strip()
    return (
        inner_text.endswith(" block")
        or inner_text.endswith("_BLOCK")
        or placeholder in KNOWN_BLOCK_PLACEHOLDERS
    )


def _load_mapping(mapping_path: Optional[str]) -> Optional[Dict[str, str]]:
    if mapping_path is None:
        mapping_path = DEFAULT_MAPPING_PATH if os.path.isfile(DEFAULT_MAPPING_PATH) else None
    if mapping_path is None:
        return None
    if not os.path.isfile(mapping_path):
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
    with open(mapping_path, "r", encoding="utf-8") as handle:
        mapping_data = json.load(handle)
    if not isinstance(mapping_data, dict):
        raise ValueError("Mapping file must contain a JSON object of placeholder-to-question mappings.")
    return {str(key): str(value) for key, value in mapping_data.items()}


def _build_placeholder_map_from_placeholders(placeholders: Dict[str, Any]) -> Dict[str, str]:
    placeholder_map: Dict[str, str] = {}
    for placeholder, value in placeholders.items():
        string_value = _stringify_value(value)
        if string_value is not None:
            placeholder_map[str(placeholder)] = string_value
    return placeholder_map




def _build_placeholder_map_from_answers(
    answers: Dict[str, Any],
    placeholders: Iterable[str],
    mapping_path: Optional[str],
) -> Dict[str, str]:
    placeholder_map: Dict[str, str] = {}
    mapping_data = _load_mapping(mapping_path)

    if mapping_data:
        for placeholder, question_id in mapping_data.items():
            value = answers.get(question_id)
            string_value = _stringify_value(value)
            if string_value is not None:
                placeholder_map[placeholder] = string_value

    for question_id, value in answers.items():
        string_value = _stringify_value(value)
        if string_value is not None:
            placeholder_map.setdefault(f"{{{question_id}}}", string_value)

    if mapping_data is None:
        normalized_answers = {
            _normalize_key(question_id): value
            for question_id, value in answers.items()
            if _stringify_value(value) is not None
        }
        for placeholder in placeholders:
            if placeholder in placeholder_map:
                continue
            inner_text = placeholder[1:-1]
            normalized_placeholder = _normalize_key(inner_text)
            if normalized_placeholder in normalized_answers:
                placeholder_map[placeholder] = _stringify_value(
                    normalized_answers[normalized_placeholder]
                )

    return placeholder_map


def _replace_placeholders_in_text(text: str, placeholder_map: Dict[str, str]) -> Tuple[str, int]:
    replaced_text = text
    replacements = 0
    for placeholder, value in placeholder_map.items():
        if placeholder in replaced_text:
            replacements += replaced_text.count(placeholder)
            replaced_text = replaced_text.replace(placeholder, value)
    return replaced_text, replacements


def _add_paragraph_after(paragraph: Paragraph, text: str = "", style=None) -> Paragraph:
    new_p_elm = OxmlElement("w:p")
    paragraph._element.addnext(new_p_elm)
    new_p = Paragraph(new_p_elm, paragraph._parent)
    if style is not None:
        new_p.style = style
    if text:
        new_p.add_run(text)
    return new_p


def _extract_num_pr(paragraph: Paragraph) -> Optional[OxmlElement]:
    ppr = paragraph._element.pPr
    if ppr is None:
        return None
    num_pr = ppr.find(qn("w:numPr"))
    return num_pr


def _apply_numbering(paragraph: Paragraph, num_pr: Optional[OxmlElement]) -> None:
    if num_pr is None:
        return
    ppr = paragraph._element.get_or_add_pPr()
    existing = ppr.find(qn("w:numPr"))
    if existing is not None:
        ppr.remove(existing)
    ppr.append(deepcopy(num_pr))


def _find_measure_reference_paragraph(doc: Document) -> Optional[Paragraph]:
    pattern = re.compile(r"\bMeasure\s*[–-]", re.IGNORECASE)
    for paragraph in _iter_all_paragraphs(doc):
        if paragraph.text and pattern.search(paragraph.text):
            return paragraph
    return None


def _format_measure_heading(title: str) -> str:
    cleaned = title.strip() if title else ""
    return f"Measure \u2013 {cleaned}" if cleaned else "Measure"


def _insert_structured_measures(
    paragraph: Paragraph,
    measures: List[Dict[str, Any]],
    *,
    heading_style: Any,
    heading_num_pr: Optional[OxmlElement],
    body_style: Any,
) -> None:
    current = paragraph
    for idx, measure in enumerate(measures):
        heading = _format_measure_heading(measure.get("measure_title", ""))
        if idx == 0:
            heading_para = current
        else:
            heading_para = _add_paragraph_after(current)
        heading_para.text = heading
        if heading_style is not None:
            heading_para.style = heading_style
        _apply_numbering(heading_para, heading_num_pr)
        current = heading_para

        existing = (measure.get("existing_conditions") or "").strip()
        retrofit = (measure.get("retrofit_recommendation") or "").strip()
        notes = (measure.get("notes") or "").strip()
        for text in (
            f"Existing Conditions: {existing}" if existing else "",
            f"Retrofit Recommendation: {retrofit}" if retrofit else "",
            f"Notes: {notes}" if notes else "",
        ):
            if not text:
                continue
            current = _add_paragraph_after(current, text=text, style=body_style)


def _split_block_paragraphs(text: str) -> List[str]:
    lines = text.splitlines()
    paragraphs: List[str] = []
    buffer: List[str] = []
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            if buffer:
                paragraphs.append(" ".join(buffer).strip())
                buffer = []
            continue
        buffer.append(cleaned)
    if buffer:
        paragraphs.append(" ".join(buffer).strip())
    if not paragraphs and text.strip():
        return [text.strip()]
    return paragraphs


def _iter_xml_parts(docx_path: str) -> Iterable[Tuple[str, bytes]]:
    with zipfile.ZipFile(docx_path) as archive:
        for info in archive.infolist():
            if not info.filename.startswith("word/") or not info.filename.endswith(".xml"):
                continue
            if info.filename == "word/document.xml" or info.filename.startswith(
                ("word/header", "word/footer")
            ):
                yield info.filename, archive.read(info.filename)


def _collect_placeholders_from_docx(docx_path: str) -> List[str]:
    placeholders: List[str] = []
    for _, xml_bytes in _iter_xml_parts(docx_path):
        text = xml_bytes.decode("utf-8", errors="ignore")
        placeholders.extend(PLACEHOLDER_PATTERN.findall(text))
    return placeholders


def _replace_placeholders_in_docx_xml(
    docx_path: str, placeholder_map: Dict[str, str]
) -> int:
    if not placeholder_map:
        return 0
    temp_path = f"{docx_path}.tmp"
    replacements = 0
    with zipfile.ZipFile(docx_path, "r") as archive, zipfile.ZipFile(
        temp_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as output:
        for info in archive.infolist():
            data = archive.read(info.filename)
            if info.filename.startswith("word/") and info.filename.endswith(".xml") and (
                info.filename == "word/document.xml"
                or info.filename.startswith(("word/header", "word/footer"))
            ):
                text = data.decode("utf-8", errors="ignore")
                replaced_text, part_replacements = _replace_placeholders_in_text(
                    text, placeholder_map
                )
                replacements += part_replacements
                data = replaced_text.encode("utf-8")
            output.writestr(info, data)
    os.replace(temp_path, docx_path)
    return replacements


def render_word(
    template_path: str,
    project_json_path: str,
    out_path: str,
    mapping_path: Optional[str] = None,
    strict: bool = False,
) -> Dict[str, Any]:
    """
    Render a Word document by replacing placeholders using project JSON.

    Note: python-docx does not expose text inside shapes/textboxes, so those placeholders
    may remain unresolved until the XML fallback replacement runs.
    """
    with open(project_json_path, "r", encoding="utf-8") as handle:
        project_data = json.load(handle)

    doc = Document(template_path)
    placeholder_occurrences = _collect_placeholders_from_docx(template_path)
    placeholder_set = set(placeholder_occurrences)

    project_placeholders = project_data.get("placeholders")
    answers = project_data.get("answers", {})
    if "placeholders" in project_data and isinstance(project_placeholders, dict):
        placeholder_map = _build_placeholder_map_from_placeholders(project_placeholders)
        facility_overview.apply_facility_placeholders(project_data, placeholder_map)
    else:
        if not isinstance(answers, dict):
            raise ValueError("project['answers'] must be a JSON object.")
        placeholder_map = _build_placeholder_map_from_answers(
            answers, placeholder_set, mapping_path
        )
        facility_overview.apply_facility_placeholders(project_data, placeholder_map)

    mapping_data = _load_mapping(mapping_path)
    base_placeholder_map = dict(placeholder_map)
    block_placeholders = [ph for ph in placeholder_occurrences if _is_block_placeholder(ph)]
    placeholder_map = {
        placeholder: value
        for placeholder, value in placeholder_map.items()
        if not _is_block_placeholder(placeholder)
    }

    measure_catalog = None
    if any(
        ph in ("{MEASURE_BLOCK}", "{MEASURE_SUMMARY_ROW}") for ph in block_placeholders
    ):
        try:
            measure_catalog = load_measure_catalog()
        except FileNotFoundError:
            measure_catalog = None

    structured_measures = measure_narratives.collect_structured_measures(project_data)
    measure_reference = _find_measure_reference_paragraph(doc) if structured_measures else None
    heading_style = None
    heading_num_pr = None
    if measure_reference is not None:
        heading_style = measure_reference.style
        heading_num_pr = _extract_num_pr(measure_reference)
    if heading_style is None:
        try:
            heading_style = doc.styles["List Number"]
        except KeyError:
            heading_style = None

    blocks_rendered: List[str] = []
    blocks_unresolved: List[str] = []
    block_replacements: Dict[str, str] = {}
    for placeholder in block_placeholders:
        if placeholder == "{MEASURE_BLOCK}" and structured_measures:
            rendered_text = DEFAULT_EMPTY_BLOCK_TEXT
        else:
            renderer = get_block_renderer(placeholder)
            if renderer:
                renderer_kwargs: Dict[str, Any] = {"schema": None, "mapping": mapping_data}
                if placeholder in ("{MEASURE_BLOCK}", "{MEASURE_SUMMARY_ROW}"):
                    renderer_kwargs.update(
                        {
                            "catalog": measure_catalog,
                            "placeholders": base_placeholder_map,
                        }
                    )
                rendered_text = renderer(project_data, **renderer_kwargs)
            else:
                rendered_text = DEFAULT_EMPTY_BLOCK_TEXT
        if not _has_meaningful_value(rendered_text):
            rendered_text = DEFAULT_EMPTY_BLOCK_TEXT
            blocks_unresolved.append(placeholder)
        block_replacements[placeholder] = rendered_text
        blocks_rendered.append(placeholder)

    replacement_map = {**placeholder_map, **block_replacements}
    block_paragraphs = {
        placeholder: _split_block_paragraphs(text)
        for placeholder, text in block_replacements.items()
    }

    placeholders_found = len(placeholder_occurrences)
    placeholders_replaced = 0
    unresolved: Set[str] = set()

    for paragraph in _iter_all_paragraphs(doc):
        text = paragraph.text
        if not text or "{" not in text:
            continue
        found = PLACEHOLDER_PATTERN.findall(text)
        if not found:
            continue
        replaced_text = text
        expanded_block = False
        if structured_measures and text.strip() == "{MEASURE_BLOCK}":
            _insert_structured_measures(
                paragraph,
                structured_measures,
                heading_style=heading_style,
                heading_num_pr=heading_num_pr,
                body_style=paragraph.style,
            )
            placeholders_replaced += text.count("{MEASURE_BLOCK}")
            expanded_block = True
        if expanded_block:
            continue
        for placeholder in set(found):
            if placeholder in replacement_map:
                placeholders_replaced += text.count(placeholder)
                if placeholder in block_replacements:
                    paragraphs = block_paragraphs.get(placeholder, [])
                    if len(paragraphs) > 1 and text.strip() == placeholder:
                        paragraph.text = paragraphs[0]
                        current_para = paragraph
                        for block_text in paragraphs[1:]:
                            current_para = _add_paragraph_after(
                                current_para, block_text, style=paragraph.style
                            )
                        expanded_block = True
                        continue
                    joined = " ".join(paragraphs) if paragraphs else replacement_map[placeholder]
                    replaced_text = replaced_text.replace(placeholder, joined)
                else:
                    replaced_text = replaced_text.replace(placeholder, replacement_map[placeholder])
            else:
                unresolved.add(placeholder)
        if expanded_block:
            continue
        if replaced_text != text:
            paragraph.text = replaced_text

    output_dir = os.path.dirname(out_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    doc.save(out_path)

    placeholders_replaced += _replace_placeholders_in_docx_xml(out_path, replacement_map)

    remaining_placeholders = _collect_placeholders_from_docx(out_path)
    unresolved.update(remaining_placeholders)

    summary = {
        "out_path": out_path,
        "placeholders_found": placeholders_found,
        "placeholders_replaced": placeholders_replaced,
        "unresolved": sorted(unresolved),
        "blocks_rendered": blocks_rendered,
        "blocks_unresolved": blocks_unresolved,
    }
    if any(
        ph in ("{MEASURE_BLOCK}", "{MEASURE_SUMMARY_ROW}") for ph in block_placeholders
    ):
        summary["measures_rendered_count"] = measure_narratives.count_selected_measures(
            project_data, catalog=measure_catalog
        )

    if strict and unresolved:
        summary["strict_error"] = True

    return summary
