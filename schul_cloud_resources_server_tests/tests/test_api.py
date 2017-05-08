import requests
from pytest import fixture, mark
from schul_cloud_resources_server_tests.tests.assertions import *


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
    - missing data
    - additional id - whether it is taken
    """

    @fixture
    def add_resource_response(self, api, valid_resource):
        """Post a resource and get the response."""
        return api.add_resource({"data": valid_resource})

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
            self, add_resource_response, valid_resource, auth_get):
        """Links are returned. The self link should point to the resource."""
        response = auth_get(add_resource_response.links.self)
        data = response.json()
        resource = data["data"]["attributes"]
        assert resource == valid_resource

    @step
    def test_location_header_is_set(self, auth_post, valid_resource, url):
        """Post a new resource and the the location header. wich should be teh self link.

        see http://jsonapi.org/format/#crud-creating
        """
        response = auth_post(url + "/resources", json={"data":valid_resource})
        assert response.headers["Location"] == response.json()["links"]["self"]

    @step
    @mark.parametrize("host", ["google.de", "schul-cloud.org"])
    def test_location_header_uses_host_header(self, auth_post, valid_resource, url, host):
        """Post a new resource and the the location header. Which should be the self link.

        see http://jsonapi.org/format/#crud-creating
        Additionally, use a different host header.
        """
        headers = ({"Host": host} if host else {})
        response = auth_post(url + "/resources", headers=headers, json={"data":valid_resource})
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


class TestGetResources:
    """Get added resources back."""

    @step
    def test_add_a_resource_and_retrieve_it(self, api, valid_resource):
        """When we save a resource, we should be able to get it back."""
        result = api.add_resource({"data": valid_resource})
        _id = result.data.id
        assert _id, "id should be in {}".format(result.to_dict())
        copy = api.get_resource(_id).data.attributes
        assert valid_resource == copy

    @step
    def test_ressource_id_is_there(self, api, valid_resource):
        """When a resource is retrieved, the id is sent with it."""
        result = api.add_resource({"data": valid_resource})
        server_copy = api.get_resource(result.data.id)
        assert result.data.id == server_copy.data.id

    @step
    def test_ressource_type_is_set(self, api, valid_resource):
        """When a resource is retrieved, the type is sent with it."""
        result = api.add_resource({"data": valid_resource})
        server_copy = api.get_resource(result.data.id)
        assert result.data.type == "resource"

    @step
    def test_ressource_is_a_response(self, api, valid_resource):
        """When a resource is retrieved, the type is sent with it."""
        result = api.add_resource({"data": valid_resource})
        assertIsResponse(result)

@step
@mark.test
def test_there_are_at_least_two_valid_resources(valid_resources):
    """For the next tests, we will need two distinct valid resssources."""
    assert len(valid_resources) >= 2

