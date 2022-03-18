"""This module is a GUI component library of various common interfaces."""
import json
from base64 import b64decode
import datajoint as dj
import re
import inspect
from datetime import date, datetime
from flask import request, send_file
from .interface import _DJConnector
import os
from pathlib import Path
import types
import io
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """teach json to dump datetimes, etc"""

    npmap = {
        np.bool_: bool,
        np.uint8: int,
        np.uint16: int,
        np.uint32: int,
        np.uint64: int,
        np.int8: int,
        np.int16: int,
        np.int32: int,
        np.int64: int,
        np.float32: float,
        np.float64: float,
        np.ndarray: list,
    }

    def default(self, o):
        if type(o) in self.npmap:
            return self.npmap[type(o)](o)
        if type(o) in (datetime, date):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

    @classmethod
    def dumps(cls, obj):
        return json.dumps(obj, cls=cls)


class QueryComponent:
    attributes_route_format = None

    def __init__(self, name, component_config, static_config, jwt_payload: dict):
        lcls = locals()
        self.name = name
        if static_config:
            self.static_variables = types.MappingProxyType(static_config)
        if not all(k in component_config for k in ("x", "y", "height", "width")):
            self.mode = "dynamic"
        else:
            self.mode = "fixed"
            self.x = component_config["x"]
            self.y = component_config["y"]
            self.height = component_config["height"]
            self.width = component_config["width"]
        self.type = component_config["type"]
        self.route = component_config["route"]
        exec(component_config["dj_query"], globals(), lcls)
        self.dj_query = lcls["dj_query"]
        if self.attributes_route_format:
            self.attribute_route = self.attributes_route_format.format(
                route=component_config["route"]
            )
        if "restriction" in component_config:
            exec(component_config["restriction"], globals(), lcls)
            self.dj_restriction = lcls["restriction"]
        else:
            self.dj_restriction = lambda: dict()

        self.vm_list = [
            dj.VirtualModule(
                s,
                s,
                connection=dj.conn(
                    host=jwt_payload["databaseAddress"],
                    user=jwt_payload["username"],
                    password=jwt_payload["password"],
                    reset=True,
                ),
            )
            for s in inspect.getfullargspec(self.dj_query).args
        ]

    @property
    def fetch_metadata(self):
        return self.dj_query(*self.vm_list)

    @property
    def restriction(self):
        # first element includes the spec's restriction,
        # second element includes the restriction from query parameters
        return dj.AndList(
            [
                self.dj_restriction(),
                {
                    k: (
                        datetime.fromtimestamp(float(v)).isoformat()
                        if re.match(
                            r"^date.*$",
                            self.fetch_metadata["query"].heading.attributes[k].type,
                        )
                        else v
                    )
                    for k, v in request.args.items()
                    if k in self.fetch_metadata["query"].heading.attributes
                },
            ]
        )


class TableComponent(QueryComponent):
    attributes_route_format = "{route}/attributes"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frontend_map = {
            "source": "sci-viz/src/Components/Table/TableView.tsx",
            "target": "TableView",
        }
        self.response_examples = {
            "dj_query_route": {
                "recordHeader": ["subject_uuid", "session_start_time", "session_uuid"],
                "records": [
                    [
                        "00778394-c956-408d-8a6c-ca3b05a611d5",
                        1565436299.0,
                        "fb9bdf18-76be-452b-ac4e-21d5de3a6f9f",
                    ],
                    [
                        "00778394-c956-408d-8a6c-ca3b05a611d5",
                        1565601663.0,
                        "d47e9a4c-18dc-4d4d-991c-d30059ec2cbd",
                    ],
                ],
                "totalCount": 9141,
            },
            "attributes_route": {
                "attributeHeaders": [
                    "name",
                    "type",
                    "nullable",
                    "default",
                    "autoincrement",
                ],
                "attributes": {
                    "primary": [
                        ["subject_uuid", "uuid", False, None, False],
                        ["session_start_time", "datetime", False, None, False],
                    ],
                    "secondary": [["session_uuid", "uuid", False, None, False]],
                },
            },
        }

    # Returns the result of djquery with paging, sorting, filtering
    def dj_query_route(self):
        fetch_metadata = self.fetch_metadata
        record_header, table_records, total_count = _DJConnector._fetch_records(
            query=fetch_metadata["query"] & self.restriction[0],
            fetch_args=fetch_metadata["fetch_args"],
            **{
                k: (
                    int(v)
                    if k in ("limit", "page")
                    else (
                        v.split(",")
                        if k == "order"
                        else json.loads(b64decode(v.encode("utf-8")).decode("utf-8"))
                    )
                )
                for k, v in request.args.items()
            },
        )
        return dict(
            recordHeader=record_header, records=table_records, totalCount=total_count
        )

    def attributes_route(self):
        attributes_meta = _DJConnector._get_attributes(self.fetch_metadata["query"])
        return dict(
            attributeHeaders=attributes_meta["attribute_headers"],
            attributes=attributes_meta["attributes"],
        )


