from . import SCHEMA_PREFIX, client, token, connection, schemas_simple


def test_definition(token, client, schemas_simple):
    simple1, simple2 = schemas_simple
    REST_definition = client.post('/get_table_definition',
                                  headers=dict(Authorization=f'Bearer {token}'),
                                  json=dict(schemaName=simple1.database,
                                            tableName='TableB')).data
    assert f'{simple1.database}.TableA' in REST_definition.decode('utf-8')

    REST_definition = client.post('/get_table_definition',
                                  headers=dict(Authorization=f'Bearer {token}'),
                                  json=dict(schemaName=simple2.database,
                                            tableName='DiffTableB')).data
    assert f'`{simple1.database}`.`#table_a`' in REST_definition.decode('utf-8')
