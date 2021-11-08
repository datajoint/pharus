from textwrap import indent
from pathlib import Path
import os
import yaml
import pkg_resources


def populate_api():
    header_template = """# Auto-generated rest api
from .server import app, protected_route
from .interface import _DJConnector, dj
from flask import request
from json import loads
from base64 import b64decode
"""
    route_template = """

@app.route('{route}', methods=['GET'])
@protected_route
def {method_name}(jwt_payload: dict) -> dict:

{query}
{restriction}
    if request.method in {{'GET'}}:
        try:
            djconn = _DJConnector._set_datajoint_config(jwt_payload)
            vm_dict = {{s: dj.VirtualModule(s, s, connection=djconn)
                       for s in dj.list_schemas()}}
            query, fetch_args = dj_query(vm_dict)
            query = query & restriction()
            record_header, table_tuples, total_count = _DJConnector._fetch_records(
                query=query,
                **{{k: (int(v) if k in ('limit', 'page')
                   else (v.split(',') if k == 'order'
                   else loads(b64decode(v.encode('utf-8')).decode('utf-8'))))
                   for k, v in request.args.items()}},
                )
            return dict(recordHeader=record_header, records=table_tuples,
                        totalCount=total_count)
        except Exception as e:
            return str(e), 500


@app.route('{route}/attributes', methods=['GET'])
@protected_route
def {method_name}_attributes(jwt_payload: dict) -> dict:

{query}
    if request.method in {{'GET'}}:
        try:
            djconn = _DJConnector._set_datajoint_config(jwt_payload)
            vm_dict = {{s: dj.VirtualModule(s, s, connection=djconn)
                       for s in dj.list_schemas()}}
            query, fetch_args = dj_query(vm_dict)
            attributes_meta = _DJConnector._get_attributes(query)

            return dict(attributeHeaders=attributes_meta['attribute_headers'],
                        attributes=attributes_meta['attributes'])
        except Exception as e:
            return str(e), 500
"""

    pharus_root = f"{pkg_resources.get_distribution('pharus').module_path}/pharus"
    api_path = f'{pharus_root}/dynamic_api.py'
    spec_path = os.environ.get('API_SPEC_PATH')

    with open(Path(api_path), 'w') as f, open(Path(spec_path), 'r') as y:
        f.write(header_template)
        values_yaml = yaml.load(y, Loader=yaml.FullLoader)
        pages = values_yaml['SciViz']['pages']

        # Crawl through the yaml file for the routes in the components
        for page in pages.values():
            for grid in page['grids'].values():
                for comp in grid['components'].values():
                    if comp['type'] == 'table':
                        f.write(route_template.format(route=comp['route'],
                                method_name=comp['route'].replace('/', ''),
                                query=indent(comp['dj_query'], '    '),
                                restriction=indent(comp['restriction'], '    ')))
