import json
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class TemplateData:
    measures: Dict[str, dict]
    checklists: Dict[str, dict]
    ui_categories: List[dict]
    category_overrides: Dict[str, str]

    @property
    def category_titles(self) -> Dict[str, str]:
        return {item.get("code", ""): item.get("tab_title", "") for item in self.ui_categories}


def load_template(path: str) -> TemplateData:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Template JSON must be an object.")

    measures = data.get("measures", {})
    if not isinstance(measures, dict):
        raise ValueError("Template JSON measures must be an object.")

    checklists = data.get("checklists", {})
    if checklists is None:
        checklists = {}
    if not isinstance(checklists, dict):
        raise ValueError("Template JSON checklists must be an object.")

    ui_categories = data.get("ui_categories", [])
    if ui_categories is None:
        ui_categories = []
    if not isinstance(ui_categories, list):
        raise ValueError("Template JSON ui_categories must be a list.")

    category_overrides = data.get("category_by_measure_overrides", {})
    if category_overrides is None:
        category_overrides = {}
    if not isinstance(category_overrides, dict):
        raise ValueError("Template JSON category_by_measure_overrides must be an object.")

    return TemplateData(
        measures=measures,
        checklists=checklists,
        ui_categories=ui_categories,
        category_overrides=category_overrides,
    )
