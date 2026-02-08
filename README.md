# report-generator

## Quick Start

### Run the unified desktop app (supported)
```bash
python app_retscreen.py
```

### Generate a Level 1 report (CLI, supported)
```bash
python -m tools.render_level1 --template templates/level1.docx --project projects/<slug>/project.json --out output/<slug>_level1.docx
```

### Level 1 workflow (schema → UI → project.json → Word)
1. Ensure the schema and option sets are up to date:
   ```bash
   python -m tools.generate_questionnaire_schema --placeholders schemas/placeholders.level1.json --mapping schemas/level1_questionnaire.mapping.json --out schemas/level1_questionnaire.schema.json
   ```
2. Run the desktop UI and save a project:
   ```bash
   python app_retscreen.py
   ```
3. Render the Word report from the saved project:
   ```bash
   python -m tools.render_level1 --template templates/level1.docx --project projects/<slug>/project.json --out output/<slug>_level1_rendered.docx
   ```

### Commit 1 - Extract placeholders
Extract placeholders from the single source of truth Word template:
```bash
python -m tools.extract_placeholders --template templates/level1.docx --out schemas/placeholders.level1.json
```

If `--out` is omitted, JSON is printed to stdout.

### Questionnaire Schema
Regenerate the schema from the Word template:
```bash
python -m tools.generate_questionnaire_schema --placeholders schemas/placeholders.level1.json --mapping schemas/level1_questionnaire.mapping.json --out schemas/level1_questionnaire.schema.json
```

Validate the generated schema:
```bash
python -m tools.validate_questionnaire_schema --schema schemas/level1_questionnaire.schema.json --placeholders schemas/placeholders.level1.json --mapping schemas/level1_questionnaire.mapping.json
```

### Narrative blocks + facility placeholders
The Word renderer now expands HVAC/DHW/Measures blocks into short narrative paragraphs and auto-fills key
facility placeholders from `answers` (even when `placeholders` is present but empty).
Narrative generation logic now lives under `reporting/narratives/` for reuse across renderers.
Narrative modules now include consultant-grade conditional language and
uncertainty handling to reflect available information while keeping a
consistent professional tone.

Minimal `project.json` example that produces HVAC/DHW/ventilation narrative blocks:
```json
{
  "answers": {
    "site_address": "45 Charles St E",
    "district": "Yorkville",
    "province": "Ontario",
    "province_abbreviation": "ON",
    "number_of_floors": "12",
    "number_of_suites": "180",
    "architectural_condition": "fair",
    "heating_system_type": "condensing_boiler",
    "heating_serves": ["serves_fancoil", "serves_ahu"],
    "number_of_boilers": 2,
    "boiler_capacity_mbh": 2500,
    "cooling_system_type": "chiller_cooling_tower",
    "number_of_chillers": 1,
    "chiller_tonnage": 300,
    "number_of_fluid_coolers": 1,
    "heating_notes": "Boilers were observed in the central plant; controls require verification.",
    "dhw_system_type": "dhw_boiler_condensing",
    "number_of_dhw_boilers": 2,
    "dhw_boiler_capacity_mbh": 500,
    "number_of_dhw_tanks": 1,
    "dhw_tank_capacity_gal": 1000,
    "dhw_recirc": true,
    "dhw_notes": "DHW storage tank observed in the main mechanical room.",
    "ventilation_system_type": "mua_gas_rooftop",
    "number_of_mua_units": 2,
    "ventilation_airflow_cfm": 12000
  },
  "selected_measures": ["BAS Upgrade", "Condensing Boiler Retrofit"]
}
```

Manual test command:
```bash
python -m tools.render_level1 --template templates/level1.docx --project projects/project.json --out output/level1_rendered.docx
```

Expected output:
* `{Central Heating Systems block}` and `{Central Cooling Systems block}` render 3–6 sentence paragraphs (not a single word).
* `{DHW System Block}` and `{Central Ventilation System Block}` render narrative blocks based on system selections.
* `{Number of Floors}`, `{Number of Suites}`, `{Architectural Condition}` are filled when provided under `answers`.

