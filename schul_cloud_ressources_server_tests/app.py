#!/usr/bin/python3
import sys
import json
import jsonschema
import base64
from schul_cloud_ressources_api_v1.schema import validate_ressource, ValidationFailed
from bottle import run, post, request, get, delete, abort, response

# configuration constants
BASE = "/v1"

# global variables
_ressources = {
    "valid1@schul-cloud.org": {},
    "valid2@schul-cloud.org": {},
    None: {}
} # user: id: ressource
last_id = 0

passwords = {
    "valid1@schul-cloud.org": "123abc",
    "valid2@schul-cloud.org": "supersecure"
}
api_keys = {
   "abcdefghijklmn": "valid1@schul-cloud.org"
}

def get_api_key():
    """Return the api key or None."""
    header = request.headers.get('Authorization')
    if not header: return
    method, data = header.split(None, 1)
    if method.lower() != 'api-key': return
    return base64.b64decode(data[4:].encode()).decode()

def get_ressources():
    """Return the ressources of the authenticated user.

    If authentication failed, this aborts the execution with
    401 Unauthorized.
    """
    basic = request.auth
    if basic:
        username, password = basic
        if passwords[username] != password:
            abort(401, "Could not do basic authentication. Wrong username or password.")
    else:
        api_key = get_api_key()
        if api_key:
            username = api_keys[api_key]
        else:
            username = None
    return _ressources[username]


@post(BASE + "/ressources")
def add_ressource():
    """Add a new ressource."""
    global last_id
    ressources = get_ressources()
    _id = str(last_id)
    last_id += 1
    try:
        ressource = request.json
    except (ValueError, TypeError):
        # this can be removed with later releases of bottle
        # https://github.com/bottlepy/bottle/blob/41ed6965de9bf7d0060ffd8245bf65ceb616e26b/bottle.py#L1292
        abort(400, "The request body is not a valid JSON object.")
    if ressource is None:
        abort(415, "JSON is expected.")
    try:
        validate_ressource(ressource)
    except ValidationFailed as error:
        abort(422, error)
    ressources[_id] = ressource
    return {"id" : _id}


@get(BASE + "/ressources/<_id>")
def get_ressource(_id):
    """Get a ressource identified by id."""
    if _id == "ids":
        return get_ressource_ids()
    ressources = get_ressources()
    ressource = ressources.get(_id)
    if ressource is None:
        abort(404, "Ressource not found.")
        return
    return ressource


@delete(BASE + "/ressources/<_id>")
def delete_ressource(_id):
    """Delete a saved ressource."""
    ressources = get_ressources()
    ressources.pop(_id)


def get_ressource_ids():
    """Return the list of current ids."""
    ressources = get_ressources()
    response.content_type = 'application/json'
    return json.dumps(list(ressources.keys()))


@delete(BASE + "/ressources")
def delete_ressources():
    """Delete all ressources."""
    ressources = get_ressources()
    ressources.clear()

def main():
    port = (int(sys.argv[1]) if len(sys.argv) >= 2 else 8080)
    run(host="", port=port, debug=True, reloader=True)


if __name__ == "__main__":
    main()

