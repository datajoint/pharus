from . import SCHEMA_PREFIX, token, client, connection, schemas_simple, schema_main, Computer, group1_token,Student
import json

def test_auto_generated_route(token, client, schemas_simple):
    REST_response1 = client.get(f'/query1', headers=dict(Authorization=f'Bearer {token}'))
    REST_response2 = client.get(f'/query2', headers=dict(Authorization=f'Bearer {token}'))
    REST_response3 = client.get(f'/query3', headers=dict(Authorization=f'Bearer {token}'))
    REST_response4 = client.get(f'/query4', headers=dict(Authorization=f'Bearer {token}'))
    
    expected_json = json.loads('[[1, 21, "Bernie", 7.77], [0, 10, "Raphael", 22.12], [0, 11, "Raphael", -1.21]]')

    assert expected_json == REST_response1.get_json(force=True)
    assert expected_json == REST_response2.get_json(force=True)
    assert expected_json == REST_response3.get_json(force=True)
    assert expected_json == REST_response4.get_json(force=True)
