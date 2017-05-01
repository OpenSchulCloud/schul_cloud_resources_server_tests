#
# Fixture collection for pytest
#

#
# command line arguments
# ----------------------
#
# see
#   https://docs.pytest.org/en/latest/example/simple.html#pass-different-values-to-a-test-function-depending-on-command-line-options
#

import pytest
import requests
import urllib
import tempfile
import zipfile
import json
import shutil
import os
from schul_cloud_ressources_api_v1.configuration import Configuration
from schul_cloud_ressources_api_v1.rest import ApiException
from schul_cloud_ressources_api_v1 import ApiClient, RessourceApi
from schul_cloud_ressources_api_v1.schema import get_valid_examples, get_invalid_examples


NUMBER_OF_VALID_RESSOURCES = 3
NUMBER_OF_INVALID_RESSOURCES = 2
RESSOURCES_API_ZIP_URL = "https://github.com/schul-cloud/ressources-api-v1/archive/master.zip"
RESSOURCES_EXAMPLES_BASE_PATH = "ressources-api-v1-master/schemas/ressource/examples"


@pytest.fixture
def valid_ressources():
    """Return a list of valid ressoruces useable by tests."""
    return get_valid_examples()


@pytest.fixture
def invalid_ressources():
    """Return a list of invalid ressoruces useable by tests."""
    return get_invalid_examples()


# https://docs.pytest.org/en/latest/fixture.html#parametrizing-fixtures
@pytest.fixture(params=list(range(NUMBER_OF_VALID_RESSOURCES)))
def valid_ressource(request, valid_ressources):
    """Return a valid ressource."""
    return valid_ressources[request.param % len(valid_ressources)]


@pytest.fixture(params=list(range(NUMBER_OF_INVALID_RESSOURCES)))
def invalid_ressource(request, invalid_ressources):
    """Return an invalid ressource."""
    return invalid_ressources[request.param % len(invalid_ressources)]


def pytest_addoption(parser):
    """Add options to pytest.

    This adds the options for
    - url to store the value
    - token to add the token to a list
    - basic to add the credentials to a list
    - noauth if you do not want to test without authentication
    """
    parser.addoption("--url", action="store", default="http://localhost:8080/v1/",
        help="url: the url of the server api to connect to")
    parser.addoption("--noauth", action="store", default="true",
        help="noauth: whether to connect without authentication")
    parser.addoption("--basic", action="append", default=[],
        help="basic: list of basic authentications to use")
    parser.addoption("--apikey", action="append", default=[],
        help="apikey: list of api key authentications to use")

def pytest_generate_tests(metafunc):
    """Generate parameters.

    - _auth a list of authentication mechanisms
    """
    if '_auth' in metafunc.fixturenames:
        auth = ([None] if metafunc.config.option.noauth == "true" else []) + \
               [("basic", a) for a in metafunc.config.option.basic] + \
               [("apikey", k) for k in metafunc.config.option.apikey]
        metafunc.parametrize("_auth", auth)


def _authenticate(auth):
    """Return a generator for setting the configuration."""
    configuration = Configuration()
    if auth is None:
        yield None
    elif auth[0] == "basic":
        configuration.username, configuration.password = auth[1].split(":", 1)
        yield ["basic"]
        configuration.username = configuration.password = ""
    elif auth[0] == "apikey":
        split = auth[1].split(":", 1)
        configuration.api_key["api_key"] = split[0]
        if len(split) == 2:
            configuration.api_key_prefix["api_key"] = split[1]
        yield ["api_key"]
        configuration.api_key.pop("api_key")
        configuration.api_key.pop("api_key")
    else:
        raise ValueError(auth)


@pytest.fixture
def auth_settings(_auth):
    """Authenticate the request."""
    return _authenticate(_auth)


@pytest.fixture
def url(request):
    """The url of the server."""
    return request.config.getoption("--url").rstrip("/")


@pytest.fixture
def client(url):
    """The client object connected to the API."""
    return ApiClient(url)


@pytest.fixture
def api(client):
    """The api to use to test the server."""
    return RessourceApi(client)



def step(function):
    """Allow pytest -m stepX to run test up to a certain number."""
    step_number = len(_steps) + 1
    step_only_marker = "step{}only".format(step_number)
    marker_only = getattr(pytest.mark, step_only_marker)
    step_marker = "step{}".format(step_number)
    marker = getattr(pytest.mark, step_marker)
    def mark_function(marker):
        marker(function)
    for mark_step in _steps:
        mark_step(marker)
    _steps.append(mark_function)
    return marker_only(marker(function))
_steps = []

__builtins__["step"] = step
