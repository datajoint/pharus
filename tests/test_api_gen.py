from . import SCHEMA_PREFIX, token, client, connection, schemas_simple, schema_main, Computer, group1_token,Student

def test_auto_generated_route(token, client, schemas_simple):
    REST_response = client.get(f'/query1', headers=dict(Authorization=f'Bearer {token}'))
    print('test')
    print(REST_response.data)
    assert False