from . import (
    SCHEMA_PREFIX,
    token,
    client,
    connection,
    schemas_simple,
)


def test_insert(token, client, connection, schemas_simple):
    REST_response = client.post(
        "/insert",
        json=dict(a_id=1, b_id=32, b_number=1.23, c_id=400, c_int=99),
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200
    assert REST_response.data == b"Insert successful"


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
