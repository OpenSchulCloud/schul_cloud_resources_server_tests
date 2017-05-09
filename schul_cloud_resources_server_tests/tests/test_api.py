import requests
from pytest import fixture, mark, raises, skip
from schul_cloud_resources_server_tests.tests.assertions import *
from schul_cloud_resources_api_v1.rest import ApiException


API_CONTENT_TYPE = "application/vnd.api+json"


def resource_dict(resource, **kw):
    kw.setdefault("attributes", resource)
    kw.setdefault("type", "resource")
    return {"data": kw}


@step
def test_server_is_reachable(url):
    """There is a server behind the url."""
    result = requests.get(url)
    assert result.status_code


@step
@mark.test
def test_valid_is_not_invalid_resource(valid_resource, invalid_resource):
    """A resource can not be valid and invalid at the same time.

    This  is a test that tests the test environment.
    If it fails, other tests may fail although the server works.
    """
    assert valid_resource != invalid_resource


class TestAddResource:
    """Test the endpoint for posting resources.

    - posting
    - response
    - links
    - location header
    """

    @fixture
    def add_resource_response(self, api, valid_resource):
        """Post a resource and get the response."""
        return api.add_resource(resource_dict(valid_resource))

    @step
    def test_get_resource_back(self, add_resource_response, valid_resource):
        """When we save a resource, we should be able to get information back."""
        assert add_resource_response.data.attributes == valid_resource

    @step
    def test_type_is_resource(self, add_resource_response):
        """The tpe must be set to "resource"."""
        assert add_resource_response.data.type == "resource"

    @step
    def test_self_link_links_to_resource(
            self, add_resource_response, valid_resource, user1):
        """Links are returned. The self link should point to the resource."""
        response = user1.get(add_resource_response.links.self)
        data = response.json()
        resource = data["data"]["attributes"]
        assert resource == valid_resource

    @step
    def test_location_header_is_set(self, user1, valid_resource, url):
        """Post a new resource and the the location header. wich should be teh self link.

        see http://jsonapi.org/format/#crud-creating
        """
        response = user1.post(url + "/resources",
                              headers={"Content-Type": API_CONTENT_TYPE},
                              json=resource_dict(valid_resource))
        assert response.headers["Location"] == response.json()["links"]["self"]


    @step
    @mark.parametrize("accept_header", ["*/*", "application/*", API_CONTENT_TYPE])
    def test_different_accept_headers(self, user1, valid_resource, url, accept_header):
        """Test that the accept header is one of "*/*", "application/*", API_CONTENT_TYPE.

        see https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
        """
        response = user1.post(url + "/resources",
                              headers={"Content-Type": API_CONTENT_TYPE,
                                       "Accept": accept_header},
                              json=resource_dict(valid_resource))
        assert response.status_code == 201
        

    @step
    @mark.parametrize("host", ["google.de", "schul-cloud.org"])
    def test_location_header_uses_host_header(self, user1, valid_resource, url, host):
        """Post a new resource and the the location header. Which should be the self link.

        see http://jsonapi.org/format/#crud-creating
        Additionally, use a different host header.
        """
        headers = ({"Host": host} if host else {})
        headers["Content-Type"] = API_CONTENT_TYPE
        response = user1.post(url + "/resources", headers=headers, json=resource_dict(valid_resource))
        location = response.headers["Location"].split("//", 1)[1]
        assert location.startswith(host)
        assert response.headers["Location"] == response.json()["links"]["self"]

    @step
    def test_creation_is_response(self, add_resource_response):
        """Make sure all required attributes are set."""
        assertIsResponse(add_resource_response)

    @step
    def test_result_id_is_a_string(self, add_resource_response):
        """The object id should be a string."""
        assert isinstance(add_resource_response.data.id, str)

    # TODO: add a test for the absent data attribute
    # TODO: add a test for a given id


class TestGetResources:
    """Get added resources back."""

    @step
    def test_add_a_resource_and_retrieve_it(self, api, valid_resource):
        """When we save a resource, we should be able to get it back."""
        result = api.add_resource(resource_dict(valid_resource))
        _id = result.data.id
        assert _id, "id should be in {}".format(result.to_dict())
        copy = api.get_resource(_id).data.attributes
        assert valid_resource == copy

    @step
    def test_ressource_id_is_there(self, api, valid_resource):
        """When a resource is retrieved, the id is sent with it."""
        result = api.add_resource(resource_dict(valid_resource))
        server_copy = api.get_resource(result.data.id)
        assert result.data.id == server_copy.data.id

    @step
    def test_ressource_type_is_set(self, api, valid_resource):
        """When a resource is retrieved, the type is sent with it."""
        result = api.add_resource(resource_dict(valid_resource))
        server_copy = api.get_resource(result.data.id)
        assert server_copy.data.type == "resource"

    @step
    def test_ressource_is_a_response(self, api, valid_resource):
        """When a resource is retrieved, the type is sent with it."""
        result = api.add_resource(resource_dict(valid_resource))
        server_copy = api.get_resource(result.data.id)
        assertIsResponse(server_copy)


