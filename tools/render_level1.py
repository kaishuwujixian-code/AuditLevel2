import argparse
import json
import os
import sys

from reporting.word_renderer import render_word


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a Level 1 Word document with simple placeholders.")
    parser.add_argument("--template", default="templates/level1.docx", help="Path to the Word template")
    parser.add_argument("--project", default="projects/project.json", help="Path to the project JSON")
    parser.add_argument("--out", default="outputs/level1_rendered.docx", help="Path for the rendered output")
    parser.add_argument(
        "--mapping",
        default=None,
        help="Optional JSON mapping file (e.g., schemas/level1_placeholders.map.json)",
    )
    parser.add_argument("--strict", action="store_true", help="Fail if any placeholders remain unresolved")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.mapping and not os.path.isfile(args.mapping):
        print(f"Mapping file not found: {args.mapping}", file=sys.stderr)
        return 2

    summary = render_word(
        template_path=args.template,
        project_json_path=args.project,
        out_path=args.out,
        mapping_path=args.mapping,
        strict=args.strict,
    )

    print(json.dumps(summary, indent=2))
    if args.strict and summary.get("unresolved"):
        print("Unresolved placeholders remain with --strict enabled.", file=sys.stderr)
        return 1

    if summary.get("strict_error"):
        print("Unresolved placeholders remain.", file=sys.stderr)

    print("Note: python-docx does not expose text inside shapes/textboxes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
