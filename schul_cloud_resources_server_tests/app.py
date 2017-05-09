import sys
import json
import jsonschema
import base64
import traceback
import os
import re
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

# global variables
last_id = 0

# set the error pages
def _error(error, code):
    """Return an error as json"""
    _error = {
        "status": code,
        "title": errors[code],
        "detail": error.body
    }
    traceback.print_exception(type(error), error, error.traceback)
    response.headers["Content-Type"] = "application/vnd.api+json"
    return response_object(errors=[_error])

for code in [403, 404, 415, 422]:
    error(code)(lambda error, code=code:_error(error, code))


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


def get_id():
    """Return a new id."""
    global last_id
    last_id += 1
    return  str(last_id)

data.delete_resources()

passwords = {
    "valid1@schul-cloud.org": "123abc",
    "valid2@schul-cloud.org": "supersecure"
}
api_keys = {
   "abcdefghijklmn": "valid1@schul-cloud.org"
}

HEADER_ERROR = "Malfomred Authorization header."

def get_api_key():
    """Return the api key or None."""
    header = request.headers.get('Authorization')
    if not header: return
    try:
        method, data = header.split(None, 1)
        if method.lower() != 'api-key': return
        return touni(base64.b64decode(tob(data[4:])))
    except (ValueError, TypeError):
        abort(401, HEADER_ERROR) 

BASIC_ERROR = "Could not do basic authentication. Wrong username or password."
API_KEY_ERROR = "Could not authenticate using the given api key."

def get_resources():
    """Return the resources of the authenticated user.

    If authentication failed, this aborts the execution with
    401 Unauthorized.
    """
    pprint(dict(request.headers))
    header = request.environ.get('HTTP_AUTHORIZATION','')
    if header:
        print("Authorization:", header)
    basic = request.auth
    if basic:
        username, password = basic
        if passwords.get(username) != password:
            abort(401, BASIC_ERROR)
    else:
        api_key = get_api_key()
        if api_key is not None:
            username = api_keys.get(api_key)
            if username is None:
                abort(401, API_KEY_ERROR)
        else:
            username = None
    return _resources[username]



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

def test_jsonapi_header():
    """Make sure that the content type is set accordingly.

    http://jsonapi.org/format/#content-negotiation-clients
    """
    content_type = request.content_type
    content_type_expected = "application/vnd.api+json"
    if content_type != content_type_expected:
        abort(415, "The Content-Type header must be \"{}\", not \"{}\".".format(
                   content_type_expected, content_type))
    accept = request.headers["Accept"]
    expected_accept = ["*/*", "application/*", "application/vnd.api+json"]
    if accept not in expected_accept:
        abort(415, "The Accept header must one of \"{}\", not \"{}\".".format(
                   expected_accept, accept))


@post(BASE + "/resources")
def add_resource():
    """Add a new resource."""
    test_jsonapi_header()
    resources = get_resources()
    try:
        data = touni(request.body.read())
        pprint(data)
        add_request = json.loads(data)
    except (ValueError):
        abort(400, "The expected content should be json, encoded in utf8.")
    if not "data" in add_request:
        abort(422, "The data property must be present.")
    if "errors" in add_request:
        abort(422, "The errors property must not be present.")
    if add_request["data"].get("type") != "resource":
        abort(422, "There must be a \"type\" property set to \"resource\" in the data field.")
    if not isinstance(add_request["data"].get("attributes"), dict):
        abort(422, "There must be a \"attributes\" property set to an object in the data field.")
    resource = add_request["data"]["attributes"]
    try:
        validate_resource(resource)
    except ValidationFailed as error:
        abort(422, str(error))
    _id = add_request["data"].get("id", get_id())
    link = get_location_url(_id)
    if not isinstance(_id, str) or not re.match("^([!*\"'(),+a-zA-Z0-9$_@.&+-]|%[0-9a-fA-F]{2})+$", _id):
        abort(403, "The id \"{}\" is invalid, can not be part of a url.".format(_id))
    if _id in resources:
        abort(403, "The id \"{}\" already exists.".format(_id))
    resources[_id] = resource
    response.headers["Location"] = link
    response.status = 201
    return response_object({"data": {"attributes": resource, "type":"resource", "id": _id},
            "links": {"self":link}})


@get(BASE + "/resources/<_id>")
def get_resource(_id):
    """Get a resource identified by id."""
    if _id == "ids":
        return get_resource_ids()
    resources = get_resources()
    resource = resources.get(_id)
    if resource is None:
        abort(404, "The resource with the id \"{}\" could not be found.".format(_id))
    return response_object({"data": {"attributes": resource, "id": _id, "type": "resource"}, })


@delete(BASE + "/resources/<_id>")
def delete_resource(_id):
    """Delete a saved resource."""
    resources = get_resources()
    if resources.pop(_id, None) is None:
        abort(404, "Resource {} not found.".format(_id))


def get_resource_ids():
    """Return the list of current ids."""
    resources = get_resources()
    #response.content_type = 'application/vnd.api+json'
    return response_object({"data": [{"type": "id", "id": _id} for _id in resources]})



@delete(BASE + "/resources")
def delete_resources():
    """Delete all resources."""
    resources = get_resources()
    resources.clear()
    response.status = 204


def main():
    """Start the serer from the command line."""
    port = (int(sys.argv[1]) if len(sys.argv) >= 2 else 8080)
    run(host="", port=port, debug=True, reloader=True)


__all__ = ["app", "data", "main"]


if __name__ == "__main__":
    main()
