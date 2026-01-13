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
