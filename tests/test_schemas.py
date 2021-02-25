from . import (SCHEMA_PREFIX, client, token, connection, schemas_simple, schema_main,
               ParentPart)
import datajoint as dj


def test_schemas(token, client, connection, schemas_simple):
    REST_schemas = client.get('/list_schemas',
                              headers=dict(
                                  Authorization=f'Bearer {token}')).json['schemaNames']
    assert set(REST_schemas) == set(
        [s for s in dj.list_schemas(connection=connection)
         if s not in ('mysql', 'performance_schema', 'sys')])


def test_tables(token, client, ParentPart):
    ScanData, ProcessScanData = ParentPart
    REST_tables = client.post(
        '/list_tables',
        headers=dict(Authorization=f'Bearer {token}'),
        json=dict(schemaName=ScanData.database)).json['tableTypeAndNames']
    assert ScanData.__name__ == REST_tables['manual_tables'][0]
    assert ProcessScanData.__name__ == REST_tables['computed_tables'][0]
    assert f"""{ProcessScanData.__name__}.{
        ProcessScanData.ProcessScanDataPart.__name__}""" == REST_tables['part_tables'][0]
