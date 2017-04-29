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

NUMBER_OF_VALID_RESSOURCES = 3
NUMBER_OF_INVALID_RESSOURCES = 2
RESSOURCES_API_ZIP_URL = "https://github.com/schul-cloud/ressources-api-v1/archive/master.zip"
RESSOURCES_EXAMPLES_BASE_PATH = "ressources-api-v1-master/schemas/ressource/examples"

def download(url, to_path):
    """Download the content of a url to path."""
    # from http://stackoverflow.com/a/16696317/1320237
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(to_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename

@pytest.fixture(scope="module")
def api_temp_dir():
    directory = os.path.join(tempfile.gettempdir(), "ressources_api")
    os.makedirs(directory, exist_ok=True)
    return directory


@pytest.fixture(scope="module")
def api_zip_file(api_temp_dir):
    """The zip file with the downloaded api repository

    RESSOURCES_API_ZIP_URL is the url to the repository.
    """
    # tempdir https://docs.pytest.org/en/latest/tmpdir.html
    zip_file = os.path.join(api_temp_dir, "api.zip")
    if not os.path.exists(zip_file):
        download(RESSOURCES_API_ZIP_URL, zip_file)
    return zip_file


@pytest.fixture(scope="module")
def api_folder(api_zip_file, api_temp_dir):
    """Extract the zip file and return the directory."""
    api_folder = os.path.join(api_temp_dir, "api")
    if not os.path.exists(api_folder):
        os.mkdir(api_folder)
        with zipfile.ZipFile(api_zip_file) as zipf:
            zipf.extractall(api_folder)
    return api_folder


@pytest.fixture(scope="module")
def ressources(api_folder):
    """Return a list of valid ressoruces useable by tests."""
    valid = []
    invalid = []
    base_folder = os.path.join(api_folder, RESSOURCES_EXAMPLES_BASE_PATH)
    assert os.path.exists(base_folder)
    for dirpath, dirnames, filenames in os.walk(base_folder):
        test_path = dirpath[len(base_folder):]
        for file in filenames:
            with open(os.path.join(dirpath, file)) as f:
                ressource = json.load(f)
            if "invalid" in test_path:
                invalid.append(ressource)
            else:
                valid.append(ressource)
    return valid, invalid


# https://docs.pytest.org/en/latest/fixture.html#parametrizing-fixtures
@pytest.fixture(scope="module",
                params=list(range(NUMBER_OF_VALID_RESSOURCES)))
def valid_ressource(request, ressources):
    """Return a valid ressource."""
    return ressources[0][request.param % len(ressources[0])]


@pytest.fixture(scope="module",
                params=list(range(NUMBER_OF_INVALID_RESSOURCES)))
def invalid_ressource(request, ressources):
    """Return an invalid ressource."""
    return ressources[1][request.param % len(ressources[1])]


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

