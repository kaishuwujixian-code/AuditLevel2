from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional

from core.paths import REPO_ROOT
from reporting.narratives import coerce_bool, has_meaningful_value, stringify_value


RULESETS_DIR = os.path.join(REPO_ROOT, "reporting", "rulesets")


def load_rulesets(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    rulesets = data.get("rulesets", []) if isinstance(data, dict) else []
    return [ruleset for ruleset in rulesets if isinstance(ruleset, dict)]


def render_ruleset_block(
    project: Dict[str, Any],
    *,
    ruleset_filename: str,
    target_block: str,
    block_ref: Optional[str] = None,
) -> str:
    rulesets = load_rulesets(os.path.join(RULESETS_DIR, ruleset_filename))
    if not rulesets:
        return ""
    matches: List[Dict[str, Any]] = []
    for ruleset in rulesets:
        blocks = ruleset.get("blocks", [])
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_target = str(
                block.get("target_section") or block.get("target_block", "")
            ).strip().lower()
            if block_target != target_block:
                continue
            if block_ref and str(block.get("block_ref")) != block_ref:
                continue
            for rule in block.get("rules", []) or []:
                if not isinstance(rule, dict):
                    continue
                if not _rule_matches(project, rule.get("if")):
                    continue
                if "items" in rule:
                    rendered_items = _render_items(rule, project)
                    if not rendered_items:
                        continue
                    paragraphs = [
                        _format_paragraph(paragraph, project.get("answers", {}))
                        for paragraph in rendered_items
                    ]
                else:
                    paragraphs = [
                        _format_paragraph(paragraph, project.get("answers", {}))
                        for paragraph in _extract_paragraphs(rule)
                    ]
                paragraphs = [paragraph for paragraph in paragraphs if paragraph]
                if not paragraphs:
                    continue
                matches.append(
                    {
                        "target_section": block_target,
                        "role": str(rule.get("role", "")).strip().lower(),
                        "exclusive_group": str(
                            rule.get("exclusive_group") or rule.get("rule_id") or ""
                        ).strip(),
                        "priority": int(rule.get("priority") or 0),
                        "paragraphs": paragraphs,
                    }
                )
    if not matches:
        return ""
    return "\n".join(_render_sections(matches)).strip()


def _render_sections(matches: List[Dict[str, Any]]) -> List[str]:
    sections: Dict[str, List[Dict[str, Any]]] = {}
    for match in matches:
        sections.setdefault(match["target_section"], []).append(match)
    output: List[str] = []
    for section in sections.values():
        selected = _select_exclusive_groups(section)
        headers = [rule for rule in selected if rule["role"] == "system_header"]
        bodies = [rule for rule in selected if rule["role"] != "system_header"]
        if headers:
            headers.sort(key=lambda item: item["priority"], reverse=True)
            output.extend(headers[0]["paragraphs"])
        bodies.sort(key=lambda item: item["priority"], reverse=True)
        for rule in bodies:
            output.extend(rule["paragraphs"])
    return output


def _select_exclusive_groups(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for match in matches:
        group = match.get("exclusive_group") or ""
        grouped.setdefault(group, []).append(match)
    selected: List[Dict[str, Any]] = []
    for group_matches in grouped.values():
        group_matches.sort(key=lambda item: item["priority"], reverse=True)
        selected.append(group_matches[0])
    return selected


def _extract_paragraphs(rule: Dict[str, Any]) -> Iterable[str]:
    payload = rule.get("then", {})
    paragraphs = payload.get("paragraphs", []) if isinstance(payload, dict) else []
    return [paragraph for paragraph in paragraphs if isinstance(paragraph, str)]


def _render_items(rule: Dict[str, Any], project: Dict[str, Any]) -> List[str]:
    items = rule.get("items")
    if not isinstance(items, list):
        return []
    outputs: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if not _rule_matches(project, item.get("if")):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            outputs.append(text.strip())
    if not outputs:
        return []
    if rule.get("role") == "load_item":
        joined = ", ".join(outputs)
        return [f"The boiler plant also serves {joined}."]
    return outputs


def _rule_matches(project: Dict[str, Any], condition: Optional[Dict[str, Any]]) -> bool:
    if not condition:
        return True
    if "all" in condition:
        return all(_evaluate_condition(project, item) for item in condition.get("all", []))
    if "any" in condition:
        return any(_evaluate_condition(project, item) for item in condition.get("any", []))
    return _evaluate_condition(project, condition)


def _evaluate_condition(project: Dict[str, Any], condition: Any) -> bool:
    if not isinstance(condition, dict):
        return False
    field = condition.get("field")
    op = condition.get("op")
    expected = condition.get("value")
    if not field or not op:
        return False
    current = _get_field_value(project, field)
    if op == "exists":
        return has_meaningful_value(current)
    if op == "eq":
        return current == expected
    if op == "ne":
        return current != expected
    if op == "in":
        if isinstance(current, (list, tuple, set)):
            return any(item in (expected or []) for item in current)
        return current in (expected or [])
    if op == "not_in":
        if isinstance(current, (list, tuple, set)):
            return all(item not in (expected or []) for item in current)
        return current not in (expected or [])
    if op == "contains":
        if isinstance(current, (list, tuple, set)):
            return expected in current
        if isinstance(current, str) and isinstance(expected, str):
            return expected in current
        return False
    if op == "not_contains":
        if isinstance(current, (list, tuple, set)):
            return expected not in current
        if isinstance(current, str) and isinstance(expected, str):
            return expected not in current
        return True
    if op == "is_true":
        return coerce_bool(current) is True
    if op == "is_false":
        return coerce_bool(current) is False
    return False


def _get_field_value(project: Dict[str, Any], field: str) -> Any:
    value: Any = project
    for part in field.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def _format_paragraph(text: str, answers: Dict[str, Any]) -> str:
    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in answers:
            value = stringify_value(answers.get(key))
            return value if value is not None else ""
        return ""

    return re.sub(r"{([^{}]+)}", _replace, text).strip()
