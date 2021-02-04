from dj_gui_api_server.DJConnector import DJConnector
from dj_gui_api_server.DJGUIAPIServer import login
from os import getenv, close, unlink
import pytest
from dj_gui_api_server.DJGUIAPIServer import app, run
import tempfile
import datajoint as dj


@pytest.fixture
def client():
    dj.config['safemode'] = False
    schema1 = dj.Schema('schema1')
    @schema1
    class TableA(dj.Manual):
        definition = """
        id: int
        ---
        name: varchar(30)
        """

    schema2 = dj.Schema('schema2')
    @schema2
    class TableB(dj.Manual):
        definition = """
        id: int
        ---
        number: float
        """

    with app.test_client() as client:
        yield client
        schema1.drop()
        schema2.drop()
        dj.config['safemode'] = True


@pytest.fixture
def token(client):
    yield client.post('/api/login', json=dict(databaseAddress=getenv('TEST_DB_SERVER'),
                                              username=getenv('TEST_DB_USER'),
                                              password=getenv('TEST_DB_PASS'))).json['jwt']


def test_connect():
    assert DJConnector.attempt_login(database_address=getenv('TEST_DB_SERVER'),
                                     username=getenv('TEST_DB_USER'),
                                     password=getenv('TEST_DB_PASS'))['result']


def test_login(token, client):
    schemas = client.get('/api/list_schemas',
                         headers=dict(Authorization=f'Bearer {token}')).json['schemaNames']
    assert 'schema1' in schemas and 'schema2' in schemas
