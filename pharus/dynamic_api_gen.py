import yaml

# Exits the script without killing the python interpreter
def populate_api():
    
    f = open('pharus//dynamic_api.py', 'w')
    y = open('pharus//dynamic_api_spec.yaml', 'r')
    
    valuesYaml = yaml.load(y, Loader=yaml.FullLoader)
    f.write(
"""
from .server import app, protected_route
from .interface import _DJConnector

@app.route('/test', methods=['GET'])
@protected_route
def test(jwt_payload: dict) -> dict:
    return str(_DJConnector._list_schemas(jwt_payload))
""".format(field=valuesYaml['Test'])
    )
    f.close()