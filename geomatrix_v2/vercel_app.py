"""Vercel service entrypoint for the GEOMATRIX FastAPI backend.

The Vercel service root is geomatrix_v2/, so we create the package namespace
explicitly and load main.py with package semantics. This keeps relative imports
working in both local development and the Vercel service runtime.
"""
import importlib.util
import sys
import types
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parent

package = sys.modules.get("geomatrix_v2")
if package is None:
    package = types.ModuleType("geomatrix_v2")
    package.__path__ = [str(SERVICE_ROOT)]
    sys.modules["geomatrix_v2"] = package

module_name = "geomatrix_v2.main"
module = sys.modules.get(module_name)
if module is None:
    spec = importlib.util.spec_from_file_location(
        module_name,
        SERVICE_ROOT / "main.py",
        submodule_search_locations=[],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load GEOMATRIX FastAPI entrypoint.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

app = module.app
