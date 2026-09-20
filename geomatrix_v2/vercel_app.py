"""Vercel service entrypoint for the GEOMATRIX FastAPI backend."""
import importlib
import sys
import types
from importlib.machinery import ModuleSpec
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parent

# The Vercel service root is geomatrix_v2/, so Python does not automatically
# see that directory as the parent package. Register a lightweight package
# namespace whose search path is the service root, then import main normally.
package = sys.modules.get("geomatrix_v2")
if package is None:
    package = types.ModuleType("geomatrix_v2")
    package.__path__ = [str(SERVICE_ROOT)]
    package.__package__ = "geomatrix_v2"
    package.__spec__ = ModuleSpec("geomatrix_v2", loader=None, is_package=True)
    sys.modules["geomatrix_v2"] = package

app = importlib.import_module("geomatrix_v2.main").app
