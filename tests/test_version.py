from dj_gui_api_server import __version__ as version
import pytest
from dj_gui_api_server.DJGUIAPIServer import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_version(client):
    assert client.get('/api/version').data.decode() == version
