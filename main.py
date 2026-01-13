import argparse
import os

from reporting.level1_generator import generate_level1_report


def _ensure_file(path: str, label: str) -> None:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{label} not found: {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the Level 1 walkthrough report.")
    parser.add_argument("--project", default="project.json", help="Path to project.json")
    parser.add_argument(
        "--template",
        default="templates/template.level1.json",
        help="Path to the template JSON configuration",
    )
    parser.add_argument(
        "--docx-template",
        default="templates/level1.docx",
        help="Path to the Word (.docx) template",
    )
    parser.add_argument(
        "--out",
        default="output/level1_walkthrough.docx",
        help="Output path for the generated Word report",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    _ensure_file(args.project, "Project file")
    _ensure_file(args.template, "Template JSON file")
    _ensure_file(args.docx_template, "Docx template file")

    output_dir = os.path.dirname(args.out)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    generate_level1_report(
        project_json_path=args.project,
        template_json_path=args.template,
        docx_template_path=args.docx_template,
        out_path=args.out,
    )

    print(f"Generated: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
