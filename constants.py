from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
STORES_PATH = sorted(path.name for path in DATA_DIR.glob("STORE*"))
