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
DEFAULT_MEASURE_CATALOG_PATH = os.path.join("templates", "template.level1.json")

PROVINCE_ABBREVIATIONS = {
    "alberta": "AB",
    "british columbia": "BC",
    "manitoba": "MB",
    "new brunswick": "NB",
    "newfoundland and labrador": "NL",
    "nova scotia": "NS",
    "northwest territories": "NT",
    "nunavut": "NU",
    "ontario": "ON",
    "prince edward island": "PE",
    "quebec": "QC",
    "saskatchewan": "SK",
    "yukon": "YT",
}

DISTRIBUTION_OVERRIDES = {
    "serves_wshp": "water-source heat pump units",
    "serves_fancoil": "fan coil units",
    "serves_radiant": "radiant distribution",
    "serves_ahu": "air handling units (AHUs)",
    "serves_mua": "make-up air units (MUAs)",
    "mixed_unknown": "mixed distribution systems",
}


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


def _format_distribution_values(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        values = value
    else:
        values = [value]
    labels: List[str] = []
    mapping = _load_option_sets().get("hvac.heating_serves", {})
    for item in values:
        if isinstance(item, str) and item in DISTRIBUTION_OVERRIDES:
            labels.append(DISTRIBUTION_OVERRIDES[item])
        elif isinstance(item, str):
            label = mapping.get(item, _humanize_value(item))
            if label.lower().startswith("serves "):
                label = label[7:]
            labels.append(label.strip())
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


def _contains_unknown(values: List[str]) -> bool:
    return any("unknown" in value.lower() for value in values)


def _is_unknown_selection(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple)):
        values = value
    else:
        values = [value]
    for item in values:
        if isinstance(item, str) and "unknown" in item.lower():
            return True
    return False


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
    system_type_raw = _get_answer_value(
        project_data,
        ["hvac.heating_system_type", "heating_system_type", "system_type"],
        section="heating",
    )
    system_type_values = _format_option_values("hvac.heating_system_type", system_type_raw)
    distribution_raw = _get_answer_value(
        project_data,
        ["hvac.heating_serves", "heating_serves", "serves"],
        section="heating",
    )
    serves_values = _format_distribution_values(distribution_raw)
    notes_value = _get_answer_value(
        project_data,
        ["heating_notes", "heating_block", "notes"],
        section="heating",
    )

    sentences: List[str] = []
    system_unknown = (
        not system_type_values
        or _contains_unknown(system_type_values)
        or _is_unknown_selection(system_type_raw)
    )
    distribution_unknown = (
        not serves_values
        or _contains_unknown(serves_values)
        or _is_unknown_selection(distribution_raw)
    )

    if not system_unknown:
        system_type = _human_join(system_type_values)
        sentences.append(f"The building is served by a {system_type} heating plant.")
    else:
        sentences.append("The heating plant type was not confirmed at the time of the site visit.")

    if not distribution_unknown:
        serves = _human_join(serves_values)
        sentences.append(f"Heat is distributed through {serves}.")
    else:
        sentences.append(
            "The heating distribution system was not confirmed at the time of the site visit."
        )

    sentences.append(
        "Additional details on equipment condition and control sequences were not confirmed at the time of the site visit."
    )

    notes_text = _stringify_value(notes_value)
    if notes_text and notes_text.strip():
        sentences.append(_ensure_sentence(notes_text))

    return " ".join(sentences[:6])


def render_dhw_block(project_data: Dict[str, Any]) -> str:
    system_type_raw = _get_answer_value(
        project_data,
        ["dhw.system_type", "dhw_system_type", "system_type"],
        section="dhw",
    )
    system_type_values = _format_option_values("dhw.system_type", system_type_raw)
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
    recirc_value = _get_answer_value(
        project_data,
        [
            "dhw_recirc",
            "dhw_recirculation",
            "dhw_circulation",
            "dhw_recirc_pumps",
            "dhw_circulation_pumps",
            "dhw_pumps",
        ],
        section="dhw",
    )

    sentences: List[str] = []
    system_unknown = (
        not system_type_values
        or _contains_unknown(system_type_values)
        or _is_unknown_selection(system_type_raw)
    )

    if not system_unknown:
        system_type = _human_join(system_type_values)
        sentences.append(f"Domestic hot water is provided by {system_type}.")
    else:
        sentences.append(
            "The domestic hot water plant type was not confirmed at the time of the site visit."
        )
    heat_source_text = _stringify_value(heat_source_value)
    if heat_source_text and heat_source_text.strip():
        sentences.append(f"The heat source is {heat_source_text}.")
    if isinstance(recirc_value, bool):
        if recirc_value:
            sentences.append("A recirculation loop with circulation pumps was observed.")
        else:
            sentences.append("No domestic hot water recirculation loop was observed.")
    elif _has_meaningful_value(recirc_value):
        sentences.append(_ensure_sentence(str(recirc_value)))
    storage_notes_text = _stringify_value(storage_notes_value)
    if storage_notes_text and storage_notes_text.strip():
        sentences.append(_ensure_sentence(storage_notes_text))

    if len(sentences) < 3:
        sentences.append(
            "Additional domestic hot water distribution details should be confirmed during detailed review."
        )

    return " ".join(sentences[:5])