### Example smoke test
Generate a sample report from `projects/example.json`:
```bash
python -m tools.render_level1 --template templates/level1.docx --project projects/example.json --out outputs/level1_rendered.docx
```
The renderer prints a summary with replaced/unresolved placeholder counts; use `--strict` to fail if any remain.

### Desktop App Smoke-Test Checklist
1. Run `python app_retscreen.py` and confirm the window opens.
2. Open or create a project, enter facility/system answers, select measures, and choose checklist findings.
3. Save and confirm it writes to `projects/<slug>/project.json`.
4. Re-open the same file and confirm fields load.
5. Edit a field and Save, confirm the JSON updates and unknown keys remain.
6. Validate Project (expect OK or warnings dialog).
7. Generate Level 1 and confirm output in `output/`.

### Deprecated entry points
These are kept only for backward compatibility. Prefer the supported commands above.

* Legacy questionnaire builder (deprecated):
  ```bash
  python app.py
  ```
  Replacement: `python app_retscreen.py`
* Legacy CLI (deprecated):
  ```bash
  python main.py --project projects/<slug>/project.json --template templates/template.level1.json --docx-template templates/level1.docx --out output/<slug>_level1.docx
  ```
  Replacement: `python -m tools.render_level1 --template templates/level1.docx --project projects/<slug>/project.json --out output/<slug>_level1.docx`
* Removed legacy UI modules: `ui/main_window.py`, `ui/project_browser.py`, and `tools/new_project.py`.

## Walkthrough Findings (Checklist)

Add optional checklist selections in `project.json`:
```json
{
  "checklist_selections": {
    "Walkthrough Findings": {
      "Safety Hazards": [
        "No storage in boiler room"
      ],
      "Opportunities": [
        "Hydronic balancing review"
      ]
    }
  }
}
```

In the Word template, place the placeholder where findings should appear:
```
{FINDINGS_BLOCK}
```

## On-Site Quick Workflow

Create a project file interactively:
```bash
python -m tools.site_wizard --new
```
Use flags like `--template`, `--out`, `--no-measures`, or `--no-checklists` to customize the prompt flow.

Clone an existing project file:
```bash
python -m tools.site_wizard --clone projects/2255_victoria_park/project.json
```

Reuse selections from an existing project file:
```bash
python -m tools.site_wizard --reuse projects/2255_victoria_park/project.json
```

Non-interactive example:
```bash
python -m tools.site_wizard --new --non-interactive --set project_info.client_name="ABC" --set project_info.site_address="123 Main" --set project_info.report_date="2026-01-13" --out projects/abc_123/project.json
```

Generate a report from the new project:
```bash
python -m tools.render_level1 --template templates/level1.docx --project projects/<slug>/project.json --out output/<slug>_level1.docx
```

## Smoke tests
* UI launches (no import errors):
  ```bash
  python app_retscreen.py
  ```
* Measures rendering smoke test (create a project with 2 measures via the UI first):
  ```bash
  python -m tools.render_level1 --template templates/level1.docx --project projects/<slug>/project.json --out output/<slug>_level1.docx
  ```
  Verify the measures appear as a numbered list with consistent fonts and include the "Existing Conditions" / "Retrofit Conditions" subtitles.
* CLI renders a docx:
  ```bash
  python -m tools.render_level1 --template templates/level1.docx --project projects/<slug>/project.json --out output/<slug>_level1.docx
  ```
* Schema tools run:
  ```bash
  python -m tools.generate_questionnaire_schema --placeholders schemas/placeholders.level1.json --mapping schemas/level1_questionnaire.mapping.json --out schemas/level1_questionnaire.schema.json
  python -m tools.validate_questionnaire_schema --schema schemas/level1_questionnaire.schema.json --placeholders schemas/placeholders.level1.json --mapping schemas/level1_questionnaire.mapping.json
  ```
* site_wizard creates project.json:
  ```bash
  python -m tools.site_wizard --new
  ```