class MetadataComponent(TableComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frontend_map = "sci-viz/src/Components/Table/Metadata.tsx:Metadata"
        self.response_examples = {
            "dj_query_route": {
                "recordHeader": ["subject_uuid", "session_start_time", "session_uuid"],
                "records": [
                    [
                        "00778394-c956-408d-8a6c-ca3b05a611d5",
                        1565436299.0,
                        "fb9bdf18-76be-452b-ac4e-21d5de3a6f9f",
                    ]
                ],
                "totalCount": 1,
            },
            "attributes_route": {
                "attributeHeaders": [
                    "name",
                    "type",
                    "nullable",
                    "default",
                    "autoincrement",
                ],
                "attributes": {
                    "primary": [
                        ["subject_uuid", "uuid", False, None, False],
                        ["session_start_time", "datetime", False, None, False],
                    ],
                    "secondary": [["session_uuid", "uuid", False, None, False]],
                },
            },
        }

    def dj_query_route(self):
        fetch_metadata = self.fetch_metadata
        record_header, table_records, total_count = _DJConnector._fetch_records(
            query=fetch_metadata["query"] & self.restriction,
            fetch_args=fetch_metadata["fetch_args"],
        )
        return dict(
            recordHeader=record_header, records=table_records, totalCount=total_count
        )


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
                        "x": ["giraffes", "orangutans", "monkeys"],
                        "y": [20, 14, 23],
                        "type": "bar",
                    }
                ],
                "layout": {"title": "Total Number of Animals"},
            },
        }

    def dj_query_route(self):
        fetch_metadata = self.fetch_metadata
        return NumpyEncoder.dumps(
            (fetch_metadata["query"] & self.restriction).fetch1(
                *fetch_metadata["fetch_args"]
            )
        )


class BasicQuery(QueryComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frontend_map = {
            "source": "sci-viz/src/Components/Plots/FullPlotly.tsx",
            "target": "FullPlotly",
        }
        self.response_examples = {
            "dj_query_route": {
                "recordHeader": ["subject_uuid", "session_start_time", "session_uuid"],
                "records": [
                    [
                        "00778394-c956-408d-8a6c-ca3b05a611d5",
                        1565436299.0,
                        "fb9bdf18-76be-452b-ac4e-21d5de3a6f9f",
                    ]
                ],
                "totalCount": 1,
            },
        }

    def dj_query_route(self):
        fetch_metadata = self.fetch_metadata
        record_header, table_records, total_count = _DJConnector._fetch_records(
            query=fetch_metadata["query"] & self.restriction,
            fetch_args=fetch_metadata["fetch_args"],
        )
        return dict(
            recordHeader=record_header, records=table_records, totalCount=total_count
        )


class FileImageAttachComponent(QueryComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frontend_map = {
            "source": "sci-viz/src/Components/Plots/Image.tsx",
            "target": "Image",
        }
        self.response_examples = {
            "dj_query_route": b"PNG...",
        }

    def dj_query_route(self):
        fetch_metadata = self.fetch_metadata
        attach_relpath = (fetch_metadata["query"] & self.restriction).fetch1(
            *fetch_metadata["fetch_args"]
        )
        with open(Path(os.getcwd(), attach_relpath), "rb") as f:
            image_data = f.read()
        os.unlink(Path(os.getcwd(), attach_relpath))
        return send_file(io.BytesIO(image_data), download_name=attach_relpath)


type_map = {
    "basicquery": BasicQuery,
    "plot:plotly:stored_json": PlotPlotlyStoredjsonComponent,
    "table": TableComponent,
    "metadata": MetadataComponent,
    "file:image:attach": FileImageAttachComponent,
    "slider": BasicQuery,
    "dropdown-query": BasicQuery,
}
