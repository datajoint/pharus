from . import (
    client,
    token,
    connection,
    schemas_simple,
    schema_main,
    ParentPart,
)
import datajoint as dj


def test_schemas(token, client, connection, schemas_simple):
    REST_schemas = client.get(
        "/schema", headers=dict(Authorization=f"Bearer {token}")
    ).json["schemaNames"]
    assert set(REST_schemas) == set(
        [
            s
            for s in dj.list_schemas(connection=connection)
            if s not in ("mysql", "performance_schema", "sys")
        ]
    )
