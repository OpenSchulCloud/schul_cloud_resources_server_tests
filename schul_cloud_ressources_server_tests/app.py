#!/usr/bin/python3

import sys
from bottle import run, post, request, get

BASE = "/v1"

ressources = {}

@post(BASE + "/ressources")
def add_ressource():
    _id = str(len(ressources))
    ressources[_id] = request.body.read()
    return {"id" : _id}


@get(BASE + "/ressources/<_id>")
def get_ressource(_id):
    return ressources[_id]

def main():
    port = (int(sys.argv[1]) if len(sys.argv) >= 2 else 8080)
    run(host="", port=port, debug=True, reloader=True)


if __name__ == "__main__":
    main()

