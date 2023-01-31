from . import (
    SCHEMA_PREFIX,
    token,
    client,
    connection,
    schemas_simple,
)
import datajoint as dj


def test_insert_map(token, client, connection, schemas_simple):
    REST_response = client.post(
        "/insert",
        json={
            "submissions": [
                {"A Id": 1, "B Id": 32, "B Number": 1.23, "C Id": 400, "c_name": "John"}
            ]
        },
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, REST_response.data
    assert REST_response.get_json() == {"response": "Insert Successful"}


def test_insert_no_map(token, client, connection, schemas_simple):
    REST_response = client.post(
        "/insert3?group=test_group1",
        json={
            "submissions": [
                {
                    "a_id": 1,
                    "b_id": 32,
                    "b_number": 1.23,
                    "c_id": 400,
                    "c_name": "Smith",
                }
            ]
        },
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200
    assert REST_response.get_json() == {"response": "Insert Successful"}


def test_insert_fail(token, client, connection, schemas_simple):
    REST_response = client.post(
        "/insert3?group=test_group1",
        json={"submissions": [{"a_id": 1, "b_id": 32, "b_number": 1.23}]},
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 500
    assert (
        dj.VirtualModule(
            schemas_simple[0].database,
            schemas_simple[0].database,
            connection=connection,
        ).TableB
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
            {"datatype": "int", "name": "B Id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "B Number",
                "type": "attribute",
                "default": None,
            },
            {
                "name": "Table A",
                "type": "table",
                "values": ['{"A Id": 0}', '{"A Id": 1}'],
            },
            {"datatype": "int", "name": "C Id", "type": "attribute", "default": None},
            {
                "datatype": "varchar(30)",
                "name": "c_name",
                "type": "attribute",
                "default": '"John Smith"',
            },
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
            {"datatype": "int", "name": "B Id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "B Number",
                "type": "attribute",
                "default": None,
            },
            {
                "name": "Table A",
                "type": "table",
                "values": ['{"a_id": 0}', '{"a_id": 1}'],
            },
            {"datatype": "int", "name": "C Id", "type": "attribute", "default": None},
            {
                "datatype": "varchar(30)",
                "name": "c_name",
                "type": "attribute",
                "default": '"John Smith"',
            },
        ],
    }


def test_form_response_no_map(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert3/fields?group=test_group1",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {
                "name": "test_group1_simple.TableA",
                "type": "table",
                "values": ['{"a_id": 0}', '{"a_id": 1}'],
            },
            {"datatype": "int", "name": "b_id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "b_number",
                "type": "attribute",
                "default": None,
            },
            {"datatype": "int", "name": "c_id", "type": "attribute", "default": None},
            {
                "datatype": "varchar(30)",
                "name": "c_name",
                "type": "attribute",
                "default": '"John Smith"',
            },
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
            {
                "name": "test_group1_simple.TableA",
                "type": "table",
                "values": ['{"a_id": 0}', '{"a_id": 1}'],
            },
            {
                "name": "test_group1_simple.TableB",
                "type": "table",
                "values": [
                    '{"a_id": 0, "b_id": 10}',
                    '{"a_id": 0, "b_id": 11}',
                    '{"a_id": 1, "b_id": 21}',
                ],
            },
            {"datatype": "int", "name": "bs_id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "bs_number",
                "type": "attribute",
                "default": None,
            },
            {"datatype": "int", "name": "c_id", "type": "attribute", "default": None},
            {
                "datatype": "varchar(30)",
                "name": "c_name",
                "type": "attribute",
                "default": '"John Smith"',
            },
        ]
    }


def test_form_response_no_map_shared_FK(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert5/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {
                "name": "test_group1_simple.TableA",
                "type": "table",
                "values": ['{"a_id": 0}', '{"a_id": 1}'],
            },
            {"datatype": "int", "name": "b_id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "b_number",
                "type": "attribute",
                "default": None,
            },
            {"datatype": "int", "name": "bs_id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "bs_number",
                "type": "attribute",
                "default": None,
            },
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
                "name": "test_group3_simple.TableZ",
                "type": "table",
                "values": ['{"z_id": 0}', '{"z_id": 1}'],
            },
            {
                "name": "test_group4_simple.DiffTableZ",
                "type": "table",
                "values": ['{"zs_id": 0}', '{"zs_id": 1}'],
            },
            {"datatype": "int", "name": "y_id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "y_number",
                "type": "attribute",
                "default": None,
            },
            {"datatype": "int", "name": "ys_id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "ys_number",
                "type": "attribute",
                "default": None,
            },
        ]
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
                "name": "test_group3_simple.TableX",
                "type": "table",
                "values": [
                    '{"x_id": 0, "x_name": "Carlos", "x_int": 10}',
                    '{"x_id": 1, "x_name": "Oscar", "x_int": 20}',
                ],
            },
            {"datatype": "int", "name": "w_id", "type": "attribute", "default": None},
            {"datatype": "int", "name": "w_int", "type": "attribute", "default": "123"},
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
            {
                "name": "test_group1_simple.TableA",
                "type": "table",
                "values": ['{"a_id": 0}', '{"a_id": 1}'],
            },
            {
                "name": "test_group3_simple.TableX",
                "type": "table",
                "values": [
                    '{"x_id": 0, "x_name": "Carlos", "x_int": 10}',
                    '{"x_id": 1, "x_name": "Oscar", "x_int": 20}',
                ],
            },
            {
                "name": "test_group3_simple.TableZ",
                "type": "table",
                "values": ['{"z_id": 0}', '{"z_id": 1}'],
            },
            {
                "name": "test_group4_simple.DiffTableZ",
                "type": "table",
                "values": ['{"zs_id": 0}', '{"zs_id": 1}'],
            },
            {"datatype": "int", "name": "b_id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "b_number",
                "type": "attribute",
                "default": None,
            },
            {"datatype": "int", "name": "bs_id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "bs_number",
                "type": "attribute",
                "default": None,
            },
            {"datatype": "int", "name": "c_id", "type": "attribute", "default": None},
            {
                "datatype": "varchar(30)",
                "name": "c_name",
                "type": "attribute",
                "default": '"John Smith"',
            },
            {"datatype": "int", "name": "y_id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "y_number",
                "type": "attribute",
                "default": None,
            },
            {"datatype": "int", "name": "ys_id", "type": "attribute", "default": None},
            {
                "datatype": "float",
                "name": "ys_number",
                "type": "attribute",
                "default": None,
            },
            {"datatype": "int", "name": "w_id", "type": "attribute", "default": None},
            {"datatype": "int", "name": "w_int", "type": "attribute", "default": "123"},
        ]
    }


def test_form_datetime_FPK(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert9/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200, f"Error: {REST_response.data}"
    assert REST_response.get_json() == {
        "fields": [
            {
                "name": "test_group4_simple.TableV",
                "type": "table",
                "values": [
                    '{"datetime": "2000-01-02T01:02:03", "v_int": 0}',
                    '{"datetime": "2023-12-01T23:12:01", "v_int": 1}',
                ],
            },
            {"datatype": "int", "default": "1", "name": "u_int", "type": "attribute"},
        ]
    }
