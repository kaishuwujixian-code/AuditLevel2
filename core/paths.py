import os
import shutil
import sys
import tempfile


def _get_resource_root() -> str:
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", None)
        if base_dir:
            return os.path.abspath(base_dir)
        return os.path.abspath(os.path.dirname(sys.executable))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _is_writable_dir(path: str) -> bool:
    if not os.path.isdir(path):
        return False
    try:
        with tempfile.NamedTemporaryFile(dir=path, delete=True):
            return True
    except OSError:
        return False


def _get_app_root() -> str:
    env_root = os.environ.get("AUDITSTUDIO_APP_ROOT")
    if env_root:
        return os.path.abspath(os.path.expanduser(env_root))

    resource_root = _get_resource_root()
    if not getattr(sys, "frozen", False):
        return resource_root

    portable_mode = os.environ.get("AUDITSTUDIO_PORTABLE", "").strip().lower()
    if portable_mode in {"1", "true", "yes", "on"}:
        return resource_root

    if _is_writable_dir(resource_root):
        return resource_root

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


def _get_audit_profile() -> str:
    profile = os.environ.get("AUDITSTUDIO_AUDIT_PROFILE", "level1").strip().lower()
    if profile in {"level2", "2", "l2"}:
        return "level2"
    return "level1"


RESOURCE_ROOT = _get_resource_root()
APP_ROOT = _get_app_root()
REPO_ROOT = RESOURCE_ROOT
AUDIT_PROFILE = _get_audit_profile()

PROJECTS_DIR = os.path.join(APP_ROOT, "projects")
TEMPLATES_DIR = os.path.join(APP_ROOT, "templates")
SCHEMAS_DIR = os.path.join(RESOURCE_ROOT, "schemas")
OUTPUT_DIR = os.path.join(APP_ROOT, "output")

if AUDIT_PROFILE == "level2":
    CATALOGS_DIR = os.path.join(APP_ROOT, "catalogs", "level2")
    RULESETS_DIR = os.path.join(APP_ROOT, "reporting", "rulesets", "level2")
    DEFAULT_TEMPLATE_JSON = os.path.join(TEMPLATES_DIR, "template.level2.json")
    DEFAULT_TEMPLATE_DOCX = os.path.join(TEMPLATES_DIR, "level2.docx")
    DEFAULT_SCHEMA_JSON = os.path.join(SCHEMAS_DIR, "level2_questionnaire.schema.json")
    DEFAULT_MAPPING_JSON = os.path.join(SCHEMAS_DIR, "level2_questionnaire.mapping.json")
else:
    CATALOGS_DIR = os.path.join(APP_ROOT, "catalogs")
    RULESETS_DIR = os.path.join(APP_ROOT, "reporting", "rulesets")
    DEFAULT_TEMPLATE_JSON = os.path.join(TEMPLATES_DIR, "template.level1.json")
    DEFAULT_TEMPLATE_DOCX = os.path.join(TEMPLATES_DIR, "level1.docx")
    DEFAULT_SCHEMA_JSON = os.path.join(SCHEMAS_DIR, "level1_questionnaire.schema.json")
    DEFAULT_MAPPING_JSON = os.path.join(SCHEMAS_DIR, "level1_questionnaire.mapping.json")

DEFAULT_MEASURE_CATALOG = os.path.join(CATALOGS_DIR, "measure_catalog.json")
DEFAULT_MISC_CATALOG = os.path.join(CATALOGS_DIR, "misc_catalog.json")

for _dir in (PROJECTS_DIR, TEMPLATES_DIR, CATALOGS_DIR, OUTPUT_DIR, RULESETS_DIR):
    _ensure_directory(_dir)

_seed_file_if_missing(
    os.path.join(RESOURCE_ROOT, "templates", "level1.docx"),
    os.path.join(TEMPLATES_DIR, "level1.docx"),
)
_seed_file_if_missing(
    os.path.join(RESOURCE_ROOT, "templates", "level2.docx"),
    os.path.join(TEMPLATES_DIR, "level2.docx"),
)
_seed_file_if_missing(
    os.path.join(RESOURCE_ROOT, "templates", "template.level1.json"),
    os.path.join(TEMPLATES_DIR, "template.level1.json"),
)
_seed_file_if_missing(
    os.path.join(RESOURCE_ROOT, "templates", "template.level2.json"),
    os.path.join(TEMPLATES_DIR, "template.level2.json"),
)

_catalog_source_dir = os.path.join(
    RESOURCE_ROOT,
    "catalogs" if AUDIT_PROFILE == "level1" else "catalogs",  # explicit for clarity
)
for _catalog_name in (
    "measure_catalog.json",
    "misc_catalog.json",
    "heating_catalog.json",
    "cooling_catalog.json",
    "dhw_catalog.json",
    "ventilation_catalog.json",
):
    _seed_file_if_missing(
        os.path.join(_catalog_source_dir, _catalog_name),
        os.path.join(CATALOGS_DIR, _catalog_name),
    )

_ruleset_source = (
    os.path.join(RESOURCE_ROOT, "reporting", "rulesets")
    if AUDIT_PROFILE == "level1"
    else os.path.join(RESOURCE_ROOT, "reporting", "rulesets", "level2")
)
_seed_dir_if_missing(_ruleset_source, RULESETS_DIR, suffixes=(".json",))
