import requests
from schul_cloud_resources_api_v1.rest import ApiException
from pytest import raises
import pytest
from schul_cloud_resources_server_tests.errors import errors as server_errors


def to_dict(model):
    """Return a dictionary."""
    if hasattr(model, "to_dict"):
        return model.to_dict()
    if hasattr(model, "json"):
        return model.json()
    return model


def assertIsResponse(response):
    response = to_dict(response)
    assert ("errors" in response) ^ ("data" in response), "The members data and errors MUST NOT coexist in the same document. http://jsonapi.org/format/#conventions"
    assert ("data" in response if "included" in response else True), "If a document does not contain a top-level data key, the included member MUST NOT be present either. http://jsonapi.org/format/#conventions"
    assert "jsonapi" in response, "jsonapi must be present, see the api specification."
    jsonapi = response["jsonapi"]
    for attr in ["name", "source", "description"]:
        assert attr in jsonapi, "{} must be present, see #/definition/Jsonapi".format(attr)
        assert isinstance(attr, str)


def assertIsError(response, status):
    """This is an error response object with a specific status code.

    You can view the specification here:
    - https://github.com/schul-cloud/resources-api-v1/blob/f0ce9acfde59563822071207bd176baf648db8b4/api-definition/swagger.yaml#L292
    - updated: https://github.com/schul-cloud/resources-api-v1/blob/master/api-definition/swagger.yaml#L292
    """
    response = to_dict(response)
    assertIsResponse(response)
    assert "errors" in response, "errors must be present"
    errors = response["errors"]
    assert isinstance(errors, list)
    assert len(errors) >= 1
    for error in errors:
        for attr in ["status", "title", "detail"]:
            assert attr in error, "#/definitions/ErrorElement"
        assert isinstance(error["status"], int), "#/definitions/ErrorElement"
        assert isinstance(error["title"], str), "#/definitions/ErrorElement"
        assert isinstance(error["detail"], str), "#/definitions/ErrorElement"
    error = errors[0]
    assert error["status"] == status
    assert error["title"] == server_errors[status]
    assert len(error["detail"]) > len(error["title"])


@step
def test_server_is_reachable(url):
    """There is a server behind the url."""
    result = requests.get(url)
    assert result.status_code


@step
def test_valid_is_not_invalid_resource(valid_resource, invalid_resource):
    """A resource can not be valid and invalid at the same time."""
    assert valid_resource != invalid_resource


@step
def test_add_a_resource_and_get_id(api, valid_resource):
    """When adding a resource, we should get an id back."""
    result = api.add_resource(valid_resource)
    assert isinstance(result.id, str)


@step
def test_add_a_resource_and_retrieve_it(api, valid_resource):
    """When we save a resource, we should be able to get it back."""
    result = api.add_resource(valid_resource)
    copy = api.get_resource(result.id)
    assert valid_resource == copy


@step
def test_there_are_at_least_two_valid_resources(valid_resources):
    """For the next tests, we will need two distinct valid resssources."""
    assert len(valid_resources) >= 2


@step
def test_add_two_different_resources(api, valid_resources):
    """When we post two different resources, we want the server to distinct them."""
    r1 = api.add_resource(valid_resources[0])
    c1_1 = api.get_resource(r1.id)
    r2 = api.add_resource(valid_resources[1])
    c2_1 = api.get_resource(r2.id)
    c1_2 = api.get_resource(r1.id)
    c2_2 = api.get_resource(r2.id)
    c1_3 = api.get_resource(r1.id)
    assert c1_1 == valid_resources[0], "see test_add_a_resource_and_retrieve_it"
    assert c1_2 == valid_resources[0]
    assert c1_3 == valid_resources[0]
    assert c2_1 == valid_resources[1]
    assert c2_2 == valid_resources[1]