@step
@mark.test
def test_there_are_at_least_two_valid_resources(valid_resources):
    """For the next tests, we will need two distinct valid resssources."""
    assert len(valid_resources) >= 2


@step
def test_add_two_different_resources(api, valid_resources):
    """When we post two different resources, we want the server to distinct them."""
    r1 = api.add_resource(resource_dict(valid_resources[0]))
    c1_1 = api.get_resource(r1.data.id).data.attributes
    r2 = api.add_resource(resource_dict(valid_resources[1]))
    c2_1 = api.get_resource(r2.data.id).data.attributes
    c1_2 = api.get_resource(r1.data.id).data.attributes
    c2_2 = api.get_resource(r2.data.id).data.attributes
    c1_3 = api.get_resource(r1.data.id).data.attributes
    assert c1_1 == valid_resources[0], "see test_add_a_resource_and_retrieve_it"
    assert c1_2 == valid_resources[0]
    assert c1_3 == valid_resources[0]
    assert c2_1 == valid_resources[1]
    assert c2_2 == valid_resources[1]


class TestDeleteResource:
    """Test the deletion of resources."""

    @fixture(params=["get_resource", "delete_resource"])
    def get_error(self, api, valid_resource, request):
        """Return an error that is created if a ressource is absent."""
        r1 = api.add_resource(resource_dict(valid_resource))
        api.delete_resource(r1.data.id)
        action = getattr(api, request.param)
        with raises(ApiException) as error:
            action(r1.data.id)
        return error

    @step
    def test_deleted_resource_is_not_available(self, get_error):
        """If a client deleted a resource, this resource should be absent afterwards."""
        assert get_error.value.status == 404

    @step
    def test_deleted_resource_error(self, get_error):
        """A deleted resource returns a valid error."""
        assertIsError(get_error.value.body, 404)


class TestListResources:
    """Test the listing of resources."""

    @fixture
    def list_response(self, api):
        """Return a response for listing resources."""
        return api.get_resource_ids()

    @step
    def test_list_of_resource_ids_is_a_list(self, list_response):
        """The list returned by the api should be a list if strings."""
        assert isinstance(list_response.data, list)

    @step
    def test_all_ids_are_ids(self, list_response):
        """The listed ids are all ids."""
        assert all(_id.type == "id" for _id in list_response.data)

    @step
    def test_all_ids_are_unique(self, list_response):
        """The ids are only once in the list."""
        ids = set(_id.id for _id in list_response.data)
        assert len(ids) == len(list_response.data)

    @step
    def test_valid_jsonapi_response(self, list_response):
        """The response shoule be a json api response."""
        assertIsResponse(list_response)

    @step
    def test_new_resources_are_listed(self, api, valid_resource):
        """Posting new resources adds them their ids to the list of ids."""
        ids_before = set(_id.id for _id in api.get_resource_ids().data)
        r1 = api.add_resource(resource_dict(valid_resource))
        ids_after = set(_id.id for _id in api.get_resource_ids().data)
        new_ids = ids_after - ids_before
        assert r1.data.id in new_ids

    @step
    def test_resources_listed_can_be_accessed(self, api):
        """All the ids listed can be accessed."""
        ids = api.get_resource_ids().data
        for _id in ids[:10]:
            api.get_resource(_id.id)


class TestDeleteAllResources:
    """Test the deletion of all posted resources."""

    @step
    @mark.parametrize("action", ["get_resource", "delete_resource"])
    @mark.parametrize("add", [True, False])
    def test_delete_all_resources_removes_resource(self, api, action, add, valid_resource):
        """After all resources are deleted, they can not be accessed any more."""
        if add:
            ids = [api.add_resource(resource_dict(valid_resource)).data]
        else:
            ids = api.get_resource_ids().data
        api.delete_resources()
        for _id in ids[:10]:
            with raises(ApiException) as error:
                getattr(api, action)(_id.id)
            assert error.value.status == 404
            assertIsError(error.value.body, 404)

    @step
    def test_deleting_all_resources_returns_204(self, user1, url):
        """The status code should be 204 on content"""
        response = user1.delete(url + "/resources")
        assert response.status_code == 204


@step
@mark.test
def test_there_are_invalid_resources(api, invalid_resources):
    """Ensure that the tests have invalid resources to run with.

    This is a test test to ensure the testing environment works.
    If this test fails, the following tests may now work because of this.
    """
    assert invalid_resources


