import requests
from pytest import fixture


@step
def test_server_is_reachable(url):
    """There is a server behind the url."""
    result = requests.get(url)
    assert result.status_code


@step
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
        assert add_resource_response.type == "resource"

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
        response = auth_post(url + "/resources", data={"data":valid_resource})
        assert response.headers["Location"] == response.json()["links"]["self"]











