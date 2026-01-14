# report-generator

## Quick Start

### Run Desktop App
```bash
python app.py
```

### Run RETScreen-style Desktop App
```bash
python app_retscreen.py
```

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