@step
def test_deleted_resource_is_not_available(api, valid_resource):
    """If a client deleted a resource, this resource should be absent afterwards."""
    r1 = api.add_resource(valid_resource)
    api.delete_resource(r1.id)
    with raises(ApiException) as error:
        api.get_resource(r1.id)
    assert error.value.status == 404


@step
def test_list_of_resource_ids_is_a_list(api):
    """The list returned by the api should be a list if strings."""
    ids = api.get_resource_ids()
    assert all(isinstance(_id, str) for _id in ids)


@step
def test_new_resources_are_listed(api, valid_resource):
    """Posting new resources adds them their ids to the list of ids."""
    ids_before = api.get_resource_ids()
    r1 = api.add_resource(valid_resource)
    ids_after = api.get_resource_ids()
    new_ids = set(ids_after) - set(ids_before)
    assert r1.id in new_ids


@step
def test_resources_listed_can_be_accessed(api):
    """All the ids listed can be accessed."""
    ids = api.get_resource_ids()
    for _id in ids[:10]:
        api.get_resource(_id)


@step
def test_delete_all_resources_removes_resource(api):
    """After all resources are deleted, they can not be accessed any more."""
    ids = api.get_resource_ids()
    api.delete_resources()
    for _id in ids[:10]:
        with raises(ApiException) as error:
            api.get_resource(_id)
        assert error.value.status == 404


@step
def test_delete_resources_deletes_posted_resource(api, valid_resource):
    """A posted resource is deleted when all resources are deleted."""
    r1 = api.add_resource(valid_resource)
    api.delete_resources()
    with raises(ApiException) as error:
        api.get_resource(r1.id)
    assert error.value.status == 404


@step
def test_delete_resource_can_not_be_found_by_delete(api, valid_resource):
    """When a resource is deleted, it can not be found."""
    r1 = api.add_resource(valid_resource)
    api.delete_resource(r1.id)
    with raises(ApiException) as error:
        api.delete_resource(r1.id)
    assert error.value.status == 404


@step
def test_there_are_invalid_resources(api, invalid_resources):
    """Ensure that the tests have invalid resources to run with."""
    assert invalid_resources


@step
def test_unprocessible_entity_if_header_is_not_set(url):
    """If the Content-Type is not set to application/json, this is communicated.

    https://httpstatuses.com/415
    """
    response = requests.post(url + "/resources", data="{}")
    assert response.status_code == 415



@step
def test_bad_request_if_there_is_no_valid_json(url):
    """If the posted object is not a valid JSON, the server notices it.

    https://httpstatuses.com/400
    """
    response = requests.post(url + "/resources", data="invalid json", 
                             headers={"Content-Type":"application/json"})
    assert response.status_code == 400


@step
def test_invalid_resources_can_not_be_posted(api, invalid_resources):
    """If the resources do not fit in the schema, they cannot be posted.

    The error code 422 should be returned.
    https://httpstatuses.com/422
    """
    for invalid_resource in invalid_resources:
        with raises(ApiException) as error:
            api.add_resource(invalid_resource)
        assert error.value.status == 422, "Unprocessable Entity"


@step
def deleting_and_adding_a_resource_creates_a_new_id(api, valid_ressorce):
    """When a resource is added and deleted and added,
    the id of existing resources are not taken."""
    ids = [api.add_resource(valid_resource).id for i in range(4)]
    api.delete_resource(ids[1])
    r = api.add_resource(valid_resource)
    assert r.id not in ids


