import requests
from schul_cloud_ressources_api_v1.rest import ApiException
from pytest import raises
import pytest

@step
def test_server_is_reachable(url):
    """There is a server behind the url."""
    result = requests.get(url)
    assert result.status_code


@step
def test_valid_is_not_invalid_ressource(valid_ressource, invalid_ressource):
    """A ressource can not be valid and invalid at the same time."""
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


@step
def test_delete_ressource_can_not_be_found_by_delete(api, valid_ressource):
    """When a ressource is deleted, it can not be found."""
    r1 = api.add_ressource(valid_ressource)
    api.delete_ressource(r1.id)
    with raises(ApiException) as error:
        api.delete_ressource(r1.id)
    assert error.value.status == 404


@step
def test_there_are_invalid_ressources(api, invalid_ressources):
    """Ensure that the tests have invalid ressources to run with."""
    assert invalid_ressources


@step
def test_unprocessible_entity_if_header_is_not_set(url):
    """If the Content-Type is not set to application/json, this is communicated.

    https://httpstatuses.com/415
    """
    response = requests.post(url + "/ressources", data="{}")
    assert response.status_code == 415



@step
def test_bad_request_if_there_is_no_valid_json(url):
    """If the posted object is not a valid JSON, the server notices it.

    https://httpstatuses.com/400
    """
    response = requests.post(url + "/ressources", data="invalid json", 
                             headers={"Content-Type":"application/json"})
    assert response.status_code == 400


@step
def test_invalid_ressources_can_not_be_posted(api, invalid_ressources):
    """If the ressources do not fit in the schema, they cannot be posted.

    The error code 422 should be returned.
    https://httpstatuses.com/422
    """
    for invalid_ressource in invalid_ressources:
        with raises(ApiException) as error:
            api.add_ressource(invalid_ressource)
        assert error.value.status == 422, "Unprocessable Entity"


@step
def deleting_and_adding_a_ressource_creates_a_new_id(api, valid_ressorce):
    """When a ressource is added and deleted and added,
    the id of existing ressources are not taken."""
    ids = [api.add_ressource(valid_ressource).id for i in range(4)]
    api.delete_ressource(ids[1])
    r = api.add_ressource(valid_ressource)
    assert r.id not in ids


@step
def test_posting_and_deleting_a_ressource_leaves_other_ressource_intact(
        api, valid_ressources):
    """When several ressoruces are posted, they are left intact if reposted."""
    ids = [api.add_ressource(valid_ressources[0]).id for i in range(4)]
    api.delete_ressource(ids.pop(2))
    r = api.add_ressource(valid_ressources[1])
    for _id in ids:
        ressource = api.get_ressource(_id)
        assert ressource == valid_ressources[0]

ERROR_NEED_MORE_CREDENTIALS = "Please pass additional authentication arguments."


class TestAuthentication:
    """Test the authentication mechanism.

    This includes:

    - different users can not see eachother
    - same users can post with different authentication machanisms
    - unauthenticated user can not see anything from other users
    - invalid username, password, api key
    - malformed Authorize header
    - empty username, password, api key
    """

    @step
    def test_user_provided_credentials(self, all_credentials):
        """To make the tests work, the user should provide credentials."""
        assert len(all_credentials) >= 2, ERROR_NEED_MORE_CREDENTIALS

    @step
    class TestTest:
        """Test the tests"""

        def test_users_are_always_unequal(self, user1, user2):
            """user1 and user2 are never the same."""
            assert user1.name != user2.name
            assert user1.credentials != user2.credentials

        def test_different_auths_have_the_same_name(self, user1, user1_auth2):
            """user1 is the same user as user1_auth2 but uses a different
            authentication mechanism"""
            assert user1.name == user1_auth2.name
            assert user1.credentials != user1_auth2.credentials

    @step
    def test_cannot_cross_post(self, user1, user2, a_valid_ressource):
        """Two disjoint users can not access each others objects."""
        ids = user2.api.get_ressource_ids()
        for i in range(len(ids) + 1):
            r = user1.api.add_ressource(a_valid_ressource)
            if r.id not in ids:
                break
        else:
            assert False, "This isnot expected."
        ids = user2.api.get_ressource_ids()
        assert r.id not in ids, "{} and {} must not access the same resources.".format(user1, user2)

    @step
    def test_cannot_cross_delete(self, user1, user2, a_valid_ressource):
        """Two users can not delete each other's ressources."""
        r = user1.api.add_ressource(a_valid_ressource)
        try:
            user2.api.delete_ressource(r.id)
        except ApiException:
            pass
        ressource = user1.api.get_ressource(r.id)
        assert ressource == a_valid_ressource

    def assertSameIds(self, user1, user1_auth2):
        """Make sure the ids are the same."""
        ids1 = user1.api.get_ressource_ids()
        ids2 = user1_auth2.api.get_ressource_ids()
        assert ids1 == ids2

    @step
    def test_same_user_can_view_ressources_with_different_auth(
            self, user1, user1_auth2, a_valid_ressource):
        """Regardless of the authentication mechanism, the user can view 
        the ressource."""
        self.assertSameIds(user1, user1_auth2)
        r = user1.api.add_ressource(a_valid_ressource)
        self.assertSameIds(user1, user1_auth2)
        user1_auth2.api.delete_ressource(r.id)
        self.assertSameIds(user1, user1_auth2)

    @step
    @pytest.mark.parametrize("action", [
            lambda api, res: api.add_ressource(res),
            lambda api, res: api.get_ressource_ids(),
            lambda api, res: api.delete_ressource("64682437"),
            lambda api, res: api.get_ressource("tralala"),
            lambda api, res: api.delete_ressources()
        ])
    def test_invalid_user_can_not_access_the_api(
            self, action, invalid_user, a_valid_ressource):
        """The invalid user gets a 401 unauthorized all the time."""
        with raises(ApiException) as error:
            action(invalid_user.api, a_valid_ressource)
        assert error.value.status == 401

    @step
    @pytest.mark.parametrize("header", [
            "api-key yek=aaaaaa", "api-key",
            "blablabla", "api-key key=aaaaaa,asd=asd"
        ])
    def test_unspecified_authorization_headers_yield_401(self, url, header):
        """"""
        result = requests.get(url + "/ressources/ids",
                              headers={"Authorization": header})
        assert result.status_code == 401
