from . import dynamic_api_gen
from .version import __version__
from os import path, environ
__version__
try:
    if path.exists(environ.get('API_SPEC_PATH')):
        dynamic_api_gen.populate_api()
except TypeError:
    print('No Dynamic API path found')