@step
def test_posting_and_deleting_a_resource_leaves_other_resource_intact(
        api, valid_resources):
    """When several ressoruces are posted, they are left intact if reposted."""
    ids = [api.add_resource(valid_resources[0]).id for i in range(4)]
    api.delete_resource(ids.pop(2))
    r = api.add_resource(valid_resources[1])
    for _id in ids:
        resource = api.get_resource(_id)
        assert resource == valid_resources[0]

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
    def test_cannot_cross_post(self, user1, user2, a_valid_resource):
        """Two disjoint users can not access each others objects."""
        ids = user2.api.get_resource_ids()
        for i in range(len(ids) + 1):
            r = user1.api.add_resource(a_valid_resource)
            if r.id not in ids:
                break
        else:
            assert False, "This isnot expected."
        ids = user2.api.get_resource_ids()
        assert r.id not in ids, "{} and {} must not access the same resources.".format(user1, user2)

    @step
    def test_cannot_cross_delete(self, user1, user2, a_valid_resource):
        """Two users can not delete each other's resources."""
        r = user1.api.add_resource(a_valid_resource)
        try:
            user2.api.delete_resource(r.id)
        except ApiException:
            pass
        resource = user1.api.get_resource(r.id)
        assert resource == a_valid_resource

    def assertSameIds(self, user1, user1_auth2):
        """Make sure the ids are the same."""
        ids1 = user1.api.get_resource_ids()
        ids2 = user1_auth2.api.get_resource_ids()
        assert ids1 == ids2

    @step
    def test_same_user_can_view_resources_with_different_auth(
            self, user1, user1_auth2, a_valid_resource):
        """Regardless of the authentication mechanism, the user can view 
        the resource."""
        self.assertSameIds(user1, user1_auth2)
        r = user1.api.add_resource(a_valid_resource)
        self.assertSameIds(user1, user1_auth2)
        user1_auth2.api.delete_resource(r.id)
        self.assertSameIds(user1, user1_auth2)

    @step
    @pytest.mark.parametrize("action", [
            lambda api, res: api.add_resource(res),
            lambda api, res: api.get_resource_ids(),
            lambda api, res: api.delete_resource("64682437"),
            lambda api, res: api.get_resource("tralala"),
            lambda api, res: api.delete_resources()
        ])
    def test_invalid_user_can_not_access_the_api(
            self, action, invalid_user, a_valid_resource):
        """The invalid user gets a 401 unauthorized all the time."""
        with raises(ApiException) as error:
            action(invalid_user.api, a_valid_resource)
        assert error.value.status == 401

    @step
    @pytest.mark.parametrize("header", [
            "api-key yek=aaaaaa", "api-key",
            "blablabla", "api-key key=aaaaaa,asd=asd"
        ])
    def test_unspecified_authorization_headers_yield_401(self, url, header):
        """"""
        result = requests.get(url + "/resources/ids",
                              headers={"Authorization": header})
        assert result.status_code == 401


class TestJsonApi:
    """Test that the api is conform to the JSON api.

    The specification can be found here: http://jsonapi.org/format/
    The JSON-api compatibility refers to
    - all requests
    - all responses including errors

    - Document structure http://jsonapi.org/format/#content-negotiation-clients
      - Content-Type: application/vnd.api+json
        - absence of this header
        - authentication comes after content type
        - negotiation of the absent header
        - error case
        - added media type parameters are errors 415 Unsupported Media Type
        - 406 Not Acceptable if client only sends application/vnd.api+json
        - Accept header
    """

    class TestUnsupportedMediaType:
        """
        Servers MUST respond with a 415 Unsupported Media Type status code 
        if a request specifies the header 
            Content-Type: application/vnd.api+json
        with any media type parameters.
        """

        INVALID_MEDIA_TYPES = [
                "", "application/jsonpip ", "application/vnd.api+json; version=1"
            ]

        @pytest.fixture(params=INVALID_MEDIA_TYPES)
        def response_to_invalid_request(self, request, request_with_headers):
            return request_with_headers({"Content-Type": request.param})

        @step
        def test_invalid_content_type_header_is_an_error(
                self, response_to_invalid_request):
            """Send possible requests to the server with a malformed header."""
            assertIsError(response_to_invalid_request, 415)

        @step
        def test_invalid_content_type_header_has_the_right_content_type(
                self, response_to_invalid_request):
            """Send possible requests to the server and set no header."""
            assert response_to_invalid_request.headers["Content-Type"] == "application/vnd.api+json"



