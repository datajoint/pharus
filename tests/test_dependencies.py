from base64 import b64encode
from json import dumps
from . import SCHEMA_PREFIX, client, token, group1_token, connection, schemas_simple


def test_dependencies_admin(token, client, schemas_simple):
    schema_name = f'{SCHEMA_PREFIX}group1_simple'
    table_name = 'TableA'
    restriction = b64encode(dumps(dict(a_id=0)).encode('utf-8')).decode('utf-8')
    REST_dependencies = client.get(
        f"""/record/dependency?schemaName={
            schema_name}&tableName={table_name}&restriction={restriction}""",
        headers=dict(Authorization=f'Bearer {token}')).json['dependencies']
    REST_records = client.post('/fetch_tuples',
                               headers=dict(Authorization=f'Bearer {token}'),
                               json=dict(schemaName=schema_name,
                                         tableName=table_name)).json['tuples']
    assert len(REST_records) == 2
    assert len(REST_dependencies) == 4
    table_a = [el for el in REST_dependencies
               if (el['schema'] == f'{SCHEMA_PREFIX}group1_simple' and
                   'table_a' in el['table'])][0]
    assert table_a['accessible'] and table_a['count'] == 1
    table_b = [el for el in REST_dependencies
               if (el['schema'] == f'{SCHEMA_PREFIX}group1_simple'and
                   'table_b' in el['table'])][0]
    assert table_b['accessible'] and table_b['count'] == 2
    table_c = [el for el in REST_dependencies
               if (el['schema'] == f'{SCHEMA_PREFIX}group1_simple' and
                   'table_c' in el['table'])][0]
    assert table_c['accessible'] and table_c['count'] == 3
    diff_table_b = [el for el in REST_dependencies
                    if (el['schema'] == f'{SCHEMA_PREFIX}group2_simple' and
                        'diff_table_b' in el['table'])][0]
    assert diff_table_b['accessible'] and diff_table_b['count'] == 2
