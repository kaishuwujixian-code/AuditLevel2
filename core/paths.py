import os


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PROJECTS_DIR = os.path.join(REPO_ROOT, "projects")
TEMPLATES_DIR = os.path.join(REPO_ROOT, "templates")
CATALOGS_DIR = os.path.join(REPO_ROOT, "catalogs")
DEFAULT_TEMPLATE_JSON = os.path.join(TEMPLATES_DIR, "template.level1.json")
DEFAULT_TEMPLATE_DOCX = os.path.join(TEMPLATES_DIR, "level1.docx")
DEFAULT_MEASURE_CATALOG = os.path.join(CATALOGS_DIR, "measure_catalog.json")
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")
