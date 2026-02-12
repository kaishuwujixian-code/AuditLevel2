import os
import shutil
import sys


def _get_resource_root() -> str:
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", None)
        if base_dir:
            return os.path.abspath(base_dir)
        return os.path.abspath(os.path.dirname(sys.executable))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _get_app_root() -> str:
    if not getattr(sys, "frozen", False):
        return _get_resource_root()
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(appdata, "AuditStudio")


def _ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _seed_file_if_missing(src: str, dst: str) -> None:
    if not os.path.isfile(src) or os.path.isfile(dst):
        return
    _ensure_directory(os.path.dirname(dst))
    shutil.copy2(src, dst)


def _seed_dir_if_missing(src_dir: str, dst_dir: str, *, suffixes: tuple[str, ...] = (".json",)) -> None:
    if not os.path.isdir(src_dir):
        return
    _ensure_directory(dst_dir)
    for name in os.listdir(src_dir):
        src_path = os.path.join(src_dir, name)
        dst_path = os.path.join(dst_dir, name)
        if os.path.isdir(src_path):
            _seed_dir_if_missing(src_path, dst_path, suffixes=suffixes)
            continue
        if suffixes and not name.lower().endswith(suffixes):
            continue
        _seed_file_if_missing(src_path, dst_path)


RESOURCE_ROOT = _get_resource_root()
APP_ROOT = _get_app_root()
REPO_ROOT = RESOURCE_ROOT

PROJECTS_DIR = os.path.join(APP_ROOT, "projects")
TEMPLATES_DIR = os.path.join(APP_ROOT, "templates")
CATALOGS_DIR = os.path.join(APP_ROOT, "catalogs")
SCHEMAS_DIR = os.path.join(RESOURCE_ROOT, "schemas")
OUTPUT_DIR = os.path.join(APP_ROOT, "output")
RULESETS_DIR = os.path.join(APP_ROOT, "reporting", "rulesets")

DEFAULT_TEMPLATE_JSON = os.path.join(TEMPLATES_DIR, "template.level1.json")
DEFAULT_TEMPLATE_DOCX = os.path.join(TEMPLATES_DIR, "level1.docx")
DEFAULT_MEASURE_CATALOG = os.path.join(CATALOGS_DIR, "measure_catalog.json")
DEFAULT_MISC_CATALOG = os.path.join(CATALOGS_DIR, "misc_catalog.json")

# Ensure writable folders exist.
for _dir in (PROJECTS_DIR, TEMPLATES_DIR, CATALOGS_DIR, OUTPUT_DIR, RULESETS_DIR):
    _ensure_directory(_dir)

# Seed user-writable working files from packaged resources on first run.
_seed_file_if_missing(
    os.path.join(RESOURCE_ROOT, "templates", "template.level1.json"),
    DEFAULT_TEMPLATE_JSON,
)
_seed_file_if_missing(
    os.path.join(RESOURCE_ROOT, "templates", "level1.docx"),
    DEFAULT_TEMPLATE_DOCX,
)
_seed_file_if_missing(
    os.path.join(RESOURCE_ROOT, "catalogs", "measure_catalog.json"),
    DEFAULT_MEASURE_CATALOG,
)
_seed_file_if_missing(
    os.path.join(RESOURCE_ROOT, "catalogs", "misc_catalog.json"),
    DEFAULT_MISC_CATALOG,
)
_seed_dir_if_missing(
    os.path.join(RESOURCE_ROOT, "reporting", "rulesets"),
    RULESETS_DIR,
    suffixes=(".json",),
)
