# report-generator

## Quick Start

### Run the unified desktop app
```bash
python app_retscreen.py
```

### Generate a Level 1 report (CLI)
```bash
python tools/render_level1.py --template templates/level1.docx --project projects/<slug>/project.json --out output/<slug>_level1.docx
```

### Validate project inputs (CLI)
```bash
python main.py --project projects/<slug>/project.json --template templates/template.level1.json --docx-template templates/level1.docx --validate
```

### Commit 1 - Extract placeholders
Extract placeholders from the single source of truth Word template:
```bash
python tools/extract_placeholders.py --template templates/level1.docx --out schemas/placeholders.level1.json

```

If `--out` is omitted, JSON is printed to stdout.

### Questionnaire Schema
Regenerate the schema from the Word template:
```bash
python tools/generate_questionnaire_schema.py --placeholders schemas/placeholders.level1.json --mapping schemas/level1_questionnaire.mapping.json --out schemas/level1_questionnaire.schema.json

```

Validate the generated schema:
```bash
python tools/validate_questionnaire_schema.py --schema schemas/level1_questionnaire.schema.json --placeholders schemas/placeholders.level1.json --mapping schemas/level1_questionnaire.mapping.json
```

### Narrative blocks + facility placeholders
The Word renderer now expands HVAC/DHW/Measures blocks into short narrative paragraphs and auto-fills key
facility placeholders from `answers` (even when `placeholders` is present but empty).
Narrative generation logic now lives under `reporting/narratives/` for reuse across renderers.
Narrative modules now include consultant-grade conditional language and
uncertainty handling to reflect available information while keeping a
consistent professional tone.

Minimal `project.json` example that produces a rich heating paragraph:
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
    "heating_notes": "Boilers were observed in the central plant; controls require verification.",
    "dhw_system_type": "dhw_boiler_condensing",
    "dhw_recirc": true,
    "dhw_notes": "DHW storage tank observed in the main mechanical room."
  },
  "selected_measures": ["BAS Upgrade", "Condensing Boiler Retrofit"]
}
```

Manual test command:
```bash
python tools/render_level1.py --template templates/level1.docx --project projects/project.json --out output/level1_rendered.docx
```

Expected output:
* `{Central Heating/Cooling Systems block}` renders as a 3–6 sentence paragraph (not a single word).
* `{Number of Floors}`, `{Number of Suites}`, `{Architectural Condition}` are filled when provided under `answers`.

### Desktop App Smoke-Test Checklist
1. Run `python app_retscreen.py` and confirm the window opens.
2. Open or create a project, enter facility/system answers, select measures, and choose checklist findings.
3. Save and confirm it writes to `projects/<slug>/project.json`.
4. Re-open the same file and confirm fields load.
5. Edit a field and Save, confirm the JSON updates and unknown keys remain.
6. Validate Project (expect OK or warnings dialog).
7. Generate Level 1 and confirm output in `output/`.

### Legacy entry points (deprecated)
The standalone questionnaire builder is still available but no longer recommended:
```bash
python app.py
```

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
python tools/site_wizard.py --new
```
Use flags like `--template`, `--out`, `--no-measures`, or `--no-checklists` to customize the prompt flow.

Clone an existing project file:
```bash
python tools/site_wizard.py --clone projects/2255_victoria_park/project.json
```

Reuse selections from an existing project file:
```bash
python tools/site_wizard.py --reuse projects/2255_victoria_park/project.json
```

Non-interactive example:
```bash
python tools/site_wizard.py --new --non-interactive --set project_info.client_name="ABC" --set project_info.site_address="123 Main" --set project_info.report_date="2026-01-13" --out projects/abc_123/project.json
```

Generate a report from the new project:
```bash
python main.py --project projects/<slug>/project.json --out output/<slug>_level1.docx
```

List measures:
```bash
python main.py --list-measures
```

Validate inputs:
```bash
python main.py --validate
```