def render_measures_block(project_data: Dict[str, Any]) -> str:
    measures: List[Any] = []
    selected_measures = project_data.get("selected_measures")
    if isinstance(selected_measures, list):
        measures = [item for item in selected_measures if _has_meaningful_value(item)]
    if not measures:
        answers = project_data.get("answers", {})
        if isinstance(answers, dict):
            answer_measures = answers.get("selected_measures") or answers.get("measures")
            if isinstance(answer_measures, list):
                measures = [item for item in answer_measures if _has_meaningful_value(item)]
            elif isinstance(answer_measures, str):
                measures = [
                    item.strip() for item in re.split(r"[\n,]+", answer_measures) if item.strip()
                ]

    if not measures:
        return "No measures were selected."

    catalog = _load_measure_catalog()
    lines = []
    for measure in measures:
        title, justification = _split_measure_entry(measure, catalog)
        lines.append(f"• {title} — {justification}")

    return "\n".join(lines)


@lru_cache(maxsize=1)
def _load_measure_catalog(
    catalog_path: str = DEFAULT_MEASURE_CATALOG_PATH,
) -> Dict[str, Dict[str, str]]:
    if not catalog_path or not os.path.isfile(catalog_path):
        return {}
    with open(catalog_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    measures = data.get("measures", {}) if isinstance(data, dict) else {}
    if not isinstance(measures, dict):
        return {}
    catalog: Dict[str, Dict[str, str]] = {}
    for key, entry in measures.items():
        if isinstance(entry, dict):
            summary = entry.get("summary") or ""
            retrofit = entry.get("retrofit") or ""
            catalog[str(key)] = {"summary": str(summary), "retrofit": str(retrofit)}
    return catalog


def _extract_first_sentence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    match = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)
    return match[0].strip()


def _split_measure_entry(
    measure: Any, catalog: Dict[str, Dict[str, str]]
) -> Tuple[str, str]:
    if isinstance(measure, dict):
        title = str(measure.get("title") or measure.get("name") or "").strip()
        justification = str(
            measure.get("justification") or measure.get("summary") or measure.get("notes") or ""
        ).strip()
    else:
        title = str(measure).strip()
        justification = ""

    if title in catalog and not justification:
        summary = catalog[title].get("summary", "")
        justification = summary.strip()
        if not justification:
            retrofit = catalog[title].get("retrofit", "")
            justification = _extract_first_sentence(retrofit)

    if not justification:
        justification = "Justification not provided."

    return title or "Untitled measure", justification


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


def _apply_facility_placeholders(
    answers: Dict[str, Any], placeholder_map: Dict[str, str]
) -> None:
    if not answers:
        return

    def set_if_missing(placeholder: str, value: Any) -> None:
        if not _has_meaningful_value(value):
            return
        existing = placeholder_map.get(placeholder, "")
        if not existing.strip():
            placeholder_map[placeholder] = _stringify_value(value) or ""

    set_if_missing("{Property Address1}", answers.get("site_address"))

    district_value = answers.get("district") or answers.get("city")
    set_if_missing("{District}", district_value)

    set_if_missing("{Province}", answers.get("province"))

    province_abbreviation = answers.get("province_abbreviation")
    if not _has_meaningful_value(province_abbreviation):
        province = answers.get("province")
        if isinstance(province, str):
            province_abbreviation = PROVINCE_ABBREVIATIONS.get(province.strip().lower())
    set_if_missing("{Province Abbreviation}", province_abbreviation)

    set_if_missing("{Number of Floors}", answers.get("number_of_floors"))
    set_if_missing("{Number of Suites}", answers.get("number_of_suites"))

    arch_condition_value = answers.get("architectural_condition")
    if _has_meaningful_value(arch_condition_value):
        labels = _format_option_values("building.arch_condition", arch_condition_value)
        if labels and not _contains_unknown(labels):
            set_if_missing("{Architectural Condition}", _human_join(labels))
        else:
            set_if_missing("{Architectural Condition}", arch_condition_value)


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
    answers = project_data.get("answers", {})
    if "placeholders" in project_data and isinstance(project_placeholders, dict):
        placeholder_map = _build_placeholder_map_from_placeholders(project_placeholders)
        if isinstance(answers, dict):
            _apply_facility_placeholders(answers, placeholder_map)
    else:
        if not isinstance(answers, dict):
            raise ValueError("project['answers'] must be a JSON object.")
        placeholder_map = _build_placeholder_map_from_answers(
            answers, placeholder_set, mapping_path
        )
        _apply_facility_placeholders(answers, placeholder_map)

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
