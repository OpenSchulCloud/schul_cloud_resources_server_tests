#!/usr/bin/python3

import sys
from bottle import run, post

BASE = "/v1"

@post(BASE + "/ressources")
def add_ressource():
    return {"id" : ""}



def main():
    port = (int(sys.argv[1]) if len(sys.argv) >= 2 else 8080)
    run(host="", port=port, debug=True, reloader=True)


if __name__ == "__main__":
    main()

