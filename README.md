# Schul-Cloud Ressources Server Tests

This repository contains

- a server to test scrapers against
- tests to test the server

## Installation

Using `pip`, you can install all dependencies like this:

    pip install --user -r requirements.txt test-requrements.txt

## Server

You can find the API definition [here][api].
The server serves according to the API.
It verifies the input and output for correctness.

To start the server, run

    python3 -m schul_cloud_ressources_server_tests.app

## Tests

You always test against the running server.
**Tests may delete everyting you can reach.**
If you test the running server, make sure to authenticate in a way that does not destroy the data you want to keep.

    pytest --pyargs schul_cloud_ressources_server_tests.test --url=http://localhost:8080/v1/

`http://localhost:8080/v1/` is the default url.

### Steps for Implementation

If you want to implement your serverm you can follow the TDD steps to implement
one test after the other.

    pytest --pyargs schul_cloud_ressources_server_tests.test -m step1
    pytest --pyargs schul_cloud_ressources_server_tests.test -m step2
    pytest --pyargs schul_cloud_ressources_server_tests.test -m step3
    ...

`step1` runs the first test  
`step2` runs the first and the second test  
`step3` runs the first, second and third test  
...

You can run  a single test with

    pytest --pyargs schul_cloud_ressources_server_tests.test -m step3only


## TODO


- generate a docker container for the server
- generate a docker container for the tests
- document how to embed the tests and the server in 
  - a crawler
  - travis build script of arbitrary language
- create example crawler with tests




[api]: https://github.com/schul-cloud/ressources-api-v1
