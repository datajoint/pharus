from base64 import b64encode
from urllib.parse import urlencode
from json import dumps
from . import SCHEMA_PREFIX, client, token, group1_token, connection, schemas_simple


def test_dependencies_admin(token, client, schemas_simple):
    schema_name = f'{SCHEMA_PREFIX}group1_simple'
    table_name = 'TableA'
    restriction = dict(a_id=0)
    restriction = [dict(attributeName=k, operation='=', value=v)
                   for k, v in restriction.items()]
    restriction = b64encode(dumps(restriction).encode('utf-8')).decode('utf-8')
    q = dict(restriction=restriction)
    REST_dependencies = client.get(
        f'/schema/{schema_name}/table/{table_name}/dependency?{urlencode(q)}',
        headers=dict(Authorization=f'Bearer {token}')).json['dependencies']
    REST_records = client.get(
        f'/schema/{schema_name}/table/{table_name}/record',
        headers=dict(Authorization=f'Bearer {token}')).json['records']
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
