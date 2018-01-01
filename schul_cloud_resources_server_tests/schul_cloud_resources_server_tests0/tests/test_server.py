import requests
from pytest import raises


def test_server_is_there(resources_server):
    """Test that the server is there."""
    requests.get(resources_server.url, headers={"Content-Type":"application/vnd.api+json"})


def test_server_works_on_data(resources_server, valid_resource):
    """Test that the api adds a resource."""
    resources_server.api.add_resource({"data": {"type": "resource", "attributes": valid_resource}})
    assert resources_server.get_resources() == [valid_resource]


# this must be the last test
def test_server_stops(resources_server):
    """Test that the server stops in the end."""
    resources_server.shutdown()
    with raises(requests.exceptions.ReadTimeout):
        requests.get(resources_server.url,timeout=0.01)
    
