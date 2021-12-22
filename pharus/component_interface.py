"""This module is a GUI component library of various common interfaces."""
import json
from base64 import b64decode
import datajoint as dj
import re
import inspect
from datetime import datetime
from flask import request
from .interface import _DJConnector


class QueryComponent():
    def __init__(self, name, component_config, create_attributes_route=False):
        lcls = locals()
        self.name = name
        if not all(k in component_config for k in ('x', 'y', 'height', 'width')):
            self.mode = 'dynamic'
        else:
            self.mode = 'fixed'
            self.x = component_config['x']
            self.y = component_config['y']
            self.height = component_config['height']
            self.width = component_config['width']
        self.type = component_config['type']
        self.route = component_config['route']
        exec(component_config['dj_query'], globals(), lcls)
        self.dj_query = lcls["dj_query"]
        if create_attributes_route:
            self.attribute_route = f'{component_config["route"]}/attributes'
        if component_config['restriction']:
            exec(component_config['restriction'], globals(), lcls)
            self.restriction = lcls["restriction"]

    # pylint: disable=method-hidden
    @staticmethod
    def restriction(**kwargs):
        return dict(**kwargs)


class TableComponent(QueryComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frontend_map = {
            "source": "sci-viz/src/Components/Table/TableView.tsx",
            "target": "TableView",
        }
        self.response_examples = {}

    # Returns the result of djquery with paging, sorting, filtering
    def dj_query_route(self, jwt_payload: dict):
        djconn = dj.conn(host=jwt_payload['databaseAddress'],
                         user=jwt_payload['username'],
                         password=jwt_payload['password'], reset=True)
        vm_list = [dj.VirtualModule(s, s, connection=djconn)
                   for s in inspect.getfullargspec(self.dj_query).args]
        djdict = self.dj_query(*vm_list)
        djdict['query'] = djdict['query'] & self.restriction()
        record_header, table_tuples, total_count = _DJConnector._fetch_records(
            query=djdict['query'], fetch_args=djdict['fetch_args'],
            **{k: (int(v) if k in ('limit', 'page')
                   else (v.split(',') if k == 'order'
                   else json.loads(b64decode(v.encode('utf-8')).decode('utf-8'))))
               for k, v in request.args.items()},
        )
        return dict(recordHeader=record_header, records=table_tuples,
                    totalCount=total_count)

    def attributes_route(self, jwt_payload: dict):
        djconn = dj.conn(host=jwt_payload['databaseAddress'],
                         user=jwt_payload['username'],
                         password=jwt_payload['password'], reset=True)
        vm_list = [dj.VirtualModule(s, s, connection=djconn)
                   for s in inspect.getfullargspec(self.dj_query).args]
        djdict = self.dj_query(*vm_list)
        attributes_meta = _DJConnector._get_attributes(djdict['query'])

        return dict(attributeHeaders=attributes_meta['attribute_headers'],
                    attributes=attributes_meta['attributes'])


class MetadataComponent(QueryComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frontend_map = {
            "source": "sci-viz/src/Components/Table/TableView.tsx",
            "target": "TableView",
        }
        self.response_examples = {}

    # Returns the result of djquery with paging, sorting, filtering
    def dj_query_route(self, jwt_payload: dict):
        djconn = dj.conn(host=jwt_payload['databaseAddress'],
                         user=jwt_payload['username'],
                         password=jwt_payload['password'], reset=True)
        vm_list = [dj.VirtualModule(s, s, connection=djconn)
                   for s in inspect.getfullargspec(self.dj_query).args]
        djdict = self.dj_query(*vm_list)
        djdict['query'] = djdict['query'] & self.restriction()
        djdict['query'] = djdict['query'] & {k: datetime.fromtimestamp(float(v))
                                             if re.match(r'^datetime.*$', djdict['query'].heading.attributes[k].type)
                                             else v for k, v in request.args.items() if k in djdict['query'].heading.attributes}
        record_header, table_tuples, total_count = _DJConnector._fetch_records(
            fetch_args=djdict['fetch_args'], query=djdict['query'])
        return dict(recordHeader=record_header, records=table_tuples,
                    totalCount=total_count)

    def attributes_route(self, jwt_payload: dict):
        djconn = dj.conn(host=jwt_payload['databaseAddress'],
                         user=jwt_payload['username'],
                         password=jwt_payload['password'], reset=True)
        vm_list = [dj.VirtualModule(s, s, connection=djconn)
                   for s in inspect.getfullargspec(self.dj_query).args]
        djdict = self.dj_query(*vm_list)
        attributes_meta = _DJConnector._get_attributes(djdict['query'])

        return dict(attributeHeaders=attributes_meta['attribute_headers'],
                    attributes=attributes_meta['attributes'])


class PlotPlotlyStoredjsonComponent(QueryComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frontend_map = {
            "source": "sci-viz/src/Components/Plots/FullPlotly.tsx",
            "target": "FullPlotly",
        }
        self.response_examples = {
            "dj_query_route": {
                "data": [
                    {
                        "x": [
                            "giraffes",
                            "orangutans",
                            "monkeys"
                        ],
                        "y": [
                            20,
                            14,
                            23
                        ],
                        "type": "bar"
                    }
                ],
                "layout": {
                    "title": "Total Number of Animals"
                }
            },
        }

    # @property
    # def template(self):
    #     return f'''
    #         <div key='{self.name}' data-grid={{{{x: {self.x}, y: {self.y}, w: {self.width}, h: {self.height}, static: true}}}}>
    #             <div className='plotContainer'>
    #                 <{self.frontend_map['target']} token={{this.props.jwtToken}} route='{self.route}' restrictionList={{restrictionList}}/>
    #             </div>
    #         </div>
    #     '''

    def dj_query_route(self, jwt_payload: dict):
        djconn = dj.conn(host=jwt_payload['databaseAddress'],
                         user=jwt_payload['username'],
                         password=jwt_payload['password'], reset=True)
        vm_list = [dj.VirtualModule(s, s, connection=djconn)
                   for s in inspect.getfullargspec(self.dj_query).args]
        djdict = self.dj_query(*vm_list)
        djdict['query'] = djdict['query'] & self.restriction()
        djdict['query'] = djdict['query'] & {
            k: datetime.fromtimestamp(float(v))
            if re.match(r'^datetime.*$', djdict['query'].heading.attributes[k].type)
            else v for k, v in request.args.items() if k in djdict['query'].heading.attributes}
        return djdict['query'].fetch1(*djdict['fetch_args'])


type_map = {
    "plot:plotly:stored_json": PlotPlotlyStoredjsonComponent,
    "table": TableComponent,
    "metadata": MetadataComponent
}