class TestInvalidRequests:
    """Some requests may be malformed.

    Here, we test that the output is malformed and the response is usable.
    """

    class TestUnsupportedMediaType:
        """
        Servers MUST respond with a 415 Unsupported Media Type status code 
        if a request specifies the header 
            Content-Type: application/vnd.api+json
        with any media type parameters.
        """

        INVALID_MEDIA_TYPES = [ # Content-Type, Accept
                ("", API_CONTENT_TYPE),
                ("application/json", API_CONTENT_TYPE), 
                ("application/vnd.api+json; version=1", API_CONTENT_TYPE),
                (API_CONTENT_TYPE, ""),
                (API_CONTENT_TYPE, "application/json"),
                (API_CONTENT_TYPE, "application/vnd.api+json; version=1"),
                (API_CONTENT_TYPE, "*/*; version=1"),
                (API_CONTENT_TYPE, "application/*; version=1"),
            ]

        @fixture(params=INVALID_MEDIA_TYPES)
        def response_to_invalid_content_type(self, request, url, a_valid_resource):
            return requests.post(url + "/resources",
                                 headers={"Content-Type": request.param[0],
                                          "Accept": request.param[1]},
                                 data=json.dumps(resource_dict(a_valid_resource)))

        @step
        def test_invalid_content_type_header_is_an_error(
                self, response_to_invalid_content_type):
            """Send possible requests to the server with a malformed header.
            The error returned should be in the jsonapi format."""
            assertIsError(response_to_invalid_content_type, 415)

        @step
        def test_invalid_content_type_header_has_the_right_content_type(
                self, response_to_invalid_content_type):
            """Send possible requests to the server and set no header."""
            assert response_to_invalid_content_type.headers["Content-Type"] == API_CONTENT_TYPE

    @step
    @mark.parametrize("data", ["invalid json", b"\x00\xfeas\x44"])
    def test_bad_request_if_there_is_no_valid_json(self, url, data):
        """If the posted object is not a valid JSON, the server notices it.

        https://httpstatuses.com/400
        """
        response = requests.post(url + "/resources", data=data, 
                                 headers={"Content-Type": API_CONTENT_TYPE})
        assert response.status_code == 400
    
    @step
    def test_invalid_resources_can_not_be_posted(self, api, invalid_resource):
        """If the resources do not fit in the schema, they cannot be posted.

        The error code 422 should be returned.
        https://httpstatuses.com/422
        """
        with raises(ApiException) as error:
            api.add_resource(resource_dict(invalid_resource))
        assert error.value.status == 422

    @step
    def test_invalid_resources_is_an_error(self, user1, invalid_resource, url):
        """If the resources do not fit in the schema, they cannot be posted.

        The error code 422 should be returned.
        https://httpstatuses.com/422
        """
        response = user1.post(url + "/resources", json=resource_dict(invalid_resource),
                              headers={"Content-Type": API_CONTENT_TYPE})
        assertIsError(response, 422)

    @step
    @mark.parametrize("document", [
            {},                               # nothing
            {"data": {}, "errors":[]},        # errors present
            {"errors":[]},                    # errors present
            {"data": {"type": "resource"}},   # no attributes
            {"data": {"type": "resrce", "attributes": {}}},      # invalid type
            {"data": {}},                     # no type
            {"data": {"attributes": {}}},     # no type
            {"data": {"attributes": [], "type": "resource"}},    # invalid data
            {"data": {"attributes": None, "type": "resource"}},  # invalid data
        ])
    def test_invalid_properties(self, user1, a_valid_resource, url, document):
        """The document must contain the data attribute.

        http://jsonapi.org/format/#document-top-level
        """
        if "data" in document and isinstance(document["data"].get("attributes", None), dict):
            document["data"]["attributes"] = a_valid_resource
        response = user1.post(url + "/resources", json=document,
                              headers={"Content-Type": API_CONTENT_TYPE})
        assertIsError(response, 422)


class TestPostWithId:
    """The client can request to store an object with a given id."""

    @step
    @mark.parametrize("_id", [
            "test-id",
            "550e8400-e29b-41d4-a716-446655440000",
            '!*"\'(),+abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$_@.&+-',
            "%aa%f1"
        ])
    def test_a_present_id_is_accepted(self, api, valid_resource, _id):
        """If an id is given for the object, it should be used to store the object."""
        response = api.add_resource(resource_dict(valid_resource, id=_id))
        assert response.data.id == _id

    @step
    def test_a_present_id_is_reachable(self, api, valid_resource):
        """If an id is given for the object, it should be used to store the object."""
        response = api.add_resource(resource_dict(valid_resource, id="test"))
        copy = api.get_resource("test")
        assert copy.data.attributes == valid_resource
        assert copy.data.id == "test"

    @step
    def test_can_not_post_twice_to_the_same_id(self, api, valid_resource):
        """Posting twice is a 403.

        see http://jsonapi.org/format/#crud-creating-client-ids
        """
        response = api.add_resource(resource_dict(valid_resource, id="id"))
        with raises(ApiException) as error:
            api.add_resource(resource_dict(valid_resource, id="id"))
        assert error.value.status == 403
        assertIsError(get_error.value.body, 403)

    @step
    @mark.parametrize("invalid_id", [
            1, "asd\x00", "%", "%1", "%Ga",
        ] + [chr(i) for i in range(256) if chr(i) not in '!*"\'(),+abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$_@.&+-'])
    def test_invalid_ids(self, api, invalid_id, valid_resource):
        """Test what happens with invalid ids."""
        with raises(ApiException) as error:
            api.add_resource(resource_dict(valid_resource, id=invalid_id))
        assert error.value.status == 403
        assertIsError(get_error.value.body, 403)
        








