from pathlib import Path
import os
from envyaml import EnvYAML
import pkg_resources
import json
import re
import warnings
from pharus.component_interface import TableComponent, InsertComponent, FetchComponent


def populate_api():
    header_template = """# Auto-generated rest api
from .server import app, protected_route
from .interface import _DJConnector
from flask import request
import datajoint as dj
from json import loads
from base64 import b64decode
from datetime import datetime
import inspect
import traceback
import os
try:
    from .component_interface_override import type_map
except (ModuleNotFoundError, ImportError):
    from .component_interface import type_map
"""
    route_template = """

@app.route('{route}', methods={rest_verb})
@protected_route(include_user_obj=False)
def {method_name}(connection: dj.Connection) -> dict:

    if request.method in {rest_verb}:
        try:
            component_instance = type_map['{component_type}'](name='{component_name}',
                                                              component_config={component},
                                                              static_config={static_config},
                                                              connection=connection,
                                                              {payload})
            return component_instance.{method_name_type}()
        except Exception as e:
            return traceback.format_exc(), 500
"""
    route_template_nologin = """

@app.route('{route}', methods={rest_verb})
def {method_name}() -> dict:
    if request.method in {rest_verb}:
        connection = dj.Connection(
            host=os.environ["PHARUS_HOST"],
            user=os.environ["PHARUS_USER"],
            password=os.environ["PHARUS_PASSWORD"],
        )
        try:
            component_instance = type_map['{component_type}'](name='{component_name}',
                                                              component_config={component},
                                                              static_config={static_config},
                                                              connection=connection,
                                                              {payload})
            return component_instance.{method_name_type}()
        except Exception as e:
            return traceback.format_exc(), 500
"""

    pharus_root = f"{pkg_resources.get_distribution('pharus').module_path}/pharus"
    api_path = f"{pharus_root}/dynamic_api.py"
    spec_path = os.environ.get("PHARUS_SPEC_PATH")
    values_yaml = EnvYAML(Path(spec_path))
    with open(Path(api_path), "w") as f:
        f.write(header_template)
        active_route_template = (
            route_template if values_yaml["SciViz"]["auth"] else route_template_nologin
        )
        if (
            "component_interface" in values_yaml["SciViz"]
            and "override" in values_yaml["SciViz"]["component_interface"]
        ):
            with open(
                Path(pharus_root, "component_interface_override.py"), "w"
            ) as component_interface_override:
                component_interface_override.write(
                    values_yaml["SciViz"]["component_interface"]["override"]
                )
        type_map_str = ""
        try:
            type_map_str = "USING OVERRIDE TYPE_MAP"
            from .component_interface_override import type_map
        except (ModuleNotFoundError, ImportError):
            type_map_str = "USING STANDARD TYPE_MAP"
            from .component_interface import type_map
        except Exception as e:
            raise e
        print(type_map_str, flush=True)
        static_config = (
            json.dumps(values_yaml["SciViz"]["component_interface"]["static_variables"])
            if (
                "component_interface" in values_yaml["SciViz"]
                and "static_variables" in values_yaml["SciViz"]["component_interface"]
            )
            else None
        )
        pages = values_yaml["SciViz"]["pages"]
        # Crawl through the yaml file for the routes in the components
        for page in pages.values():
            for grid in page["grids"].values():
                if grid["type"] == "dynamic":
                    f.write(
                        (active_route_template).format(
                            route=grid["route"],
                            rest_verb=[FetchComponent.rest_verb[0]],
                            method_name=grid["route"].replace("/", ""),
                            component_type="basicquery",
                            component_name="dynamicgrid",
                            component=json.dumps(grid),
                            static_config=static_config,
                            payload="",
                            method_name_type="dj_query_route",
                        )
                    )
                for comp_name, comp in (
                    grid["component_templates"]
                    if "component_templates" in grid
                    else grid["components"]
                ).items():
                    if re.match(r"^table.*$", comp["type"]):
                        # For some reason the warnings package filters out deprecation
                        # warnings by default so make sure that filter is turned off
                        warnings.simplefilter("always", DeprecationWarning)
                        warnings.warn(
                            "table component to be Deprecated in next major release, "
                            + "please use antd-table",
                            DeprecationWarning,
                            stacklevel=2,
                        )
                    if re.match(
                        r"""^(
                            table|
                            antd-table|
                            metadata|
                            plot|
                            file|
                            slider|
                            dropdown-query|
                            form|
                            basicquery|
                            external|
                            slideshow|
                            delete
                            ).*$""",
                        comp["type"],
                        flags=re.VERBOSE,
                    ):
                        f.write(
                            (active_route_template).format(
                                route=comp["route"],
                                rest_verb=[type_map[comp["type"]].rest_verb[0]],
                                method_name=comp["route"].replace("/", ""),
                                component_type=comp["type"],
                                component_name=comp_name,
                                component=json.dumps(comp),
                                static_config=static_config,
                                payload=(
                                    "payload=request.get_json()"
                                    if comp["type"].split(":", 1)[0] == "form"
                                    else ""
                                ),
                                method_name_type="dj_query_route",
                            )
                        )
                        if issubclass(type_map[comp["type"]], InsertComponent):
                            fields_route = type_map[
                                comp["type"]
                            ].fields_route_format.format(route=comp["route"])
                            presets_route = type_map[
                                comp["type"]
                            ].presets_route_format.format(route=comp["route"])
                            f.write(
                                (active_route_template).format(
                                    route=fields_route,
                                    rest_verb=[InsertComponent.rest_verb[1]],
                                    method_name=fields_route.replace("/", ""),
                                    component_type=comp["type"],
                                    component_name=comp_name,
                                    component=json.dumps(comp),
                                    static_config=static_config,
                                    payload="payload=None",
                                    method_name_type="fields_route",
                                )
                            )
                            f.write(
                                (active_route_template).format(
                                    route=presets_route,
                                    rest_verb=[InsertComponent.rest_verb[1]],
                                    method_name=presets_route.replace("/", ""),
                                    component_type=comp["type"],
                                    component_name=comp_name,
                                    component=json.dumps(comp),
                                    static_config=static_config,
                                    payload="payload=None",
                                    method_name_type="presets_route",
                                )
                            )
                        elif issubclass(type_map[comp["type"]], TableComponent):
                            attributes_route = type_map[
                                comp["type"]
                            ].attributes_route_format.format(route=comp["route"])
                            uniques_route = type_map[
                                comp["type"]
                            ].uniques_route_format.format(route=comp["route"])
                            f.write(
                                (active_route_template).format(
                                    route=attributes_route,
                                    rest_verb=[TableComponent.rest_verb[0]],
                                    method_name=attributes_route.replace("/", ""),
                                    component_type=comp["type"],
                                    component_name=comp_name,
                                    component=json.dumps(comp),
                                    static_config=static_config,
                                    payload="",
                                    method_name_type="attributes_route",
                                )
                            )
                            f.write(
                                (active_route_template).format(
                                    route=uniques_route,
                                    rest_verb=[TableComponent.rest_verb[0]],
                                    method_name=uniques_route.replace("/", ""),
                                    component_type=comp["type"],
                                    component_name=comp_name,
                                    component=json.dumps(comp),
                                    static_config=static_config,
                                    payload="",
                                    method_name_type="uniques_route",
                                )
                            )
