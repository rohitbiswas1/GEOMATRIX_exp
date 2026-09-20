"""Vercel-compatible FastAPI entrypoint."""
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1] / "geomatrix_v2"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app
