from . import dynamic_api_gen
from .version import __version__
from os import path, environ

try:
    if path.exists(environ.get("PHARUS_SPEC_PATH")):
        dynamic_api_gen.populate_api()
except TypeError:
    print("No Dynamic API path found")

try:
    from .dynamic_api import app
except ImportError:
    from .server import app

__all__ = ["__version__", "app"]
