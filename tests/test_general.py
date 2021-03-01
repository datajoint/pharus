from pharus import __version__ as version
from . import client


def test_version(client):
    assert client.get('/version').data.decode() == version
