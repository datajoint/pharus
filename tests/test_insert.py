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


def test_form(token, client, connection, schemas_simple):
    REST_response = client.get(
        "/insert/fields",
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200
    assert REST_response.get_json() == dict(fields=["test1", "test2"])
