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
import base64
import schul_cloud_resources_api_v1.auth as auth
from schul_cloud_resources_api_v1.rest import ApiException
from schul_cloud_resources_api_v1 import ApiClient, ResourceApi
from schul_cloud_resources_api_v1.schema import get_valid_examples, get_invalid_examples
from schul_cloud_resources_server_tests.tests.fixtures import *
from bottle import touni, tob


NUMBER_OF_VALID_RESSOURCES = 3
NUMBER_OF_INVALID_RESSOURCES = 2
RESSOURCES_API_ZIP_URL = "https://github.com/schul-cloud/resources-api-v1/archive/master.zip"
RESSOURCES_EXAMPLES_BASE_PATH = "resources-api-v1-master/schemas/resource/examples"


@pytest.fixture
def valid_resources():
    """Return a list of valid ressoruces useable by tests."""
    return get_valid_examples()


@pytest.fixture
def invalid_resources():
    """Return a list of invalid ressoruces useable by tests."""
    return get_invalid_examples()


@pytest.fixture
def a_valid_resource(valid_resources):
    """Return a valid resource.

    This fixture is not parametrized and does not mulitply the tests.
    """
    return valid_resources[0]


# https://docs.pytest.org/en/latest/fixture.html#parametrizing-fixtures
@pytest.fixture(params=list(range(NUMBER_OF_VALID_RESSOURCES)))
def valid_resource(request, valid_resources):
    """Return a valid resource."""
    return valid_resources[request.param % len(valid_resources)]


@pytest.fixture(params=list(range(NUMBER_OF_INVALID_RESSOURCES)))
def invalid_resource(request, invalid_resources):
    """Return an invalid resource."""
    return invalid_resources[request.param % len(invalid_resources)]


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

ERROR_BASIC = "user name and password must be divided by \":\" when "\
              "using --basic=username:password as a test parameter"

def get_credentials(metafunc):
    """Generate a list of credentials from the test parameters.

    Return a tuple (authentication mechanism, user name, password)
    """
    users = []
    if metafunc.config.option.noauth == "true":
        users.append(("noauth", None, None))
    for credentials in metafunc.config.option.basic:
        assert ":" in credentials, ERROR_BASIC
        username, password = credentials.split(":", 1)
        users.append(("basic", username, password))
    for credentials in metafunc.config.option.apikey:
        credentials = credentials.split(":", 1)
        username = (["anonymous api key"] if len(credentials) == 1 else credentials[0])
        users.append(("apikey", username, credentials[-1]))
    return users


def pytest_generate_tests(metafunc):
    """Generate parameters.

    The authentication parameters require special handling
    to create nice test cases.
    """
    if "all_credentials"  in metafunc.fixturenames:
        metafunc.parametrize("all_credentials", [get_credentials(metafunc)])
    if "a_user" in metafunc.fixturenames:
        credentials = get_credentials(metafunc)
        metafunc.parametrize("_a_user", credentials[:1])
    if "_user2" in metafunc.fixturenames and \
        "_user1_auth2" in metafunc.fixturenames:
        raise NotImplementedError()
    elif "_user1" in metafunc.fixturenames and \
        "_user2" in metafunc.fixturenames:
        credentials = get_credentials(metafunc)
        params = [(u1, u2) for u1 in credentials for u2 in credentials
                  if u1[1] != u2[1]]
        metafunc.parametrize("_user1,_user2", params)
    elif "_user1" in metafunc.fixturenames and \
        "_user1_auth2" in metafunc.fixturenames:
        credentials = get_credentials(metafunc)
        params = [(u1, u2) for u1 in credentials for u2 in credentials
                  if u1[1] == u2[1] and u1[2] != u2[2]]
        metafunc.parametrize("_user1,_user1_auth2", params)
    elif "_user1" in metafunc.fixturenames:
        credentials = get_credentials(metafunc)
        metafunc.parametrize("_user1", credentials)
    if "_invalid_user" in metafunc.fixturenames:
        credentials = get_credentials(metafunc)
        invalid_credentials = [
            ("apikey", "", ""), # empty api key
            ("basic", "", ""), # empty username and password
        ]
        if not ("noauth", None, None) in credentials:
            invalid_credentials.append(("noauth", None, None))
        for cred in credentials:
            if cred[0] == "basic":
                # empty password or user name
                invalid_credentials.append(("basic", cred[1], ""))
                invalid_credentials.append(("basic", "", cred[2]))
                invalid_credentials.append(("basic", "invalid" + cred[1], cred[2]))
                invalid_credentials.append(("basic", cred[1], "invalid" + cred[2]))
                invalid_credentials.append(("basic", cred[2], cred[1]))
                invalid_credentials.append(("apikey", None, cred[1]))
                invalid_credentials.append(("apikey", None, cred[2]))
            elif cred[0] == "apikey":
                invalid_credentials.append(("apikey", None, cred[1]))
                invalid_credentials.append(("basic", cred[2], cred[1]))
                invalid_credentials.append(("basic", cred[1], cred[2]))
                invalid_credentials.append(("apikey", None, cred[1] + "invalid"))
                invalid_credentials.append(("apikey", None, cred[2] + "invalid"))
                invalid_credentials.append(("basic", cred[2], cred[1] + "invalid"))
                invalid_credentials.append(("basic", cred[1], cred[2] + "invalid"))
                invalid_credentials.append(("basic", "invalid" + cred[2], cred[1]))
                invalid_credentials.append(("basic", "invalid" + cred[1], cred[2]))
        metafunc.parametrize("_invalid_user", invalid_credentials)


