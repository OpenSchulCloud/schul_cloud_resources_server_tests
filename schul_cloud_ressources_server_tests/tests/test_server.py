import requests


def test_server_is_there(ressources_server):
    """Test that the server is there."""
    requests.get(ressources_server.url)


def test_server_works_on_data(ressources_server, valid_ressource):
    """Test that the api adds a ressource."""
    ressources_server.api.add_ressource(valid_ressource)
    assert ressources_server.get_ressources() == [valid_ressource]


# this must be the last test
def test_server_stops(ressources_server):
    """Test that the server stops in the end."""
    requests.get(ressources_server.url)
    