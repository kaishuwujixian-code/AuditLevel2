from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_UI_STATE_PATH = Path.home() / ".audit_studio_ui_state.json"


def _load_all() -> Dict[str, Any]:
    if not _UI_STATE_PATH.is_file():
        return {}
    try:
        data = json.loads(_UI_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_ui_state(key: str) -> Dict[str, Any]:
    data = _load_all()
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def save_ui_state(key: str, value: Dict[str, Any]) -> None:
    data = _load_all()
    data[key] = value
    _UI_STATE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
