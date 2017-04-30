import requests
from schul_cloud_ressources_api_v1.rest import ApiException
from pytest import raises

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


@step
def test_deleted_ressource_is_not_available(api, valid_ressource):
    """If a client deleted a ressource, this ressource should be absent afterwards."""
    r1 = api.add_ressource(valid_ressource)
    api.delete_ressource(r1.id)
    with raises(ApiException) as error:
        api.get_ressource(r1.id)
    assert error.value.status == 404


@step
def test_list_of_ressource_ids_is_a_list(api):
    """The list returned by the api should be a list if strings."""
    ids = api.get_ressource_ids()
    assert all(isinstance(_id, str) for _id in ids)


@step
def test_new_resources_are_listed(api, valid_ressource):
    """Posting new ressources adds them their ids to the list of ids."""
    ids_before = api.get_ressource_ids()
    r1 = api.add_ressource(valid_ressource)
    ids_after = api.get_ressource_ids()
    new_ids = set(ids_after) - set(ids_before)
    assert r1.id in new_ids


@step
def test_ressources_listed_can_be_accessed(api):
    """All the ids listed can be accessed."""
    ids = api.get_ressource_ids()
    for _id in ids[:10]:
        api.get_ressource(_id)


@step
def test_delete_all_ressources_removes_ressource(api):
    """After all ressources are deleted, they can not be accessed any more."""
    ids = api.get_ressource_ids()
    api.delete_ressources()
    for _id in ids[:10]:
        with raises(ApiException) as error:
            api.get_ressource(_id)
        assert error.value.status == 404
    

@step
def test_delete_ressources_deletes_posted_ressource(api, valid_ressource):
    """A posted ressource is deleted when all ressources are deleted."""
    r1 = api.add_ressource(valid_ressource)
    api.delete_ressources()
    with raises(ApiException) as error:
        api.get_ressource(r1.id)
    assert error.value.status == 404

