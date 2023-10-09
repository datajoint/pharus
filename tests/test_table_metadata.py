from . import (
    SCHEMA_PREFIX,
    client,
    token,
    connection,
    schemas_simple,
    schema_main,
    ParentPart,
)


def test_definition(token, client, schemas_simple):
    simple1, simple2 = schemas_simple
    REST_definition = client.get(
        f'/schema/{simple1.database}/table/{"TableB"}/definition',
        headers=dict(Authorization=f"Bearer {token}"),
    ).data
    assert f"{simple1.database}.TableA" in REST_definition.decode("utf-8")

    REST_definition = client.get(
        f'/schema/{simple2.database}/table/{"DiffTableB"}/definition',
        headers=dict(Authorization=f"Bearer {token}"),
    ).data
    assert f"`{simple1.database}`.`#table_a`" in REST_definition.decode("utf-8")


def test_definition_part_table(token, client, ParentPart):
    ScanData, ProcessScanData = ParentPart

    # Test Parent
    REST_value = client.get(
        f"/schema/{ScanData.database}/table/{ProcessScanData.__name__}/definition",
        headers=dict(Authorization=f"Bearer {token}"),
    ).data

    assert f"{ScanData.database}.ScanData" in REST_value.decode("utf-8")

    # Test Child
    REST_value = client.get(
        f"""/schema/{ProcessScanData.database}/table/{
            ProcessScanData.__name__ + '.' +
            ProcessScanData.ProcessScanDataPart.__name__}/definition""",
        headers=dict(Authorization=f"Bearer {token}"),
    ).data

    assert f"{ProcessScanData.database}.ProcessScanData" in REST_value.decode("utf-8")
