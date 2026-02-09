from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import messagebox, ttk

from core.paths import REPO_ROOT, SCHEMAS_DIR
from reporting.narratives import load_option_sets


RULESET_DIR = os.path.join(REPO_ROOT, "reporting", "rulesets")
SCHEMA_PATH = os.path.join(SCHEMAS_DIR, "level1_questionnaire.schema.json")


ROLE_OPTIONS = [
    "system_header",
    "plant_support",
    "equipment_detail",
    "loads",
    "performance",
    "condition",
    "finding",
    "operation_notes",
]

OPERATOR_OPTIONS = ["eq", "exists", "in", "is_true", "is_false"]


@dataclass
class Selection:
    ruleset_index: int
    block_index: Optional[int] = None
    rule_index: Optional[int] = None


class RulesetLibraryPanel(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._rulesets: List[Dict[str, Any]] = []
        self._ruleset_files: List[str] = []
        self._selection: Optional[Selection] = None
        self._schema_fields: List[str] = []
        self._field_options: Dict[str, List[str]] = {}
        self._condition_rows: List[Tuple[ttk.Frame, tk.StringVar, tk.StringVar, tk.StringVar, ttk.Combobox, ttk.Entry]] = []
        self._build_schema_fields()
        self._build_ui()
        self._load_rulesets()

    def _build_schema_fields(self) -> None:
        self._schema_fields = []
        self._field_options = {}
        try:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as handle:
                schema = json.load(handle)
        except Exception:
            schema = {}
        option_sets = load_option_sets()
        for section in schema.get("sections", []) if isinstance(schema, dict) else []:
            for question in section.get("questions", []) if isinstance(section, dict) else []:
                if not isinstance(question, dict):
                    continue
                field_id = str(question.get("id", "")).strip()
                if not field_id:
                    continue
                field_name = f"answers.{field_id}"
                self._schema_fields.append(field_name)
                options = question.get("options", []) or []
                if options:
                    values = [str(option.get("value")) for option in options if isinstance(option, dict)]
                    self._field_options[field_name] = [value for value in values if value]
                else:
                    options_ref = question.get("options_ref")
                    if options_ref and options_ref in option_sets:
                        self._field_options[field_name] = list(option_sets[options_ref].keys())
        self._schema_fields.sort()

    def _build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        list_frame = ttk.Frame(self)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(6, 8), pady=6)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(list_frame, show="tree", selectmode="browse")
        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        editor = ttk.Frame(self)
        editor.grid(row=0, column=1, sticky="nsew", padx=(0, 6), pady=6)
        editor.columnconfigure(1, weight=1)

        ttk.Label(editor, text="Level").grid(row=0, column=0, sticky="w", pady=2)
        self._level_var = tk.StringVar(value="")
        ttk.Label(editor, textvariable=self._level_var).grid(row=0, column=1, sticky="w", pady=2)

        ttk.Label(editor, text="Rule ID").grid(row=1, column=0, sticky="w", pady=2)
        self._rule_id_var = tk.StringVar()
        self._rule_id_entry = ttk.Entry(editor, textvariable=self._rule_id_var)
        self._rule_id_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(editor, text="Role").grid(row=2, column=0, sticky="w", pady=2)
        self._role_var = tk.StringVar()
        self._role_combo = ttk.Combobox(
            editor, textvariable=self._role_var, values=ROLE_OPTIONS, state="readonly"
        )
        self._role_combo.grid(row=2, column=1, sticky="ew", pady=2)

        ttk.Label(editor, text="Exclusive group").grid(row=3, column=0, sticky="w", pady=2)
        self._exclusive_group_var = tk.StringVar()
        ttk.Entry(editor, textvariable=self._exclusive_group_var).grid(
            row=3, column=1, sticky="ew", pady=2
        )

        ttk.Label(editor, text="Priority").grid(row=4, column=0, sticky="w", pady=2)
        self._priority_var = tk.StringVar()
        ttk.Entry(editor, textvariable=self._priority_var).grid(
            row=4, column=1, sticky="ew", pady=2
        )

        ttk.Label(editor, text="Target block").grid(row=5, column=0, sticky="w", pady=2)
        self._target_block_var = tk.StringVar()
        self._target_block_combo = ttk.Combobox(editor, textvariable=self._target_block_var)
        self._target_block_combo.grid(row=5, column=1, sticky="ew", pady=2)

        ttk.Label(editor, text="Conditions mode").grid(row=6, column=0, sticky="w", pady=2)
        self._condition_mode = tk.StringVar(value="all")
        self._condition_mode_combo = ttk.Combobox(
            editor, textvariable=self._condition_mode, values=["all", "any"], state="readonly"
        )
        self._condition_mode_combo.grid(row=6, column=1, sticky="w", pady=2)

        ttk.Label(editor, text="Conditions").grid(row=7, column=0, sticky="nw", pady=2)
        self._conditions_frame = ttk.Frame(editor)
        self._conditions_frame.grid(row=7, column=1, sticky="ew", pady=2)
        self._conditions_frame.columnconfigure(0, weight=1)

        ttk.Button(editor, text="Add Condition", command=self._add_condition_row).grid(
            row=8, column=1, sticky="w", pady=(4, 8)
        )

        ttk.Label(editor, text="Narrative text").grid(row=9, column=0, sticky="nw", pady=2)
        self._paragraph_text = tk.Text(editor, height=6, wrap="word")
        self._paragraph_text.grid(row=9, column=1, sticky="ew", pady=2)

        button_row = ttk.Frame(editor)
        button_row.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Button(button_row, text="Apply Changes", command=self._apply_changes).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_row, text="Move Up", command=lambda: self._move_rule(-1)).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(button_row, text="Move Down", command=lambda: self._move_rule(1)).pack(
            side="left", padx=(0, 6)
        )

        action_row = ttk.Frame(editor)
        action_row.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(action_row, text="New Rule", command=self._new_rule).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(action_row, text="Delete", command=self._delete_rule).pack(
            side="left", padx=(0, 6)
        )

        footer = ttk.Frame(editor)
        footer.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(footer, text="Reload", command=self._load_rulesets).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Validate", command=self._validate_rulesets).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(footer, text="Save", command=self._save_rulesets).pack(side="left")

    def _load_rulesets(self) -> None:
        self._rulesets = []
        self._ruleset_files = []
        try:
            files = [
                os.path.join(RULESET_DIR, name)
                for name in os.listdir(RULESET_DIR)
                if name.endswith(".rules.json")
            ]
        except FileNotFoundError:
            files = []
        for path in sorted(files):
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except Exception as exc:
                messagebox.showerror("Ruleset Library", f"Load failed: {exc}")
                continue
            rulesets = data.get("rulesets", []) if isinstance(data, dict) else []
            for ruleset in rulesets:
                if isinstance(ruleset, dict):
                    ruleset["_source_path"] = path
                    self._rulesets.append(ruleset)
                    self._ruleset_files.append(path)
        self._selection = None
        self._refresh_tree()
        self._clear_form()

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        self._tree_index: Dict[str, Selection] = {}
        for r_index, ruleset in enumerate(self._rulesets):
            ruleset_name = ruleset.get("ruleset_name", "Ruleset")
            ruleset_node = self._tree.insert("", "end", text=ruleset_name, open=True)
            self._tree_index[ruleset_node] = Selection(ruleset_index=r_index)
            for b_index, block in enumerate(ruleset.get("blocks", [])):
                block_label = block.get("block_id", "Block")
                block_node = self._tree.insert(ruleset_node, "end", text=block_label, open=True)
                self._tree_index[block_node] = Selection(ruleset_index=r_index, block_index=b_index)
                for rule_index, rule in enumerate(block.get("rules", []) or []):
                    if not isinstance(rule, dict):
                        continue
                    rule_label = rule.get("rule_id", "Rule")
                    rule_node = self._tree.insert(block_node, "end", text=rule_label)
                    self._tree_index[rule_node] = Selection(
                        ruleset_index=r_index, block_index=b_index, rule_index=rule_index
                    )

    def _on_select(self, _event: tk.Event) -> None:
        selection = self._tree.selection()
        if not selection:
            return
        entry = self._tree_index.get(selection[0])
        if not entry:
            return
        self._selection = entry
        if entry.rule_index is not None:
            self._load_rule(entry)
        elif entry.block_index is not None:
            self._load_block(entry)
        else:
            self._clear_form()

    def _load_block(self, entry: Selection) -> None:
        self._clear_form()
        self._level_var.set("Block")
        block = self._rulesets[entry.ruleset_index]["blocks"][entry.block_index]
        self._target_block_var.set(str(block.get("target_block", "")).strip())
        self._rule_id_entry.configure(state="disabled")
        self._role_combo.configure(state="disabled")
        self._condition_mode_combo.configure(state="disabled")

    def _load_rule(self, entry: Selection) -> None:
        self._clear_form()
        self._level_var.set("Rule")
        block = self._rulesets[entry.ruleset_index]["blocks"][entry.block_index]
        rule = block["rules"][entry.rule_index]
        self._rule_id_var.set(str(rule.get("rule_id", "")).strip())
        self._role_var.set(str(rule.get("role", "")).strip())
        self._exclusive_group_var.set(str(rule.get("exclusive_group", "")).strip())
        self._priority_var.set(str(rule.get("priority", "")).strip())
        self._target_block_var.set(str(block.get("target_block", "")).strip())
        self._rule_id_entry.configure(state="normal")
        self._role_combo.configure(state="readonly")
        self._condition_mode_combo.configure(state="readonly")

        condition = rule.get("if", {}) if isinstance(rule, dict) else {}
        if isinstance(condition, dict) and "any" in condition:
            self._condition_mode.set("any")
            conditions = condition.get("any", [])
        else:
            self._condition_mode.set("all")
            conditions = condition.get("all", [])

        for cond in conditions if isinstance(conditions, list) else []:
            if not isinstance(cond, dict):
                continue
            self._add_condition_row(cond)

        paragraphs = rule.get("then", {}).get("paragraphs", []) if isinstance(rule, dict) else []
        if isinstance(paragraphs, list):
            text = "\n\n".join(str(item) for item in paragraphs if item is not None)
        else:
            text = ""
        _set_text(self._paragraph_text, text)

    def _clear_form(self) -> None:
        self._level_var.set("")
        self._rule_id_var.set("")
        self._role_var.set("")
        self._exclusive_group_var.set("")
        self._priority_var.set("")
        self._target_block_var.set("")
        self._condition_mode.set("all")
        self._rule_id_entry.configure(state="disabled")
        self._role_combo.configure(state="disabled")
        self._condition_mode_combo.configure(state="disabled")
        _set_text(self._paragraph_text, "")
        self._clear_condition_rows()

    def _clear_condition_rows(self) -> None:
        for frame, *_ in self._condition_rows:
            frame.destroy()
        self._condition_rows = []

    def _add_condition_row(self, condition: Optional[Dict[str, Any]] = None) -> None:
        frame = ttk.Frame(self._conditions_frame)
        frame.pack(fill="x", pady=2)
        field_var = tk.StringVar(value=str(condition.get("field", "")) if condition else "")
        op_var = tk.StringVar(value=str(condition.get("op", "")) if condition else "eq")
        value_var = tk.StringVar(
            value=str(condition.get("value", "")) if condition else ""
        )
        field_combo = ttk.Combobox(frame, textvariable=field_var, values=self._schema_fields)
        field_combo.pack(side="left", fill="x", expand=True)
        op_combo = ttk.Combobox(
            frame, textvariable=op_var, values=OPERATOR_OPTIONS, width=12, state="readonly"
        )
        op_combo.pack(side="left", padx=(4, 4))
        value_combo = ttk.Combobox(frame, textvariable=value_var, width=22)
        value_combo.pack(side="left", padx=(0, 4))
        delete_btn = ttk.Button(frame, text="X", width=2, command=lambda: self._delete_condition_row(frame))
        delete_btn.pack(side="left")

        def _refresh_value_options(*_args) -> None:
            field = field_var.get().strip()
            op = op_var.get().strip()
            options = self._field_options.get(field, [])
            if options:
                value_combo.configure(values=options, state="readonly")
            else:
                value_combo.configure(values=[], state="normal")
            if op in {"exists", "is_true", "is_false"}:
                value_combo.configure(state="disabled")
                value_var.set("")
            elif op == "in" and options:
                value_combo.configure(state="readonly")

        field_var.trace_add("write", _refresh_value_options)
        op_var.trace_add("write", _refresh_value_options)
        _refresh_value_options()

        self._condition_rows.append((frame, field_var, op_var, value_var, value_combo, field_combo))

    def _delete_condition_row(self, frame: ttk.Frame) -> None:
        for idx, (row_frame, *_rest) in enumerate(self._condition_rows):
            if row_frame == frame:
                row_frame.destroy()
                self._condition_rows.pop(idx)
                return

    def _apply_changes(self) -> None:
        if not self._selection or self._selection.rule_index is None:
            return
        entry = self._selection
        block = self._rulesets[entry.ruleset_index]["blocks"][entry.block_index]
        rule = block["rules"][entry.rule_index]
        rule_id = self._rule_id_var.get().strip()
        if not rule_id:
            messagebox.showerror("Ruleset Library", "Rule ID is required.")
            return
        if self._is_duplicate_rule_id(entry, rule_id):
            messagebox.showerror("Ruleset Library", f"Duplicate rule ID: {rule_id}")
            return
        rule["rule_id"] = rule_id
        rule["role"] = self._role_var.get().strip()
        rule["exclusive_group"] = self._exclusive_group_var.get().strip()
        try:
            rule["priority"] = int(self._priority_var.get().strip() or 0)
        except ValueError:
            messagebox.showerror("Ruleset Library", "Priority must be a number.")
            return

        condition_mode = self._condition_mode.get().strip() or "all"
        conditions: List[Dict[str, Any]] = []
        for _frame, field_var, op_var, value_var, *_rest in self._condition_rows:
            field = field_var.get().strip()
            op = op_var.get().strip()
            value = value_var.get().strip()
            if not field or not op:
                continue
            cond: Dict[str, Any] = {"field": field, "op": op}
            if op not in {"exists", "is_true", "is_false"}:
                if op == "in":
                    cond["value"] = [item.strip() for item in value.split(",") if item.strip()]
                else:
                    cond["value"] = value
            conditions.append(cond)
        rule["if"] = {condition_mode: conditions} if conditions else {}

        paragraphs_raw = _get_text(self._paragraph_text)
        paragraphs = [p.strip() for p in paragraphs_raw.split("\n\n") if p.strip()]
        rule["then"] = {"paragraphs": paragraphs}
        self._refresh_tree()

    def _is_duplicate_rule_id(self, entry: Selection, rule_id: str) -> bool:
        for r_index, ruleset in enumerate(self._rulesets):
            for b_index, block in enumerate(ruleset.get("blocks", [])):
                for rule_index, rule in enumerate(block.get("rules", []) or []):
                    if not isinstance(rule, dict):
                        continue
                    if r_index == entry.ruleset_index and b_index == entry.block_index and rule_index == entry.rule_index:
                        continue
                    if rule.get("rule_id") == rule_id:
                        return True
        return False

    def _new_rule(self) -> None:
        if not self._selection or self._selection.block_index is None:
            messagebox.showinfo("Ruleset Library", "Select a block to add a rule.")
            return
        entry = self._selection
        block = self._rulesets[entry.ruleset_index]["blocks"][entry.block_index]
        block.setdefault("rules", []).append(
            {
                "rule_id": "new_rule",
                "if": {},
                "then": {"paragraphs": []},
                "role": "",
                "exclusive_group": "",
                "priority": 0,
            }
        )
        self._refresh_tree()

    def _delete_rule(self) -> None:
        if not self._selection or self._selection.rule_index is None:
            return
        entry = self._selection
        block = self._rulesets[entry.ruleset_index]["blocks"][entry.block_index]
        if not messagebox.askyesno("Ruleset Library", "Delete this rule?"):
            return
        block["rules"].pop(entry.rule_index)
        self._selection = None
        self._refresh_tree()
        self._clear_form()

    def _move_rule(self, direction: int) -> None:
        if not self._selection or self._selection.rule_index is None:
            return
        entry = self._selection
        block = self._rulesets[entry.ruleset_index]["blocks"][entry.block_index]
        rules = block.get("rules", [])
        idx = entry.rule_index
        new_index = idx + direction
        if new_index < 0 or new_index >= len(rules):
            return
        rules[idx], rules[new_index] = rules[new_index], rules[idx]
        entry.rule_index = new_index
        self._refresh_tree()

    def _validate_rulesets(self) -> None:
        errors = []
        seen_ids = set()
        for ruleset in self._rulesets:
            for block in ruleset.get("blocks", []):
                for rule in block.get("rules", []) or []:
                    if not isinstance(rule, dict):
                        continue
                    rule_id = str(rule.get("rule_id", "")).strip()
                    if not rule_id:
                        errors.append("Rule without rule_id found.")
                    elif rule_id in seen_ids:
                        errors.append(f"Duplicate rule_id: {rule_id}")
                    else:
                        seen_ids.add(rule_id)
                    if not rule.get("then", {}).get("paragraphs"):
                        errors.append(f"Rule '{rule_id}' has no narrative text.")
                    condition = rule.get("if", {})
                    if not condition:
                        errors.append(f"Rule '{rule_id}' has no conditions.")
                    for key in ("all", "any"):
                        for cond in condition.get(key, []) if isinstance(condition, dict) else []:
                            field = cond.get("field")
                            if field and field not in self._schema_fields:
                                errors.append(f"Rule '{rule_id}' uses unknown field: {field}")
        if errors:
            messagebox.showerror("Ruleset Library", "\n".join(errors))
        else:
            messagebox.showinfo("Ruleset Library", "Ruleset validation passed.")

    def _save_rulesets(self) -> None:
        self._apply_changes()
        grouped: Dict[str, Dict[str, Any]] = {}
        for ruleset in self._rulesets:
            path = ruleset.get("_source_path")
            if not path:
                continue
            grouped.setdefault(path, {"rulesets": []})["rulesets"].append(
                {k: v for k, v in ruleset.items() if k != "_source_path"}
            )
        try:
            for path, payload in grouped.items():
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, indent=2, ensure_ascii=False)
                    handle.write("\n")
        except Exception as exc:
            messagebox.showerror("Ruleset Library", f"Save failed: {exc}")
            return
        messagebox.showinfo("Ruleset Library", "Rulesets saved successfully.")


def _set_text(widget: tk.Text, value: Any) -> None:
    widget.delete("1.0", tk.END)
    if value is None:
        return
    widget.insert("1.0", str(value))


def _get_text(widget: tk.Text) -> str:
    return widget.get("1.0", "end-1c")
