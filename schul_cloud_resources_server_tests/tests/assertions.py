import json
from schul_cloud_resources_server_tests.errors import errors as server_errors


def to_dict(model):
    """Return a dictionary."""
    if hasattr(model, "to_dict"):
        return model.to_dict()
    if hasattr(model, "json"):
        return model.json()
    if isinstance(model, str):
        return json.loads(model)
    assert isinstance(model, dict)
    return model


def assertIsResponse(response):
    response = to_dict(response)
    assert ("errors" in response) ^ ("data" in response), "The members data and errors MUST NOT coexist in the same document. http://jsonapi.org/format/#conventions"
    assert ("data" in response if "included" in response else True), "If a document does not contain a top-level data key, the included member MUST NOT be present either. http://jsonapi.org/format/#conventions"
    assert "jsonapi" in response, "jsonapi must be present, see the api specification."
    jsonapi = response.get("jsonapi")
    assert jsonapi, "the jsonapi attribute must be set in the reponse"
    for attr in ["name", "source", "description"]:
        assert attr in jsonapi, "{} must be present, see #/definition/Jsonapi".format(attr)
        assert isinstance(attr, str)


def assertIsError(response, status):
    """This is an error response object with a specific status code.

    You can view the specification here:
    - https://github.com/schul-cloud/resources-api-v1/blob/f0ce9acfde59563822071207bd176baf648db8b4/api-definition/swagger.yaml#L292
    - updated: https://github.com/schul-cloud/resources-api-v1/blob/master/api-definition/swagger.yaml#L292
    """
    response = to_dict(response)
    assertIsResponse(response)
    assert "errors" in response, "errors must be present"
    errors = response["errors"]
    assert isinstance(errors, list)
    assert len(errors) >= 1
    for error in errors:
        for attr in ["status", "title", "detail"]:
            assert attr in error, "#/definitions/ErrorElement"
        assert isinstance(error["status"], int), "#/definitions/ErrorElement"
        assert isinstance(error["title"], str), "#/definitions/ErrorElement"
        assert isinstance(error["detail"], str), "#/definitions/ErrorElement"
    error = errors[0]
    assert error["status"] == status
    assert error["title"] == server_errors[status]
    assert len(error["detail"]) > len(error["title"])
