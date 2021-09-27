from .version import __version__
from os import path
__version__
from . import dynamic_api_gen

if path.exists('pharus//dynamic_api_spec.yaml'): dynamic_api_gen.populate_api()
try:
    import dynamic_api
except ImportError:
    pass