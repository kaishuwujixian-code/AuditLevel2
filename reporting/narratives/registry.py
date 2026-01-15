from typing import Any, Callable, Dict, Optional

from reporting.narratives import dhw, findings, heating, measures, misc, ventilation

_BLOCK_RENDERERS: Dict[str, Callable[..., str]] = {}
_BLOCK_EXPECTATIONS: Dict[str, Dict[str, Any]] = {}

for module in (heating, dhw, ventilation, measures, misc, findings):
    for placeholder in module.BLOCK_PLACEHOLDERS:
        _BLOCK_RENDERERS.setdefault(placeholder, module.render_block)
    module_expectations = getattr(module, "EXPECTED_INPUTS", {})
    if isinstance(module_expectations, dict):
        for placeholder, details in module_expectations.items():
            if isinstance(details, dict):
                _BLOCK_EXPECTATIONS.setdefault(placeholder, details)

_BLOCK_RENDERERS["{MEASURE_SUMMARY_ROW}"] = measures.render_summary_row

KNOWN_BLOCK_PLACEHOLDERS = set(_BLOCK_RENDERERS.keys())


def get_block_renderer(placeholder: str) -> Optional[Callable[..., str]]:
    return _BLOCK_RENDERERS.get(placeholder)


def list_blocks() -> list[str]:
    return sorted(KNOWN_BLOCK_PLACEHOLDERS)


def describe_expected_inputs(placeholder: str) -> Dict[str, Any]:
    return dict(_BLOCK_EXPECTATIONS.get(placeholder, {}))
