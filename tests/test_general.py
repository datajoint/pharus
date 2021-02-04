from dj_gui_api_server import __version__ as version
import pytest
from dj_gui_api_server.DJGUIAPIServer import app
from dj_gui_api_server.DJConnector import DJConnector
from os import getenv


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_version(client):
    assert client.get('/api/version').data.decode() == version


def test_connect():
    assert DJConnector.attempt_login(database_address=getenv('TEST_DB_SERVER'),
                                     username=getenv('TEST_DB_USER'),
                                     password=getenv('TEST_DB_PASS'))['result']
