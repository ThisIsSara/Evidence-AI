# config.py
# Central place for simple project settings (paths, filenames).
# Keeping this in one file means we never hardcode paths elsewhere.

from pathlib import Path

# BASE_DIR points to the folder that contains this file (the project root).
BASE_DIR = Path(__file__).resolve().parent

# Folders used by the app.
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

# SQLite database file and the demo case JSON file.
DATABASE_PATH = DATA_DIR / "evidence.db"
DEMO_CASE_PATH = DATA_DIR / "demo_case.json"

# NOTE: No AI API key is required yet.
# In a later phase, an Anthropic API key will be read from a .env file here.
