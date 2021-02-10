from os import getenv
import pytest
from dj_gui_api_server.DJGUIAPIServer import app
import datajoint as dj
from base64 import b64encode
from json import dumps


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


@pytest.fixture
def token(client):
    yield client.post('/api/login', json=dict(databaseAddress=getenv('TEST_DB_SERVER'),
                                              username=getenv('TEST_DB_USER'),
                                              password=getenv('TEST_DB_PASS'))).json['jwt']


@pytest.fixture
def connection():
    dj.config['safemode'] = False
    connection = dj.conn(host=getenv('TEST_DB_SERVER'),
                         user=getenv('TEST_DB_USER'),
                         password=getenv('TEST_DB_PASS'), reset=True)
    connection.query("""
                     CREATE USER IF NOT EXISTS 'underprivileged'@'%%'
                     IDENTIFIED BY 'datajoint';
                     """)
    connection.query("GRANT ALL PRIVILEGES ON `deps`.* TO 'underprivileged'@'%%';")
    deps_secret = dj.VirtualModule('deps_secret', 'deps_secret', create_tables=True)
    deps = dj.VirtualModule('deps', 'deps', create_tables=True)
    @deps.schema
    class TableA(dj.Lookup):
        definition = """
        a_id: int
        ---
        a_name: varchar(30)
        """
        contents = [(0, 'Raphael',), (1, 'Bernie',)]

    @deps.schema
    class TableB(dj.Lookup):
        definition = """
        -> TableA
        b_id: int
        ---
        b_number: float
        """
        contents = [(0, 10, 22.12), (0, 11, -1.21,), (1, 21, 7.77,)]
    deps = dj.VirtualModule('deps', 'deps', create_tables=True)

    @deps_secret.schema
    class DiffTableB(dj.Lookup):
        definition = """
        -> deps.TableA
        bs_id: int
        ---
        bs_number: float
        """
        contents = [(0, -10, -99.99), (0, -11, 287.11,)]

    @deps.schema
    class TableC(dj.Lookup):
        definition = """
        -> TableB
        c_id: int
        ---
        c_int: int
        """
        contents = [(0, 10, 100, -8), (0, 11, 200, -9,), (0, 11, 300, -7,)]

    yield connection

    deps_secret.schema.drop()
    deps.schema.drop()
    connection.query("DROP USER 'underprivileged'@'%%';")
    connection.close()
    dj.config['safemode'] = True


@pytest.fixture
def underprivileged_token(client, connection):
    yield client.post('/api/login', json=dict(databaseAddress=getenv('TEST_DB_SERVER'),
                                              username='underprivileged',
                                              password='datajoint')).json['jwt']


def test_dependencies_underprivileged(underprivileged_token, client):
    schema_name = 'deps'
    table_name = 'TableA'
    restriction = b64encode(dumps(dict(a_id=0)).encode('utf-8')).decode('utf-8')
    REST_dependencies = client.get(
        f"""/api/record/dependency?schema_name={
            schema_name}&table_name={table_name}&restriction={restriction}""",
        headers=dict(Authorization=f'Bearer {underprivileged_token}')).json['dependencies']
    # print(REST_dependencies)
    assert len(REST_dependencies) == 4
    table_a = [el for el in REST_dependencies
               if el['schema'] == 'deps' and 'table_a' in el['table']][0]
    assert table_a['accessible'] and table_a['count'] == 1
    table_b = [el for el in REST_dependencies
               if el['schema'] == 'deps' and 'table_b' in el['table']][0]
    assert table_b['accessible'] and table_b['count'] == 2
    table_c = [el for el in REST_dependencies
               if el['schema'] == 'deps' and 'table_c' in el['table']][0]
    assert table_c['accessible'] and table_c['count'] == 3
    diff_table_b = [el for el in REST_dependencies
                    if el['schema'] == 'deps_secret' and 'diff_table_b' in el['table']][0]
    assert not diff_table_b['accessible']


def test_dependencies_admin(token, client, connection):
    schema_name = 'deps'
    table_name = 'TableA'
    restriction = b64encode(dumps(dict(a_id=0)).encode('utf-8')).decode('utf-8')
    REST_dependencies = client.get(
        f"""/api/record/dependency?schema_name={
            schema_name}&table_name={table_name}&restriction={restriction}""",
        headers=dict(Authorization=f'Bearer {token}')).json['dependencies']
    # print(REST_dependencies)
    assert len(REST_dependencies) == 4
    table_a = [el for el in REST_dependencies
               if el['schema'] == 'deps' and 'table_a' in el['table']][0]
    assert table_a['accessible'] and table_a['count'] == 1
    table_b = [el for el in REST_dependencies
               if el['schema'] == 'deps' and 'table_b' in el['table']][0]
    assert table_b['accessible'] and table_b['count'] == 2
    table_c = [el for el in REST_dependencies
               if el['schema'] == 'deps' and 'table_c' in el['table']][0]
    assert table_c['accessible'] and table_c['count'] == 3
    diff_table_b = [el for el in REST_dependencies
                    if el['schema'] == 'deps_secret' and 'diff_table_b' in el['table']][0]
    assert diff_table_b['accessible'] and diff_table_b['count'] == 2
