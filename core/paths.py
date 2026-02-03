import os
import sys


def _get_repo_root() -> str:
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", None)
        if base_dir:
            return os.path.abspath(base_dir)
        return os.path.abspath(os.path.dirname(sys.executable))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


REPO_ROOT = _get_repo_root()
PROJECTS_DIR = os.path.join(REPO_ROOT, "projects")
TEMPLATES_DIR = os.path.join(REPO_ROOT, "templates")
CATALOGS_DIR = os.path.join(REPO_ROOT, "catalogs")
SCHEMAS_DIR = os.path.join(REPO_ROOT, "schemas")
DEFAULT_TEMPLATE_JSON = os.path.join(TEMPLATES_DIR, "template.level1.json")
DEFAULT_TEMPLATE_DOCX = os.path.join(TEMPLATES_DIR, "level1.docx")
DEFAULT_MEASURE_CATALOG = os.path.join(CATALOGS_DIR, "measure_catalog.json")
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")
