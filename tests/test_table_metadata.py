from . import SCHEMA_PREFIX, client, token, connection, schemas_simple


def test_definition(token, client, schemas_simple):
    simple1, simple2 = schemas_simple
    REST_definition = client.get(
        f'/schema/{simple1.database}/table/{"TableB"}/definition',
        headers=dict(Authorization=f'Bearer {token}')).data
    assert f'{simple1.database}.TableA' in REST_definition.decode('utf-8')

    REST_definition = client.get(
        f'/schema/{simple2.database}/table/{"DiffTableB"}/definition',
        headers=dict(Authorization=f'Bearer {token}')).data
    assert f'`{simple1.database}`.`#table_a`' in REST_definition.decode('utf-8')
