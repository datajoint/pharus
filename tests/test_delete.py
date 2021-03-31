from . import SCHEMA_PREFIX, token, client, connection, schemas_simple
import datajoint as dj
from json import dumps
from base64 import b64encode
from urllib.parse import urlencode


def test_delete_dependent_with_cascade(token, client, connection, schemas_simple):
    schema_name = f'{SCHEMA_PREFIX}group1_simple'
    table_name = 'TableB'
    restriction = dict(a_id=0, b_id=11)
    filters = [dict(attributeName=k, operation='=', value=v)
               for k, v in restriction.items()]
    encoded_filters = b64encode(dumps(filters).encode('utf-8')).decode('utf-8')
    q = dict(cascade='tRuE', restriction=encoded_filters)
    vm = dj.VirtualModule('group1_simple', schema_name)
    REST_response = client.delete(
        f'/schema/{schema_name}/table/{table_name}/record?{urlencode(q)}',
        headers=dict(Authorization=f'Bearer {token}'))
    assert REST_response.status_code == 200
    assert len(getattr(vm, table_name) & restriction) == 0
    assert len(getattr(vm, 'TableC') & restriction) == 0


def test_delete_dependent_without_cascade(token, client, connection, schemas_simple):
    schema_name = f'{SCHEMA_PREFIX}group1_simple'
    table_name = 'TableB'
    restriction = dict(a_id=0, b_id=11)
    filters = [dict(attributeName=k, operation='=', value=v)
               for k, v in restriction.items()]
    encoded_filters = b64encode(dumps(filters).encode('utf-8')).decode('utf-8')
    q = dict(restriction=encoded_filters)
    vm = dj.VirtualModule('group1_simple', schema_name)
    REST_response = client.delete(
        f'/schema/{schema_name}/table/{table_name}/record?{urlencode(q)}',
        headers=dict(Authorization=f'Bearer {token}'))
    assert REST_response.status_code == 409
    assert REST_response.json['childSchema'] == f'{SCHEMA_PREFIX}group1_simple'
    assert REST_response.json['childTable'] == 'TableC'
    assert len(getattr(vm, table_name) & restriction) == 1
    assert len(getattr(vm, 'TableC') & restriction) == 2


def test_delete_independent_without_cascade(token, client, connection, schemas_simple):
    schema_name = f'{SCHEMA_PREFIX}group1_simple'
    table_name = 'TableB'
    restriction = dict(a_id=1, b_id=21)
    filters = [dict(attributeName=k, operation='=', value=v)
               for k, v in restriction.items()]
    encoded_filters = b64encode(dumps(filters).encode('utf-8')).decode('utf-8')
    q = dict(cascade='fAlSe', restriction=encoded_filters)
    vm = dj.VirtualModule('group1_simple', schema_name)
    REST_response = client.delete(
        f'/schema/{schema_name}/table/{table_name}/record?{urlencode(q)}',
        headers=dict(Authorization=f'Bearer {token}'))
    assert REST_response.status_code == 200
    assert len(getattr(vm, table_name) & restriction) == 0


def test_delete_invalid(token, client, connection, schemas_simple):
    schema_name = f'{SCHEMA_PREFIX}group1_simple'
    table_name = 'TableB'
    restriction = dict(a_id=999)
    filters = [dict(attributeName=k, operation='=', value=v)
               for k, v in restriction.items()]
    encoded_filters = b64encode(dumps(filters).encode('utf-8')).decode('utf-8')
    q = dict(cascade='TRUE', restriction=encoded_filters)
    vm = dj.VirtualModule('group1_simple', schema_name)
    REST_response = client.delete(
        f'/schema/{schema_name}/table/{table_name}/record?{urlencode(q)}',
        headers=dict(Authorization=f'Bearer {token}'))
    assert REST_response.status_code == 500
    assert b'Nothing to delete' in REST_response.data
    assert len(getattr(vm, table_name)()) == 3
