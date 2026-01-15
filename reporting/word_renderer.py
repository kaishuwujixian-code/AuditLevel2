import json
import os
import re
import zipfile
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from docx import Document


PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}")
DEFAULT_MAPPING_PATH = os.path.join("schemas", "level1_placeholders.map.json")
DEFAULT_OPTION_SETS_PATH = os.path.join("schemas", "level1_questionnaire.mapping.json")
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


def _is_block_placeholder(placeholder: str) -> bool:
    if not placeholder.startswith("{") or not placeholder.endswith("}"):
        return False
    inner_text = placeholder[1:-1].strip()
    return inner_text.endswith(" block") or inner_text.endswith("_BLOCK")


@lru_cache(maxsize=1)
def _load_option_sets(
    mapping_path: Optional[str] = DEFAULT_OPTION_SETS_PATH,
) -> Dict[str, Dict[str, str]]:
    if mapping_path is None or not os.path.isfile(mapping_path):
        return {}
    with open(mapping_path, "r", encoding="utf-8") as handle:
        mapping_data = json.load(handle)
    option_sets = mapping_data.get("option_sets", {})
    if not isinstance(option_sets, dict):
        return {}
    formatted: Dict[str, Dict[str, str]] = {}
    for set_name, options in option_sets.items():
        if not isinstance(options, list):
            continue
        formatted[set_name] = {
            str(option.get("value")): str(option.get("label"))
            for option in options
            if isinstance(option, dict)
        }
    return formatted


def _humanize_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.replace("_", " ").replace("-", " ").strip()
    return str(value)


def _format_option_values(option_set: str, value: Any) -> List[str]:
    option_sets = _load_option_sets()
    mapping = option_sets.get(option_set, {})
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        values = value
    else:
        values = [value]
    labels = []
    for item in values:
        if isinstance(item, str):
            labels.append(mapping.get(item, _humanize_value(item)))
        else:
            labels.append(_humanize_value(item))
    return [label for label in labels if label]


