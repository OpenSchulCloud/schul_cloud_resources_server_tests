import requests

@step
def test_server_is_reachable(url):
    result = requests.get(url)
    assert result.status_code


@step
def test_valid_is_not_invalid_ressource(valid_ressource, invalid_ressource):
    assert valid_ressource != invalid_ressource


@step
def test_add_a_ressource_and_get_id(api, valid_ressource):
    """When adding a ressource, we should get an id back."""
    result = api.add_ressource(valid_ressource)
    assert isinstance(result.id, str)


@step
def test_add_a_ressource_and_retrieve_it(api, valid_ressource):
    """When we save a ressource, we should be able to get it back."""
    result = api.add_ressource(valid_ressource)
    copy = api.get_ressource(result.id)
    assert valid_ressource == copy


@step
def test_there_are_at_least_two_valid_ressources(valid_ressources):
    """For the next tests, we will need two distinct valid resssources."""
    assert len(valid_ressources) >= 2


@step
def test_add_two_different_ressources(api, valid_ressources):
    """When we post two different ressources, we want the server to distinct them."""
    r1 = api.add_ressource(valid_ressources[0])
    c1_1 = api.get_ressource(r1.id)
    r2 = api.add_ressource(valid_ressources[1])
    c2_1 = api.get_ressource(r2.id)
    c1_2 = api.get_ressource(r1.id)
    c2_2 = api.get_ressource(r2.id)
    c1_3 = api.get_ressource(r1.id)
    assert c1_1 == valid_ressources[0], "see test_add_a_ressource_and_retrieve_it"
    assert c1_2 == valid_ressources[0]
    assert c1_3 == valid_ressources[0]
    assert c2_1 == valid_ressources[1]
    assert c2_2 == valid_ressources[1]

