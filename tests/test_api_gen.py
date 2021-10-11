from . import SCHEMA_PREFIX, token, client, connection, schemas_simple
import json


def test_auto_generated_route(token, client, schemas_simple):

    # verify crawling over multiple grids
    REST_response1 = client.get('/query1', headers=dict(Authorization=f'Bearer {token}'))
    REST_response2 = client.get('/query2', headers=dict(Authorization=f'Bearer {token}'))
    # verify crawling over multiple components
    REST_response3 = client.get('/query3', headers=dict(Authorization=f'Bearer {token}'))
    REST_response4 = client.get('/query4', headers=dict(Authorization=f'Bearer {token}'))

    expected_json = (
        '[[0, 11, "Raphael", -1.21], [1, 21, "Bernie", 7.77], [0, 10, "Raphael", 22.12]]')

    print(json.dumps(REST_response1.get_json(force=True), sort_keys=True))

    assert expected_json == json.dumps(REST_response1.get_json(force=True), sort_keys=True)
    assert expected_json == json.dumps(REST_response2.get_json(force=True), sort_keys=True)
    assert expected_json == json.dumps(REST_response3.get_json(force=True), sort_keys=True)
    assert expected_json == json.dumps(REST_response4.get_json(force=True), sort_keys=True)


def test_get_attributes(token, client, schemas_simple):
    REST_response1 = client.get('/query1/attributes',
                                headers=dict(Authorization=f'Bearer {token}'))

    print(REST_response1.get_json())
    expected_json = {'attributeHeaders': ['name', 'type', 'nullable',
                                          'default', 'autoincrement'],
                     'attributes': {'primary': [['a_id', 'int', False, None, False],
                                                ['b_id', 'int', False, None, False]],
                                    'secondary': [['a_name', 'varchar(30)',
                                                   False, None, False],
                                                  ['b_number', 'float', False, None, False]]}}

    assert expected_json == REST_response1.get_json()
