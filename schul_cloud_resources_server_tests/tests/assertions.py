"""This module contains assertions which work across many tests.

These assertions are a bit more complex than an assert ==.
"""

import json
from schul_cloud_resources_server_tests.errors import errors as server_errors
import sys

if sys.version_info[0] == 2:
    STRING_TYPE = basestring
else:
    STRING_TYPE = str


def to_dict(model):
    """Return a dictionary."""
    if hasattr(model, "to_dict"):
        return model.to_dict()
    try:
        if hasattr(model, "json"):
            return model.json()
        if isinstance(model, STRING_TYPE):
            return json.loads(model)
    except ValueError as error:
        raise ValueError("The response should be JSON. {}".format(error))
    assert isinstance(model, dict)
    return model


def assertIsResponse(response, link_self="TODO"):
    response = to_dict(response)
    assert ("errors" in response) ^ ("data" in response), "Either the member \"data\" or the member \"error\" must be given. http://jsonapi.org/format/#conventions"
    assert ("data" in response if "included" in response else True), "If a document does not contain a top-level data key, the included member MUST NOT be present either. http://jsonapi.org/format/#conventions"
    assert "jsonapi" in response, "jsonapi must be present, see the api specification."
    jsonapi = response.get("jsonapi")
    assert jsonapi is not None, "the jsonapi attribute must be set in the reponse"
    assert jsonapi.get("version") == "1.0", "version must be present http://jsonapi.org/format/#document-jsonapi-object"
    assert "meta" in jsonapi, "meta tag should be present to contain some information."
    for attr in ["name", "source", "description"]:
        assert attr in jsonapi["meta"], "{} must be present, see #/definition/Jsonapi".format(attr)
        assert isinstance(jsonapi["meta"][attr], STRING_TYPE)
    if link_self is not None:
       assert link_self != "TODO", "Change the test case source code to include the url."
       assert "links" in response
       assert isinstance(response["links"], dict)
       assert "self" in response["links"] or "_self" in response["links"]
       link = response["links"].get("self", response["links"].get("_self"))
       assert link == link_self, link_self


def assertIsError(response, status):
    """This is an error response object with a specific status code.

    You can view the specification here:
    - https://github.com/schul-cloud/resources-api-v1/blob/f0ce9acfde59563822071207bd176baf648db8b4/api-definition/swagger.yaml#L292
    - updated: https://github.com/schul-cloud/resources-api-v1/blob/master/api-definition/swagger.yaml#L292
    """
    response = to_dict(response)
    assertIsResponse(response, None)
    assert "errors" in response, "errors must be present"
    errors = response["errors"]
    assert isinstance(errors, list)
    assert len(errors) >= 1
    for error in errors:
        for attr in ["status", "title", "detail"]:
            assert attr in error, "#/definitions/ErrorElement"
        assert isinstance(error["status"], int), "#/definitions/ErrorElement"
        assert isinstance(error["title"], STRING_TYPE), "#/definitions/ErrorElement"
        assert isinstance(error["detail"], STRING_TYPE), "#/definitions/ErrorElement"
    error = errors[0]
    assert error["status"] == status, status
    assert error["title"] == server_errors[status], server_errors[status]
    assert len(error["detail"]) > len(error["title"])
