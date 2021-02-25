from . import SCHEMA_PREFIX, token, client, connection, schemas_simple
import datajoint as dj


def test_delete_dependent_with_cascade(token, client, connection, schemas_simple):
    schema_name = f'{SCHEMA_PREFIX}group1_simple'
    table_name = 'TableB'
    restriction = dict(a_id=0, b_id=11)
    vm = dj.VirtualModule('group1_simple', schema_name)
    print(getattr(vm, table_name) & restriction)
    REST_response = client.post(
        '/delete_tuple?cascade=tRuE',
        headers=dict(Authorization=f'Bearer {token}'),
        json=dict(schemaName=schema_name,
                  tableName=table_name,
                  restrictionTuple=restriction))
    assert REST_response.status_code == 200
    assert len(getattr(vm, table_name) & restriction) == 0
    assert len(getattr(vm, 'TableC') & restriction) == 0


def test_delete_dependent_without_cascade(token, client, connection, schemas_simple):
    schema_name = f'{SCHEMA_PREFIX}group1_simple'
    table_name = 'TableB'
    restriction = dict(a_id=0, b_id=11)
    vm = dj.VirtualModule('group1_simple', schema_name)
    REST_response = client.post(
        '/delete_tuple',
        headers=dict(Authorization=f'Bearer {token}'),
        json=dict(schemaName=schema_name,
                  tableName=table_name,
                  restrictionTuple=restriction))
    assert REST_response.status_code == 409
    assert REST_response.json['child_schema'] == f'{SCHEMA_PREFIX}group1_simple'
    assert REST_response.json['child_table'] == 'TableC'
    assert len(getattr(vm, table_name) & restriction) == 1
    assert len(getattr(vm, 'TableC') & restriction) == 2


def test_delete_independent_without_cascade(token, client, connection, schemas_simple):
    schema_name = f'{SCHEMA_PREFIX}group1_simple'
    table_name = 'TableB'
    restriction = dict(a_id=1, b_id=21)
    vm = dj.VirtualModule('group1_simple', schema_name)
    REST_response = client.post(
        '/delete_tuple?cascade=fAlSe',
        headers=dict(Authorization=f'Bearer {token}'),
        json=dict(schemaName=schema_name,
                  tableName=table_name,
                  restrictionTuple=restriction))
    assert REST_response.status_code == 200
    assert len(getattr(vm, table_name) & restriction) == 0


def test_delete_invalid(token, client, connection, schemas_simple):
    schema_name = f'{SCHEMA_PREFIX}group1_simple'
    table_name = 'TableB'
    restriction = dict()
    vm = dj.VirtualModule('group1_simple', schema_name)
    REST_response = client.post(
        '/delete_tuple?cascade=TRUE',
        headers=dict(Authorization=f'Bearer {token}'),
        json=dict(schemaName=schema_name,
                  tableName=table_name,
                  restrictionTuple=restriction))
    assert REST_response.status_code == 500
    assert b'Restriction is invalid' in REST_response.data
    assert len(getattr(vm, table_name)()) == 3
