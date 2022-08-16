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
        json=dict(
            a_id=2, a_name="Insert Test", b_id=32, b_number=1.23, c_id=400, c_int=99
        ),
        headers=dict(Authorization=f"Bearer {token}"),
    )
    assert REST_response.status_code == 200
    assert REST_response.data == b"Insert successful"
