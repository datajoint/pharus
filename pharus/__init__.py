from .version import __version__
from os import path, environ
__version__
from . import dynamic_api_gen

if path.exists(environ.get('API_SPEC_PATH')): dynamic_api_gen.populate_api()
try:
    import dynamic_api
except ImportError:
    pass