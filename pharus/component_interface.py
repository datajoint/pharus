"""This module is a GUI component library of various common interfaces."""
from base64 import b64decode
import json
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
from uuid import UUID


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
        if type(o) is UUID:
            return str(o)
        if type(o) is str and o == "NaN":
            return None
        if type(o) in (datetime, date):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

    @classmethod
    def dumps(cls, obj):
        return json.dumps(obj, cls=cls)


class Component:
    def __init__(
        self,
        name,
        component_config,
        static_config,
        connection: dj.Connection,
        payload=None,
    ):
        self.name = name
        self.type = component_config["type"]
        self.route = component_config["route"]
        if not all(k in component_config for k in ("x", "y", "height", "width")):
            self.mode = "dynamic"
        else:
            self.mode = "fixed"
            self.x = component_config["x"]
            self.y = component_config["y"]
            self.height = component_config["height"]
            self.width = component_config["width"]
        if static_config:
            self.static_variables = types.MappingProxyType(static_config)
        self.connection = connection
        self.payload = payload


class FetchComponent(Component):
    rest_verb = ["GET"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        component_config = kwargs.get("component_config", args[1] if args else None)
        lcls = locals()
        exec(component_config["dj_query"], globals(), lcls)
        self.dj_query = lcls["dj_query"]
        if "restriction" in component_config:
            exec(component_config["restriction"], globals(), lcls)
            self.dj_restriction = lcls["restriction"]
        else:
            self.dj_restriction = lambda: dict()
        self.vm_list = [
            dj.VirtualModule(
                s,
                s.replace("__", "-"),
                connection=self.connection,
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

    def dj_query_route(self):
        fetch_metadata = self.fetch_metadata
        record_header, table_records, total_count = _DJConnector._fetch_records(
            query=fetch_metadata["query"] & self.restriction,
            fetch_args=fetch_metadata["fetch_args"],
        )

        return (
            NumpyEncoder.dumps(
                dict(
                    recordHeader=record_header,
                    records=table_records,
                    totalCount=total_count,
                )
            ),
            200,
            {"Content-Type": "application/json"},
        )


class DeleteComponent(Component):
    rest_verb = ["DELETE"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dj_query_route(self):
        return


class InsertComponent(Component):
    rest_verb = ["POST", "GET"]
    fields_route_format = "{route}/fields"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        component_config = kwargs.get("component_config", args[1] if args else None)
        self.fields_map = component_config.get("map")
        self.tables = [
            getattr(
                dj.VirtualModule(
                    s,
                    s,
                    connection=self.connection,
                ),
                t,
            )
            for s, t in (
                _.format(**request.args).split(".") for _ in component_config["tables"]
            )
        ]
        self.parents = sorted(
            set(
                [
                    p
                    for t in self.tables
                    for p in t.parents(as_objects=True)
                    if p.full_table_name not in (t.full_table_name for t in self.tables)
                ]
            ),
            key=lambda p: p.full_table_name,
        )
        self.destination_lookup = {
            sub_m.get("input", sub_m["destination"]): sub_m["destination"]
            for m in (self.fields_map or [])
            for sub_m in (m.get("map", []) + [m])
        }
        self.input_lookup = {v: k for k, v in self.destination_lookup.items()}

    def dj_query_route(self):
        with self.connection.transaction:
            for t in self.tables:
                t.insert(
                    [
                        {
                            a: v
                            for k, v in r.items()
                            if (a := self.destination_lookup.get(k, k))
                            in t.heading.attributes
                        }
                        for r in self.payload["submissions"]
                    ]
                )
        return {"response": "Insert Successful"}

    def fields_route(self):
        parent_attributes = sorted(set(sum([p.primary_key for p in self.parents], [])))
        source_fields = {
            **{
                (p_name := f"{p.database}.{dj.utils.to_camel_case(p.table_name)}"): {
                    "values": p.fetch("KEY"),
                    "type": "table",
                    "name": p_name,
                }
                for p in self.parents
            },
            **{
                a: {
                    "datatype": v.type,
                    "type": "attribute",
                    "name": v.name,
                    "default": v.default,
                }
                for t in self.tables
                for a, v in t.heading.attributes.items()
                if a not in parent_attributes
            },
        }

        if not self.fields_map:
            return dict(fields=list(source_fields.values()))
        return dict(
            fields=[
                dict(
                    (
                        field := source_fields.pop(
                            (m_destination := m["destination"].format(**request.args))
                        )
                    ),
                    name=m.get("input", m_destination),
                    **(
                        {
                            "values": [
                                {self.input_lookup.get(k, k): v for k, v in r.items()}
                                for r in field["values"]
                            ]
                        }
                        if m["type"] == "table"
                        else {}
                    ),
                )
                for m in self.fields_map
            ]
            + list(source_fields.values())
        )


class TableComponent(FetchComponent):
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
            query=fetch_metadata["query"] & self.restriction,
            fetch_args=fetch_metadata["fetch_args"],
            limit=int(request.args["limit"]) if "limit" in request.args else 1000,
            page=int(request.args["page"]) if "page" in request.args else 1,
            order=request.args["order"].split(",") if "order" in request.args else None,
            restriction=json.loads(b64decode(request.args["restriction"]))
            if "restriction" in request.args
            else [],
        )

        return (
            NumpyEncoder.dumps(
                dict(
                    recordHeader=record_header,
                    records=table_records,
                    totalCount=total_count,
                )
            ),
            200,
            {"Content-Type": "application/json"},
        )

    def attributes_route(self):
        attributes_meta = _DJConnector._get_attributes(
            self.fetch_metadata["query"] & self.restriction, include_unique_values=True
        )
        return (
            NumpyEncoder.dumps(
                dict(
                    attributeHeaders=attributes_meta["attribute_headers"],
                    attributes=attributes_meta["attributes"],
                )
            ),
            200,
            {"Content-Type": "application/json"},
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
        return (
            NumpyEncoder.dumps(
                dict(
                    recordHeader=record_header,
                    records=table_records,
                    totalCount=total_count,
                )
            ),
            200,
            {"Content-Type": "application/json"},
        )


class PlotPlotlyStoredjsonComponent(FetchComponent):
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
        return (
            NumpyEncoder.dumps(
                (fetch_metadata["query"] & self.restriction).fetch1(
                    *fetch_metadata["fetch_args"]
                )
            ),
            200,
            {"Content-Type": "application/json"},
        )


class FileImageAttachComponent(FetchComponent):
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
    "external": Component,
    "basicquery": FetchComponent,
    "plot:plotly:stored_json": PlotPlotlyStoredjsonComponent,
    "table": TableComponent,
    "antd-table": TableComponent,
    "metadata": MetadataComponent,
    "file:image:attach": FileImageAttachComponent,
    "slider": FetchComponent,
    "dropdown-query": FetchComponent,
    "form": InsertComponent,
    "delete": DeleteComponent,
}
