from . import (
    SCHEMA_PREFIX,
    token,
    client,
    connection,
    schemas_simple,
)
import datajoint as dj


def test_insert(token, client, connection, schemas_simple):
    REST_response = client.post(
        "/insert",
        json=dict(a_id=1, b_id=32, b_number=1.23, c_id=400, c_int=99),
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200
    assert REST_response.data == b"Insert successful"


def test_insert_fail(token, client, connection, schemas_simple):
    REST_response = client.post(
        "/insert",
        json=dict(a_id=1, b_id=32, b_number=1.23, c_id=400),
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 500
    assert (
        dj.VirtualModule(schemas_simple[0].database, schemas_simple[0].database).TableB
        & "b_id = 32"
    ).fetch().size == 0


def test_form_response(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {"datatype": "int", "name": "B Id", "type": "attribute"},
            {"datatype": "float", "name": "B Number", "type": "attribute"},
            {"name": "Table A", "type": "table", "values": [{"A Id": 0}, {"A Id": 1}]},
            {"datatype": "int", "name": "C Id", "type": "attribute"},
            {"datatype": "int", "name": "c_int", "type": "attribute"},
        ],
    }


def test_form_response_no_table_map(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert2/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {"datatype": "int", "name": "B Id", "type": "attribute"},
            {"datatype": "float", "name": "B Number", "type": "attribute"},
            {"name": "Table A", "type": "table", "values": [{"a_id": 0}, {"a_id": 1}]},
            {"datatype": "int", "name": "C Id", "type": "attribute"},
            {"datatype": "int", "name": "c_int", "type": "attribute"},
        ],
    }


def test_form_response_no_map(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert3/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {"name": "TableA", "type": "table", "values": [{"a_id": 0}, {"a_id": 1}]},
            {"datatype": "int", "name": "b_id", "type": "attribute"},
            {"datatype": "float", "name": "b_number", "type": "attribute"},
            {"datatype": "int", "name": "c_id", "type": "attribute"},
            {"datatype": "int", "name": "c_int", "type": "attribute"},
        ],
    }


def test_form_response_no_map_shared_FK_hierarchy(
    token, client, connection, schemas_simple
):
    REST_response = client.get(
        "/insert4/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {"name": "TableA", "type": "table", "values": [{"a_id": 0}, {"a_id": 1}]},
            {"datatype": "int", "name": "bs_id", "type": "attribute"},
            {"datatype": "float", "name": "bs_number", "type": "attribute"},
            {
                "name": "TableB",
                "type": "table",
                "values": [
                    {"a_id": 0, "b_id": 10},
                    {"a_id": 0, "b_id": 11},
                    {"a_id": 1, "b_id": 21},
                ],
            },
            {"datatype": "int", "name": "c_id", "type": "attribute"},
            {"datatype": "int", "name": "c_int", "type": "attribute"},
        ],
    }


def test_form_response_no_map_shared_FK(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert5/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {"name": "TableA", "type": "table", "values": [{"a_id": 0}, {"a_id": 1}]},
            {"datatype": "int", "name": "b_id", "type": "attribute"},
            {"datatype": "float", "name": "b_number", "type": "attribute"},
            {"datatype": "int", "name": "bs_id", "type": "attribute"},
            {"datatype": "float", "name": "bs_number", "type": "attribute"},
        ],
    }


def test_form_response_no_map_diff_FK(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert6/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {
                "name": "DiffTableZ",
                "type": "table",
                "values": [{"zs_id": 0}, {"zs_id": 1}],
            },
            {"datatype": "int", "name": "y_id", "type": "attribute"},
            {"datatype": "float", "name": "y_number", "type": "attribute"},
            {"name": "TableZ", "type": "table", "values": [{"z_id": 0}, {"z_id": 1}]},
            {"datatype": "int", "name": "ys_id", "type": "attribute"},
            {"datatype": "float", "name": "ys_number", "type": "attribute"},
        ],
    }


def test_form_response_no_map_multi_FPK(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert7/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {
                "name": "TableX",
                "type": "table",
                "values": [
                    {"x_id": 0, "x_int": 10, "x_name": "Carlos"},
                    {"x_id": 1, "x_int": 20, "x_name": "Oscar"},
                ],
            },
            {"datatype": "int", "name": "w_id", "type": "attribute"},
            {"datatype": "int", "name": "w_int", "type": "attribute"},
        ],
    }


def test_form_response_no_map_many_tables(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert8/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {"name": "TableA", "type": "table", "values": [{"a_id": 0}, {"a_id": 1}]},
            {"datatype": "int", "name": "b_id", "type": "attribute"},
            {"datatype": "float", "name": "b_number", "type": "attribute"},
            {"datatype": "int", "name": "bs_id", "type": "attribute"},
            {"datatype": "float", "name": "bs_number", "type": "attribute"},
            {"datatype": "int", "name": "c_id", "type": "attribute"},
            {"datatype": "int", "name": "c_int", "type": "attribute"},
            {
                "name": "DiffTableZ",
                "type": "table",
                "values": [{"zs_id": 0}, {"zs_id": 1}],
            },
            {"datatype": "int", "name": "y_id", "type": "attribute"},
            {"datatype": "float", "name": "y_number", "type": "attribute"},
            {"name": "TableZ", "type": "table", "values": [{"z_id": 0}, {"z_id": 1}]},
            {"datatype": "int", "name": "ys_id", "type": "attribute"},
            {"datatype": "float", "name": "ys_number", "type": "attribute"},
            {
                "name": "TableX",
                "type": "table",
                "values": [
                    {"x_id": 0, "x_int": 10, "x_name": "Carlos"},
                    {"x_id": 1, "x_int": 20, "x_name": "Oscar"},
                ],
            },
            {"datatype": "int", "name": "w_id", "type": "attribute"},
            {"datatype": "int", "name": "w_int", "type": "attribute"},
        ],
    }
