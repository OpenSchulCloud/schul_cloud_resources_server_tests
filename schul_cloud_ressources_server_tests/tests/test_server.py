import requests


def test_server_is_reachable(url):
    result = requests.get(url)
    assert result.status_code == 404


def test_valid_is_not_invalid_ressource(valid_ressource, invalid_ressource):
    assert valid_ressource != invalid_ressource


def test_add_a_ressource_and_get_id(api, valid_ressource):
    """When adding a ressource, we should get an id back."""
    result = api.add_ressource(valid_ressource)
    assert isinstance(result.id, str)


def test_add_a_ressource_and_retrieve_it(api, valid_ressource):
    """When we save a ressource, we should be able to get it back."""
    result = api.add_ressource(valid_ressource)
    copy = api.get_ressource(result.id)
    assert valid_ressource == copy