from . import SCHEMA_PREFIX, token, client, connection, schemas_simple
import json


def test_auto_generated_route(token, client, schemas_simple):
    # verify crawling over multiple grids
    # verify crawling over multiple components

    REST_response1 = client.get(f'/query1', headers=dict(Authorization=f'Bearer {token}'))
    REST_response2 = client.get(f'/query2', headers=dict(Authorization=f'Bearer {token}'))
    REST_response3 = client.get(f'/query3', headers=dict(Authorization=f'Bearer {token}'))
    REST_response4 = client.get(f'/query4', headers=dict(Authorization=f'Bearer {token}'))

    expected_json = (
        '[[0, 11, "Raphael", -1.21], [1, 21, "Bernie", 7.77], [0, 10, "Raphael", 22.12]]')

    print(json.dumps(REST_response1.get_json(force=True), sort_keys=True))

    assert expected_json == json.dumps(REST_response1.get_json(force=True), sort_keys=True)
    assert expected_json == json.dumps(REST_response2.get_json(force=True), sort_keys=True)
    assert expected_json == json.dumps(REST_response3.get_json(force=True), sort_keys=True)
    assert expected_json == json.dumps(REST_response4.get_json(force=True), sort_keys=True)
