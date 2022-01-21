from . import client, connection, token, schema_main, ParentPart
from flask.wrappers import Response
import datajoint as dj


def test_list_tables(token, client, ParentPart):
    ScanData, ProcessScanData = ParentPart
    REST_tables = client.get(
        f"/schema/{ScanData.database}/table",
        headers=dict(Authorization=f"Bearer {token}"),
    ).json["tableTypes"]
    assert ScanData.__name__ == REST_tables["manual"][0]
    assert ProcessScanData.__name__ == REST_tables["computed"][0]
    assert (
        f"""{ProcessScanData.__name__}.{
        ProcessScanData.ProcessScanDataPart.__name__}"""
        == REST_tables["part"][0]
    )


def test_invalid_schema_list_table(token, client, schema_main):
    # Test invalid schema
    response: Response = client.get(
        f'/schema/{"invalid_schema"}/table',
        headers=dict(Authorization=f"Bearer {token}"),
    )

    assert response.status_code != 200
    assert "invalid_schema" not in dj.list_schemas()
