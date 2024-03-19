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
import cv2
import base64
from dateutil import parser


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


class SlideshowComponent(FetchComponent):
    rest_verb = ["GET"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dj_query_route(self):
        fetch_metadata = self.fetch_metadata

        # Dj query provided should return only a video location
        video_name = (fetch_metadata["query"] & self.restriction).fetch1(
            *fetch_metadata["fetch_args"]
        )
        video = cv2.VideoCapture(video_name)

        payload_size = 0  # bytes
        encoded_frames = []
        last_chunk = False

        chunk_size = int(request.args["chunk_size"])
        start_frame = int(request.args["start_frame"])

        video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        while payload_size < chunk_size:
            success, frame = video.read()
            if not success:
                last_chunk = True
                break
            encoded_f = cv2.imencode(".jpeg", frame)[1].tobytes()
            encoded_frames.append(base64.b64encode(encoded_f).decode())
            payload_size += 1

        return (
            NumpyEncoder.dumps(
                {
                    "frameMeta": {
                        "fps": 50,
                        "frameCount": len(encoded_frames),
                        "finalChunk": last_chunk,
                    },
                    "frames": encoded_frames,
                }
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
    presets_route_format = "{route}/presets"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.component_config = kwargs.get(
            "component_config", args[1] if args else None
        )
        self.fields_map = self.component_config.get("map")
        self.tables = [
            getattr(
                dj.VirtualModule(
                    s,
                    s,
                    connection=self.connection,
                ),
                t[0],
            )
            if len(t) == 1
            else getattr(
                getattr(
                    dj.VirtualModule(
                        s,
                        s,
                        connection=self.connection,
                    ),
                    t[0],
                ),
                t[1],
            )
            for s, t in (
                (
                    _.format(**request.args).split(".")[0],
                    _.format(**request.args).split(".")[1:],
                )
                for _ in self.component_config["tables"]
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
        self.datatype_lookup = {
            k: v[1] for t in self.tables for k, v in t.heading.attributes.items()
        }
        self.nullable_lookup = [
            k
            for t in self.tables
            for k, v in t.heading.attributes.items()
            if v.nullable
        ]
        print(self.nullable_lookup, flush=True)

        if "presets" in self.component_config:
            lcls = locals()
            exec(self.component_config["presets"], globals(), lcls)
            self.presets = lcls["presets"]

            self.preset_vm_list = [
                dj.VirtualModule(
                    s,
                    s.replace("__", "-"),
                    connection=self.connection,
                )
                for s in inspect.getfullargspec(self.presets).args
            ]

    @property
    def presets_dict(self):
        return self.presets(*self.preset_vm_list)

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
                    "values": [NumpyEncoder.dumps(row) for row in p.fetch("KEY")]
                    if not all(k in self.nullable_lookup for k in p.primary_key)
                    else [NumpyEncoder.dumps(row) for row in p.fetch("KEY")]
                    + [NumpyEncoder.dumps({k: None for k in p.primary_key})],
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
                                json.dumps(
                                    {
                                        self.input_lookup.get(k, k): v
                                        for k, v in json.loads(r).items()
                                    }
                                )
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

    def presets_route(self):
        # Table content for presets should follow the following format:
        #
        # preset_names: string
        # ---
        # presets: blob or json
        #
        # Example result from query:
        # [['preset_name', {"b_id": 1, "b_number": 2345}],
        # ['preset2_name', {"b_id": 13, "b_number": 225}]]
        #
        # If you have a name mapping it will be applied to each preset
        # Route will 404 if no preset query is defined and 500 if there is an Exception

        # Helper function to convert datetime strings
        def convert_datetime_string(datetime_string):
            try:
                dt = parser.parse(datetime_string)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError("Invalid datetime string")

        # Helper function to filter out fields not in the insert,
        # as well as apply the fields_map
        def filter_preset(preset: dict):
            # Any key that follows the schema.table.attribute format,
            # and its schema.table is not in the forms is filtered out.

            preset_with_tables_filtered = {
                k: v
                for k, v in preset.items()
                if (
                    len(k.split(".")) == 1
                    or ".".join(k.split(".")[0:2]) in self.component_config["tables"]
                )
            }
            return {
                (
                    self.input_lookup[a]
                    if (a := k.split(".").pop()) in self.input_lookup
                    else a
                ): convert_datetime_string(v)
                if a in self.datatype_lookup
                and re.search(r"^date.*|time.*$", self.datatype_lookup[a])
                else v
                for k, v in preset_with_tables_filtered.items()
            }

        if "presets" not in self.component_config:
            return (
                "No Preset query found",
                404,
                {"Content-Type": "text/plain"},
            )

        try:
            filtered_preset_dictionary = {
                k: filter_preset(v) for k, v in self.presets_dict.items()
            }
        except ValueError as e:
            return (
                str(e),
                406,
                {"Content-Type": "text/plain"},
            )

        return (
            NumpyEncoder.dumps(filtered_preset_dictionary),
            200,
            {"Content-Type": "application/json"},
        )


class TableComponent(FetchComponent):
    attributes_route_format = "{route}/attributes"
    uniques_route_format = "{route}/uniques"

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
            self.fetch_metadata["query"] & self.restriction
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

    def uniques_route(self):
        query = self.fetch_metadata["query"] & self.restriction
        query_attributes = dict(primary=[], secondary=[])
        for attribute_name, attribute_info in query.heading.attributes.items():
            if attribute_info.in_key:
                query_attributes["primary"].append(
                    (
                        [
                            dict({"text": str(v), "value": v})
                            for (v,) in (dj.U(attribute_name) & query).fetch()
                        ]
                        if True
                        else None,
                    )
                )
            else:
                query_attributes["secondary"].append(
                    (
                        [
                            dict({"text": str(v), "value": v})
                            for (v,) in (dj.U(attribute_name) & query).fetch()
                        ]
                        if True
                        else None,
                    )
                )

        return (
            NumpyEncoder.dumps(
                dict(
                    unique_values=query_attributes,
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
    "slideshow": SlideshowComponent,
    "delete": DeleteComponent,
}
