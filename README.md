# report-generator

## Quick Start

### Run Desktop App
```bash
python app.py
```

### Questionnaire Schema
Regenerate the schema from the Word template:
```bash
python tools/generate_questionnaire_schema.py --template templates/level1.docx --mapping schemas/level1_questionnaire.mapping.json --out schemas/level1_questionnaire.schema.json
```

Validate the generated schema:
```bash
python tools/validate_questionnaire_schema.py --schema schemas/level1_questionnaire.schema.json --template templates/level1.docx
```

Edit `schemas/level1_questionnaire.mapping.json` to add or adjust placeholder-to-question rules and option sets. Any placeholders that do not match a mapping rule are emitted under the `unmapped` section in the schema with a default text question.

### Desktop App Smoke-Test Checklist
1. Run `python app.py` and confirm the window opens.
2. File → New, enter project info, choose Heating/DHW/Cooling/Ventilation values, select measures, add notes.
3. File → Save As, confirm it writes to `projects/<slug>/project.json`.
4. File → Open an existing project.json and confirm fields load.
5. Edit a field and Save, confirm the JSON updates and unknown keys remain.
6. Tools → Validate Project (expect OK or warnings dialog).
7. Report → Generate Level 1 and confirm output in `output/`.

### Generate a report
Windows (PowerShell/CMD):
```bash
python main.py --project project.json --template templates\\template.level1.json --docx-template templates\\level1.docx --out output\\level1_walkthrough.docx
```

POSIX (macOS/Linux):
```bash
python main.py --project project.json --template templates/template.level1.json --docx-template templates/level1.docx --out output/level1_walkthrough.docx
```

### List available measures
Windows:
```bash
python main.py --template templates\\template.level1.json --list-measures
```

POSIX:
```bash
python main.py --template templates/template.level1.json --list-measures
```

### Validate inputs
Windows:
```bash
python main.py --project project.json --template templates\\template.level1.json --docx-template templates\\level1.docx --validate
```

POSIX:
```bash
python main.py --project project.json --template templates/template.level1.json --docx-template templates/level1.docx --validate
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
