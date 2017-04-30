#!/usr/bin/python3

import sys
import json
from bottle import run, post, request, get, delete, abort, response

BASE = "/v1"

ressources = {}

@post(BASE + "/ressources")
def add_ressource():
    """Add a new ressource."""
    _id = str(len(ressources))
    ressources[_id] = request.body.read()
    return {"id" : _id}


@get(BASE + "/ressources/<_id>")
def get_ressource(_id):
    """Get a ressource identified by id."""
    if _id == "ids":
        return get_ressource_ids()
    ressource = ressources.get(_id)
    if ressource is None:
        abort(404, "Ressource not found.")
        return
    return ressource


@delete(BASE + "/ressources/<_id>")
def delete_ressource(_id):
    """Delete a saved ressource."""
    del ressources[_id]


def get_ressource_ids():
    """Return the list of current ids."""
    response.content_type = 'application/json'
    return json.dumps(list(ressources.keys()))


@delete(BASE + "/ressources")
def delete_ressources():
    """Delete all ressources."""
    global ressources
    ressources = {}


def main():
    port = (int(sys.argv[1]) if len(sys.argv) >= 2 else 8080)
    run(host="", port=port, debug=True, reloader=True)


if __name__ == "__main__":
    main()

