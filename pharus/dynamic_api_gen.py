from textwrap import indent
from pathlib import Path
import os
import yaml
import pkg_resources
import json
import re


def populate_api():
    header_template = """# Auto-generated rest api
from .server import app, protected_route
from .interface import _DJConnector, dj
from flask import request
from json import loads
from base64 import b64decode
from datetime import datetime
import inspect
try:
    from .extra_component_interface import type_map
except:
    from .component_interface import type_map
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
            vm_list = [dj.VirtualModule(s, s, connection=djconn)
                       for s in inspect.getfullargspec(dj_query).args]
            djdict = dj_query(*vm_list)
            djdict['query'] = djdict['query'] & restriction()
            record_header, table_tuples, total_count = _DJConnector._fetch_records(
                query=djdict['query'], fetch_args=djdict['fetch_args'],
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
            vm_list = [dj.VirtualModule(s, s, connection=djconn)
                       for s in inspect.getfullargspec(dj_query).args]
            djdict = dj_query(*vm_list)
            attributes_meta = _DJConnector._get_attributes(djdict['query'])

            return dict(attributeHeaders=attributes_meta['attribute_headers'],
                        attributes=attributes_meta['attributes'])
        except Exception as e:
            return str(e), 500
"""

    plot_route_template = '''

@app.route('{route}', methods=['GET'])
@protected_route
def {method_name}(jwt_payload: dict) -> dict:

{query}
{restriction}
    if request.method in {{'GET'}}:
        try:
            component_instance = type_map['{component_type}'](name='{component_name}', component_config={component})
            return component_instance.dj_query_route(jwt_payload)
        except Exception as e:
            return str(e), 500
'''

    metadata_template = """

@app.route('{route}', methods=['GET'])
@protected_route
def {method_name}(jwt_payload: dict) -> dict:

{query}
{restriction}
    if request.method in {{'GET'}}:
        try:
            djconn = _DJConnector._set_datajoint_config(jwt_payload)
            vm_list = [dj.VirtualModule(s, s, connection=djconn)
                       for s in inspect.getfullargspec(dj_query).args]
            djdict = dj_query(*vm_list)
            djdict['query'] = djdict['query'] & restriction()
            djdict['query'] = djdict['query'] & {{k: datetime.fromtimestamp(int(v))
                                                 if djdict['query'].heading.attributes[k].type
                                                 in ('datetime')
                                                 else v for k, v in request.args.items()}}
            record_header, table_tuples, total_count = _DJConnector._fetch_records(
                fetch_args=djdict['fetch_args'], query=djdict['query'])
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
            vm_list = [dj.VirtualModule(s, s, connection=djconn)
                       for s in inspect.getfullargspec(dj_query).args]
            djdict = dj_query(*vm_list)
            attributes_meta = _DJConnector._get_attributes(djdict['query'])

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
        if 'extra_components' in values_yaml['SciViz'] and 'config' in values_yaml['SciViz']['extra_components']:
            with open(Path(pharus_root, 'extra_component_interface.py'), 'w') as extra_component_config:
                extra_component_config.write(
                    values_yaml['SciViz']['extra_components']['config'])
        pages = values_yaml['SciViz']['pages']

        # Crawl through the yaml file for the routes in the components
        for page in pages.values():
            for grid in page['grids'].values():
                if grid['type'] == 'dynamic':
                    f.write(route_template.format(route=grid['route'],
                            method_name=grid['route'].replace('/', ''),
                            query=indent(grid['dj_query'], '    '),
                            restriction=indent(grid['restriction'], '    ')))
                    for comp in grid['component_templates'].values():
                        if re.match(r'^plot.*$', comp['type']):
                            f.write(plot_route_template.format(
                                route=comp['route'],
                                method_name=comp['route'].replace('/', ''),
                                query=indent(comp['dj_query'], '    '),
                                restriction=indent(
                                    comp['restriction'], '    '),
                                component_type=comp['type'],
                                component_name=comp_name,
                                component=json.dumps(comp)))
                        if re.match(r'^metadata.*$', comp['type']):
                            f.write(metadata_template.format(route=comp['route'],
                                    method_name=comp['route'].replace('/', ''),
                                    query=indent(comp['dj_query'], '    '),
                                    restriction=indent(comp['restriction'], '    ')))
                    continue
                for comp_name, comp in grid['components'].items():
                    if re.match(r'^table.*$', comp['type']):
                        f.write(route_template.format(route=comp['route'],
                                method_name=comp['route'].replace('/', ''),
                                query=indent(comp['dj_query'], '    '),
                                restriction=indent(comp['restriction'], '    ')))
                    if re.match(r'^plot.*$', comp['type']):
                        f.write(plot_route_template.format(
                                route=comp['route'],
                                method_name=comp['route'].replace('/', ''),
                                query=indent(comp['dj_query'], '    '),
                                restriction=indent(
                                    comp['restriction'], '    '),
                                component_type=comp['type'],
                                component_name=comp_name,
                                component=json.dumps(comp)))
                    if re.match(r'^metadata.*$', comp['type']):
                        f.write(metadata_template.format(route=comp['route'],
                                method_name=comp['route'].replace('/', ''),
                                query=indent(comp['dj_query'], '    '),
                                restriction=indent(comp['restriction'], '    ')))
