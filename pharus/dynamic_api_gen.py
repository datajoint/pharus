import yaml
from textwrap import indent
# Exits the script without killing the python interpreter
def populate_api():
    
    f = open('pharus//dynamic_api.py', 'w')
    y = open('pharus//dynamic_api_spec.yaml', 'r')
    
    header_template = """
# Auto-generated rest api
from .server import app, protected_route
from .interface import _DJConnector, dj

"""
    f.write(header_template)

    route_template = """

@app.route('{route}', methods=['GET'])
@protected_route
def test(jwt_payload: dict) -> list:
    
{query}

    djconn = _DJConnector._set_datajoint_config(jwt_payload)
    vm_dict = {{s: dj.VirtualModule(s, s, connection=djconn) for s in dj.list_schemas()}}

    return dj_query(**vm_dict)
"""

    valuesYaml = yaml.load(y, Loader=yaml.FullLoader)
    f.write(route_template.format(
        route=valuesYaml['SciViz']['pages']
        ['page2']['grids']['grid1']['components']['component1']['route'],
        query=indent(valuesYaml['SciViz']['pages']
        ['page2']['grids']['grid1']['components']['component1']['dj_query'], '    ')
        )
    )
    f.close()