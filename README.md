# report-generator

## Quick Start

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
python tools/new_project.py
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
