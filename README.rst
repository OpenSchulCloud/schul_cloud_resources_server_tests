Schul-Cloud Ressources Server Tests
===================================

.. image:: https://travis-ci.org/schul-cloud/schul_cloud_ressources_server_tests.svg?branch=master
   :target: https://travis-ci.org/schul-cloud/schul_cloud_ressources_server_tests
   :alt: Build Status

.. image:: https://badge.fury.io/py/schul-cloud-ressources-server-tests.svg
   :target: https://pypi.python.org/pypi/schul-cloud-ressources-server-tests
   :alt: Python Package Index

This repository contains

- a server to test scrapers against
- tests to test the server

Installation
------------

Using `pip`, you can install all dependencies like this:

.. code:: shell

    pip install schul_cloud_ressources_server_tests

When you are done, you can import the package.

.. code:: Python

    import schul_cloud_ressources_server_tests

Usage
-----

This section describes how to use the server and the tests.

Server
~~~~~~

You can find the API_ definition.
The server serves according to the API_.
It verifies the input and output for correctness.

To start the server, run

.. code:: shell

    python3 -m schul_cloud_ressources_server_tests.app

The server should appear at http://localhost:8080/v1.

Tests
~~~~~

You always test against the running server.
**Tests may delete everyting you can reach.**
If you test the running server, make sure to authenticate in a way that does not destroy the data you want to keep.

.. code:: shell

    pytest --pyargs schul_cloud_ressources_server_tests.test --url=http://localhost:8080/v1/

`http://localhost:8080/v1/` is the default url.

Steps for Implementation
~~~~~~~~~~~~~~~~~~~~~~~~

If you want to implement your serverm you can follow the TDD steps to implement
one test after the other.

.. code:: shell

    pytest --pyargs schul_cloud_ressources_server_tests.test -m step1
    pytest --pyargs schul_cloud_ressources_server_tests.test -m step2
    pytest --pyargs schul_cloud_ressources_server_tests.test -m step3
    ...

- `step1` runs the first test  
- `step2` runs the first and the second test  
- `step3` runs the first, second and third test  
- ...

You can run  a single test with

.. code:: shell

    pytest --pyargs schul_cloud_ressources_server_tests.test -m step3only


TODO
----

- generate a docker container for the server
- generate a docker container for the tests
- document how to embed the tests and the server in 

  - a crawler
  - travis build script of arbitrary language
- create example crawler with tests




.. _API: https://github.com/schul-cloud/ressources-api-v1
