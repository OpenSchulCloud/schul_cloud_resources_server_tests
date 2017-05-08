import sys
import json
import jsonschema
import base64
import traceback
import os
HERE = os.path.dirname(__file__)
try:
    import schul_cloud_resources_server_tests
except ImportError:
    sys.path.insert(0, os.path.join(HERE, ".."))
    import schul_cloud_resources_server_tests
from schul_cloud_resources_api_v1.schema import validate_resource, ValidationFailed
from bottle import request, response, tob, touni, Bottle, abort
from pprint import pprint
from schul_cloud_resources_server_tests.errors import errors


app = Bottle()

run = app.run
post = app.post
get = app.get
delete = app.delete
error = app.error

# configuration constants
BASE = "/v1"

class data(object):
    """The data interface the server operates with."""

    @staticmethod
    def delete_resources():
        """Initialize the resources."""
        global _resources
        _resources = {
            "valid1@schul-cloud.org": {},
            "valid2@schul-cloud.org": {},
            None: {}
        } # user: id: resource

    @staticmethod
    def get_resources():
        """Return all stored resources."""
        resources = []
        for user_resources in _resources.values():
            resources.extend(user_resources.values())
        return resources


data.delete_resources()

passwords = {
    "valid1@schul-cloud.org": "123abc",
    "valid2@schul-cloud.org": "supersecure"
}
api_keys = {
   "abcdefghijklmn": "valid1@schul-cloud.org"
}

def get_location_url(resource_id):
    """Return the location orl of a resource given by id."""
    return "http://" + request.headers["Host"] + BASE + "/resources/{}".format(resource_id)


def response_object(cnf={}, **kw):
    kw.update(cnf)
    kw["jsonapi"] = dict(
        name="schul_cloud_resources_server_tests.app",
        source="https://gitub.com/schul-cloud/schul_cloud_resources_server_tests",
        description="A test server to test crawlers agains the resources api.")
    return json.dumps(kw)


@post(BASE + "/resources")
def add_resource():
    """Add a new resource."""
    global resource
    data = touni(request.body.read())
    pprint(data)
    add_request = json.loads(data)
    resource = resource = add_request["data"]
    link = get_location_url(1)
    response.headers["Location"] = link
    return response_object({"data": {"attributes": resource, "type":"resource", "id": "1"},
            "links": {"self":link}})

@get(BASE + "/resources/<_id>")
def get_resource(_id):
    """Get a resource identified by id."""
    return response_object({"data": {"attributes": resource, "id": "1", "type": "resource"}, })



def main():
    """Start the serer from the command line."""
    port = (int(sys.argv[1]) if len(sys.argv) >= 2 else 8080)
    run(host="", port=port, debug=True, reloader=True)


__all__ = ["app", "data", "main"]


if __name__ == "__main__":
    main()
