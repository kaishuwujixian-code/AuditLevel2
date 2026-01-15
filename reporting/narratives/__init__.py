import json
import os
import re
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_OPTION_SETS_PATH = os.path.join("schemas", "level1_questionnaire.mapping.json")

DISTRIBUTION_OVERRIDES = {
    "serves_wshp": "water-source heat pump units",
    "serves_fancoil": "fan coil units",
    "serves_radiant": "radiant distribution",
    "serves_ahu": "air handling units (AHUs)",
    "serves_mua": "make-up air units (MUAs)",
    "mixed_unknown": "mixed distribution systems",
}


def stringify_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)


def has_meaningful_value(value: Any) -> bool:
    string_value = stringify_value(value)
    return string_value is not None and bool(string_value.strip())


@lru_cache(maxsize=1)
def _load_option_sets_from_path(
    mapping_path: Optional[str] = DEFAULT_OPTION_SETS_PATH,
) -> Dict[str, Dict[str, str]]:
    if mapping_path is None or not os.path.isfile(mapping_path):
        return {}
    with open(mapping_path, "r", encoding="utf-8") as handle:
        mapping_data = json.load(handle)
    return _coerce_option_sets(mapping_data)


def _coerce_option_sets(mapping_data: Any) -> Dict[str, Dict[str, str]]:
    option_sets = mapping_data.get("option_sets", {}) if isinstance(mapping_data, dict) else {}
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


def load_option_sets(mapping: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, str]]:
    if mapping is not None:
        return _coerce_option_sets(mapping)
    return _load_option_sets_from_path()


def humanize_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.replace("_", " ").replace("-", " ").strip()
    return str(value)


def format_option_values(
    option_set: str, value: Any, mapping: Optional[Dict[str, Any]] = None
) -> List[str]:
    option_sets = load_option_sets(mapping)
    selection = option_sets.get(option_set, {})
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        values = value
    else:
        values = [value]
    labels = []
    for item in values:
        if isinstance(item, str):
            labels.append(selection.get(item, humanize_value(item)))
        else:
            labels.append(humanize_value(item))
    return [label for label in labels if label]


def format_distribution_values(
    value: Any, mapping: Optional[Dict[str, Any]] = None
) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        values = value
    else:
        values = [value]
    labels: List[str] = []
    selection = load_option_sets(mapping).get("hvac.heating_serves", {})
    for item in values:
        if isinstance(item, str) and item in DISTRIBUTION_OVERRIDES:
            labels.append(DISTRIBUTION_OVERRIDES[item])
        elif isinstance(item, str):
            label = selection.get(item, humanize_value(item))
            if label.lower().startswith("serves "):
                label = label[7:]
            labels.append(label.strip())
        else:
            labels.append(humanize_value(item))
    return [label for label in labels if label]


def human_join(values: List[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return ", ".join(values[:-1]) + f", and {values[-1]}"


def ensure_sentence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?":
        return f"{cleaned}."
    return cleaned


def uncertainty_sentence(reason: str) -> str:
    return ensure_sentence(f"Based on available information, {reason}")


def not_confirmed_sentence(item: str) -> str:
    return ensure_sentence(f"{item} was not confirmed at the time of the site visit")


def further_investigation_sentence(scope: str) -> str:
    return ensure_sentence(f"Further investigation is recommended to confirm {scope}")


def contains_unknown(values: List[str]) -> bool:
    return any("unknown" in value.lower() for value in values)


def is_unknown_selection(value: Any) -> bool:
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


def get_answer_value(
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


def first_meaningful_text(values: Iterable[Any]) -> Optional[str]:
    for value in values:
        if has_meaningful_value(value):
            text = stringify_value(value)
            if text and text.strip():
                return text.strip()
    return None


def extract_first_sentence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    match = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)
    return match[0].strip()
