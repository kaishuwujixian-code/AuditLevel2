from typing import Callable, Dict, Optional

from reporting.narratives import dhw, heating, measures, misc, ventilation

_BLOCK_RENDERERS: Dict[str, Callable[..., str]] = {}

for module in (heating, dhw, ventilation, measures, misc):
    for placeholder in module.BLOCK_PLACEHOLDERS:
        _BLOCK_RENDERERS.setdefault(placeholder, module.render_block)

_BLOCK_RENDERERS["{MEASURE_SUMMARY_ROW}"] = measures.render_summary_row

KNOWN_BLOCK_PLACEHOLDERS = set(_BLOCK_RENDERERS.keys())


def get_block_renderer(placeholder: str) -> Optional[Callable[..., str]]:
    return _BLOCK_RENDERERS.get(placeholder)