def _human_join(values: List[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return ", ".join(values[:-1]) + f", and {values[-1]}"


def _ensure_sentence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?":
        return f"{cleaned}."
    return cleaned


def _get_answer_value(
    project_data: Dict[str, Any],
    keys: Iterable[str],
    section: Optional[str] = None,
) -> Any:
    answers = project_data.get("answers", {})
    if isinstance(answers, dict):
        for key in keys:
            if key in answers:
                return answers[key]
    if section:
        systems = project_data.get("building_systems", {})
        if isinstance(systems, dict):
            section_data = systems.get(section, {})
            if isinstance(section_data, dict):
                for key in keys:
                    if key in section_data:
                        return section_data[key]
    return None


def render_heating_block(project_data: Dict[str, Any]) -> str:
    system_type_values = _format_option_values(
        "hvac.heating_system_type",
        _get_answer_value(
            project_data,
            ["hvac.heating_system_type", "heating_system_type", "system_type"],
            section="heating",
        ),
    )
    serves_values = _format_option_values(
        "hvac.heating_serves",
        _get_answer_value(
            project_data,
            ["hvac.heating_serves", "heating_serves", "serves"],
            section="heating",
        ),
    )
    notes_value = _get_answer_value(
        project_data,
        ["heating_notes", "heating_block", "notes"],
        section="heating",
    )

    sentences: List[str] = []
    if system_type_values:
        system_type = _human_join(system_type_values)
        sentences.append(f"The building is served by a {system_type} heating system.")
    if serves_values:
        serves = _human_join(serves_values)
        sentences.append(f"The system provides space heating to {serves}.")
    notes_text = _stringify_value(notes_value)
    if notes_text:
        sentences.append(_ensure_sentence(notes_text))

    if not sentences:
        return DEFAULT_EMPTY_BLOCK_TEXT
    return " ".join(sentences)


def render_dhw_block(project_data: Dict[str, Any]) -> str:
    system_type_values = _format_option_values(
        "dhw.system_type",
        _get_answer_value(
            project_data,
            ["dhw.system_type", "dhw_system_type", "system_type"],
            section="dhw",
        ),
    )
    heat_source_value = _get_answer_value(
        project_data,
        ["dhw_heat_source", "heat_source", "dhw_source"],
        section="dhw",
    )
    storage_notes_value = _get_answer_value(
        project_data,
        ["dhw_storage_notes", "dhw_distribution_notes", "dhw_notes", "notes", "dhw_block"],
        section="dhw",
    )

    sentences: List[str] = []
    if system_type_values:
        system_type = _human_join(system_type_values)
        sentences.append(f"Domestic hot water is provided by {system_type}.")
    heat_source_text = _stringify_value(heat_source_value)
    if heat_source_text:
        sentences.append(f"The heat source is {heat_source_text}.")
    storage_notes_text = _stringify_value(storage_notes_value)
    if storage_notes_text:
        sentences.append(_ensure_sentence(storage_notes_text))

    if not sentences:
        return DEFAULT_EMPTY_BLOCK_TEXT
    return " ".join(sentences)


def render_measures_block(project_data: Dict[str, Any]) -> str:
    measures: List[str] = []
    selected_measures = project_data.get("selected_measures")
    if isinstance(selected_measures, list):
        measures = [str(item).strip() for item in selected_measures if str(item).strip()]
    if not measures:
        answers = project_data.get("answers", {})
        if isinstance(answers, dict):
            answer_measures = answers.get("selected_measures") or answers.get("measures")
            if isinstance(answer_measures, list):
                measures = [str(item).strip() for item in answer_measures if str(item).strip()]
            elif isinstance(answer_measures, str):
                measures = [
                    item.strip()
                    for item in re.split(r"[\n,]+", answer_measures)
                    if item.strip()
                ]

    if not measures:
        return DEFAULT_EMPTY_BLOCK_TEXT

    sentences = [f"({idx}) {measure}." for idx, measure in enumerate(measures, start=1)]
    return (
        "The following energy conservation measures were identified during the walkthrough: "
        + " ".join(sentences)
    )


BLOCK_RENDERERS = {
    "Central Heating/Cooling Systems block": render_heating_block,
    "DHW System Block": render_dhw_block,
    "MEASURE_BLOCK": render_measures_block,
}


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
    if "placeholders" in project_data and isinstance(project_placeholders, dict):
        placeholder_map = _build_placeholder_map_from_placeholders(project_placeholders)
    else:
        answers = project_data.get("answers", {})
        if not isinstance(answers, dict):
            raise ValueError("project['answers'] must be a JSON object.")
        placeholder_map = _build_placeholder_map_from_answers(
            answers, placeholder_set, mapping_path
        )

    block_placeholders = [ph for ph in placeholder_occurrences if _is_block_placeholder(ph)]
    placeholder_map = {
        placeholder: value
        for placeholder, value in placeholder_map.items()
        if not _is_block_placeholder(placeholder)
    }

    blocks_rendered: List[str] = []
    block_replacements: Dict[str, str] = {}
    for placeholder in block_placeholders:
        inner_text = placeholder[1:-1].strip()
        renderer = BLOCK_RENDERERS.get(inner_text)
        if not renderer:
            continue
        rendered_text = renderer(project_data)
        if rendered_text is None:
            rendered_text = DEFAULT_EMPTY_BLOCK_TEXT
        block_replacements[placeholder] = rendered_text
        blocks_rendered.append(placeholder)

    replacement_map = {**placeholder_map, **block_replacements}

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
        for placeholder in set(found):
            if placeholder in replacement_map:
                placeholders_replaced += text.count(placeholder)
                replaced_text = replaced_text.replace(placeholder, replacement_map[placeholder])
            else:
                unresolved.add(placeholder)
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
    }

    if strict and unresolved:
        summary["strict_error"] = True

    return summary