class User(object):
    """The user object for the tests.

    The user has an api which uses a certain authentication.
    """

    def __init__(self, api, auth_type, name, secret):
        """Create a new user object."""
        self._api = api
        assert auth_type in ["noauth", "basic", "apikey"]
        self._auth_type = auth_type
        self._name = name
        self._secret = secret
    
    @property
    def name(self):
        """The user name, None if no name is given."""
        return self._name

    @property
    def credentials(self):
        """The authentication credentials, None if none are given."""
        return self._name, self._secret

    def authenticate(self):
        """Authenticate the user."""
        if self._auth_type == "noauth":
            auth.none()
        elif self._auth_type == "basic":
            auth.basic(self._name, self._secret)
        elif self._auth_type == "apikey":
            auth.api_key(self._secret)
        else:
            raise ValueError(self._auth_type)

    @property
    def api(self):
        """Return an api object that is authenticated."""
        self.authenticate()
        return self._api

    def _get_auth_headers(self, headers):
        """Return the Authorization headers."""
        r = headers.copy()
        if self._auth_type == "noauth":
            pass
        elif self._auth_type == "basic":
            credentials = touni(base64.b64encode(tob(self._name + ":" + self._secret)))
            r.setdefault("Authorization", "basic " + credentials)
        elif self._auth_type == "apikey":
            credentials = touni(base64.b64encode(tob(self._secret)))
            r.setdefault("Authorization", "api-key key=" + credentials)
        else:
            raise ValueError(self._auth_type)
        return r

    def __repr__(self):
        """A string representation."""
        return "User(api, {}, {}, {})".format(self._auth_type, repr(self._name), repr(self._secret))

    def _add_auth_headers(self, kw):
        """Embed the authenticatin headers into to key words"""
        kw["headers"] = self._get_auth_headers(kw.get("headers", {}))
        return kw

    def get(self, url, **kw):
        """Return a requests.get with authentication parameters."""
        return requests.get(url, **self._add_auth_headers(kw))

    def post(self, url, **kw):
        """Return a requests.get with authentication parameters."""
        return requests.post(url, **self._add_auth_headers(kw))

    def delete(self, url, **kw):
        """Return a requests.get with authentication parameters."""
        return requests.delete(url, **self._add_auth_headers(kw))

@pytest.fixture
def user1(_user1, _api):
    """Return a user for the api with credentials."""
    return User(_api, *_user1)


@pytest.fixture
def a_user(_a_user, _api):
    """Return a user for the api with credentials.
    
    This fixture uses only one authentication mechanism.
    It does not multiply the tests.
    """
    return User(_api, *_a_user)


@pytest.fixture
def user1_auth2(_user1_auth2, _api):
    """Return a user for the api with credentials."""
    return User(_api, *_user1_auth2)


@pytest.fixture
def user2(_user2, _api):
    """Return a user for the api with credentials."""
    return User(_api, *_user2)


@pytest.fixture
def invalid_user(_invalid_user, _api):
    """Return an invalid user."""
    return User(_api, *_invalid_user)


@pytest.fixture
def url(request):
    """The url of the server."""
    return request.config.getoption("--url").rstrip("/")


@pytest.fixture
def client(url):
    """The client object connected to the API."""
    return ApiClient(url)


@pytest.fixture
def _api(client):
    """The api to use to test the server."""
    return ResourceApi(client)


@pytest.fixture
def api(user1):
    """The api uses the authentication credentials."""
    return user1.api


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



