from nautilus_api import __version__ as version
import pytest
from nautilus_api.server import app
from nautilus_api.interface import DJConnector
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
