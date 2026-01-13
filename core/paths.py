import os


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PROJECTS_DIR = os.path.join(REPO_ROOT, "projects")
TEMPLATES_DIR = os.path.join(REPO_ROOT, "templates")
DEFAULT_TEMPLATE_JSON = os.path.join(TEMPLATES_DIR, "template.level1.json")
DEFAULT_TEMPLATE_DOCX = os.path.join(TEMPLATES_DIR, "level1.docx")
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")
