#!/usr/bin/python3
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

# global variables
last_id = 0

def response_object(**kw):
    kw["jsonapi"] = dict(
        name=__file__,
        source="https://gitub.com/schul-cloud/schul_cloud_resources_server_tests",
        description="A test server to test crawlers agains the resources api.")
    return json.dumps(kw)

# set the error pages
def _error(error, code):
    """Return an error as json"""
    _error = {
        "status": code,
        "title": errors[code],
        "detail": error.body
    }
    traceback.print_exception(type(error), error, error.traceback)
    return response_object(errors=[_error])

for code in [404, 415]:
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

def test_json_api_headers():
    """Make sure the headers comply to json api standarts.

    Must be set: `Content-Type: application/vnd.api+json`
    """
    if request.headers["Content-Type"] != "application/vnd.api+json":
        abort(415, "Only the media type \"application/vnd.api+json\" is supported. "
                   "The api is json api compaible. "
                   "http://jsonapi.org/format/#content-negotiation")


@post(BASE + "/resources")
def add_resource():
    """Add a new resource."""
    global last_id
    resources = get_resources()
    _id = str(last_id)
    last_id += 1
    try:
        resource = json.loads(touni(request.body.read()))
    except (TypeError, ValueError):
        # this can be removed with later releases of bottle
        # https://github.com/bottlepy/bottle/blob/41ed6965de9bf7d0060ffd8245bf65ceb616e26b/bottle.py#L1292
        abort(400, "The request body is not a valid JSON object.")
    try:
        validate_resource(resource)
    except ValidationFailed as error:
        abort(422, error)
    resources[_id] = resource
    return {"id" : _id}


@get(BASE + "/resources/<_id>")
def get_resource(_id):
    """Get a resource identified by id."""
    if _id == "ids":
        return get_resource_ids()
    resources = get_resources()
    resource = resources.get(_id)
    if resource is None:
        abort(404, "Resource not found.")
        return
    return resource


@delete(BASE + "/resources/<_id>")
def delete_resource(_id):
    """Delete a saved resource."""
    resources = get_resources()
    if resources.pop(_id, None) is None:
        abort(404, "Resource not found.")


def get_resource_ids():
    """Return the list of current ids."""
    test_json_api_headers()
    resources = get_resources()
    response.content_type = 'application/vnd.api+json'
    return json.dumps(list(resources.keys()))


@delete(BASE + "/resources")
def delete_resources():
    """Delete all resources."""
    resources = get_resources()
    resources.clear()


def main():
    """Start the serer from the command line."""
    port = (int(sys.argv[1]) if len(sys.argv) >= 2 else 8080)
    run(host="", port=port, debug=True, reloader=True)


if __name__ == "__main__":
    main()

