from . import SCHEMA_PREFIX, token, client, connection, schemas_simple
from base64 import b64encode
import json
from os import environ
from envyaml import EnvYAML
from pathlib import Path


def test_spec_endpoint(token, client):
    REST_response = client.get("/spec", headers=dict(Authorization=f"Bearer {token}"))
    spec_path = environ.get("PHARUS_SPEC_PATH")
    assert EnvYAML(Path(spec_path))["SciViz"] == REST_response.get_json()


def test_auto_generated_route(token, client, schemas_simple):
    # verify crawling over multiple grids
    REST_response1 = client.get(
        "/query1", headers=dict(Authorization=f"Bearer {token}")
    )
    REST_response2 = client.get(
        "/query2", headers=dict(Authorization=f"Bearer {token}")
    )
    # verify crawling over multiple components
    REST_response3 = client.get(
        "/query3", headers=dict(Authorization=f"Bearer {token}")
    )
    REST_response4 = client.get(
        "/query4", headers=dict(Authorization=f"Bearer {token}")
    )

    expected_json = json.dumps(
        {
            "recordHeader": ["a_id", "b_id", "a_name", "b_number"],
            "records": [
                [0, 10, "Raphael", 22.12],
                [0, 11, "Raphael", -1.21],
                [1, 21, "Bernie", 7.77],
            ],
            "totalCount": 3,
        }
    )

    assert expected_json == json.dumps(REST_response1.get_json(), sort_keys=True)
    assert expected_json == json.dumps(REST_response2.get_json(), sort_keys=True)
    assert expected_json == json.dumps(REST_response3.get_json(), sort_keys=True)
    assert expected_json == json.dumps(REST_response4.get_json(), sort_keys=True)


def test_get_full_plot(token, client, schemas_simple):
    REST_response1 = client.get("/plot1", headers=dict(Authorization=f"Bearer {token}"))
    expected_json = json.dumps(
        dict(
            data=[
                dict(
                    x=[1, 2, 3],
                    y=[2, 6, 3],
                    type="scatter",
                    mode="lines+markers",
                    marker=dict(color="red"),
                ),
                dict(type="bar", x=[1, 2, 3], y=[2, 5, 3]),
            ],
            layout=dict(title="A Fancy Plot"),
        ),
        sort_keys=True,
    )
    assert expected_json == json.dumps(REST_response1.get_json(), sort_keys=True)


def test_get_attributes(token, client, schemas_simple):
    REST_response = client.get(
        "/query1/attributes", headers=dict(Authorization=f"Bearer {token}")
    )

    expected_json = {
        "attributeHeaders": ["name", "type", "nullable", "default", "autoincrement"],
        "attributes": {
            "primary": [
                [
                    "a_id",
                    "int",
                    False,
                    None,
                    False,
                    None,
                ],
                [
                    "b_id",
                    "int",
                    False,
                    None,
                    False,
                    None,
                ],
            ],
            "secondary": [
                [
                    "a_name",
                    "varchar(30)",
                    False,
                    None,
                    False,
                    None,
                ],
                [
                    "b_number",
                    "float",
                    False,
                    None,
                    False,
                    None,
                ],
            ],
        },
    }

    assert expected_json == REST_response.get_json()


def test_get_uniques(token, client, schemas_simple):
    REST_response = client.get(
        "/query1/uniques", headers=dict(Authorization=f"Bearer {token}")
    )

    expected_json = {
        "unique_values": {
            "primary": [
                [
                    [{"text": "0", "value": 0}, {"text": "1", "value": 1}],
                ],
                [
                    [
                        {"text": "10", "value": 10},
                        {"text": "11", "value": 11},
                        {"text": "21", "value": 21},
                    ]
                ],
            ],
            "secondary": [
                [
                    [
                        {"text": "Raphael", "value": "Raphael"},
                        {"text": "Bernie", "value": "Bernie"},
                    ],
                ],
                [
                    [
                        {"text": "22.12", "value": 22.12},
                        {"text": "-1.21", "value": -1.21},
                        {"text": "7.77", "value": 7.77},
                    ],
                ],
            ],
        },
    }

    assert expected_json == REST_response.get_json()


def test_dynamic_restriction(token, client, schemas_simple):
    REST_response = client.get("/query5", headers=dict(Authorization=f"Bearer {token}"))
    # should restrict in the spec sheet by a_id=0
    expected_json = json.dumps(
        {
            "recordHeader": ["a_id", "b_id", "a_name", "b_number"],
            "records": [[0, 10, "Raphael", 22.12], [0, 11, "Raphael", -1.21]],
            "totalCount": 2,
        }
    )
    assert expected_json == json.dumps(REST_response.get_json(), sort_keys=True)


def test_fetch_restriction(token, client, schemas_simple):
    restriction = [{"attributeName": "a_id", "operation": "=", "value": 1}]
    encoded = b64encode(json.dumps(restriction).encode("utf-8"))
    REST_response = client.get(
        f"/query1?restriction={encoded.decode()}",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    # should restrict in the query parameter by a_id=1
    expected_json = json.dumps(
        {
            "recordHeader": ["a_id", "b_id", "a_name", "b_number"],
            "records": [
                [1, 21, "Bernie", 7.77],
            ],
            "totalCount": 1,
        }
    )
    assert expected_json == json.dumps(REST_response.get_json(), sort_keys=True)
