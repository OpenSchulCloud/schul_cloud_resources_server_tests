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
    - url

    """
    parser.addoption("--url", action="store", default="http://localhost:8080/v1/",
        help="url: the url of the server api to connect to")


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


_steps = []

def step(function):
    """Allow pytest -m stepX to run test up to a certain number."""
    step_number = len(_steps) + 1
    step_only_marker = "step{}only".format(step_number)
    marker_only = getattr(pytest.mark, step_only_marker)
    step_marker = "step{}".format(step_number)
    marker = getattr(pytest.mark, step_marker)
    def mark_function(marker):
        current_function = function.__globals__[function.__name__] # KeyError: do not use step twice
        function.__globals__[function.__name__] = marker(current_function)
    for mark_step in _steps:
        mark_step(marker)
    _steps.append(mark_function)
    return marker_only(marker(function))
__builtins__["step"] = step
