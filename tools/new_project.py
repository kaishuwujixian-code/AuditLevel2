import sys

import site_wizard


def main() -> int:
    return site_wizard.main(["--new", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
