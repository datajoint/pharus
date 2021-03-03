from . import client, connection, token, schema_main, ParentPart
from flask.wrappers import Response
import datajoint as dj

def test_list_tables(token, client, ParentPart):
    ScanData, ProcessScanData = ParentPart
    REST_tables = client.post(
        '/list_tables',
        headers=dict(Authorization=f'Bearer {token}'),
        json=dict(schemaName=ScanData.database)).json['tableTypeAndNames']
    assert ScanData.__name__ == REST_tables['manual_tables'][0]
    assert ProcessScanData.__name__ == REST_tables['computed_tables'][0]
    assert f"""{ProcessScanData.__name__}.{
        ProcessScanData.ProcessScanDataPart.__name__}""" == REST_tables['part_tables'][0]

def test_invalid_schema_list_table(token, client):
    # Test invalid schema
    response: Response = client.post(
        '/list_tables', 
        headers=dict(Authorization=f'Bearer {token}'),
        json=dict(schemaName='invalid_schema')
        )

    assert('Database `invalid_schema` has not yet been declared. Set argument create_schema=True to create it.' in response.get_data(as_text=True))