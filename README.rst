Schul-Cloud Resources Server Tests
==================================

.. image:: https://travis-ci.org/schul-cloud/schul_cloud_resources_server_tests.svg?branch=master
   :target: https://travis-ci.org/schul-cloud/schul_cloud_resources_server_tests
   :alt: Build Status

.. image:: https://badge.fury.io/py/schul-cloud-resources-server-tests.svg
   :target: https://pypi.python.org/pypi/schul-cloud-resources-server-tests
   :alt: Python Package Index

.. image:: https://img.shields.io/docker/build/schulcloud/schul_cloud_resources_server_tests.svg
   :target: https://hub.docker.com/r/schulcloud/schul_cloud_resources_server_tests/builds/
   :alt: Dockerhub Automated Build Status

.. image:: http://firsttimers.quelltext.eu/repository/schul-cloud/schul_cloud_resources_server_tests.svg
   :target: http://firsttimers.quelltext.eu/repository/schul-cloud/schul_cloud_resources_server_tests.html
   :alt: First Timers

This repository contains

- a server to test scrapers against
- tests to test the server

The package works under Python 2 and 3.

You can view the live docker instance at http://scrst.quelltext.eu/

Installation
------------

Using ``pip``, you can install all dependencies like this:

.. code:: shell

    pip install --user schul_cloud_resources_server_tests

When you are done, you can import the package.

.. code:: Python

    import schul_cloud_resources_server_tests
    
Installation for Development
----------------------------

If you want to work on the module, you need to install it differently.
If you set it up for development, you can add new tests and features.

First, you need to have git installed. Then, clone the repository:

.. code:: shell

    git clone https://github.com/schul-cloud/schul_cloud_resources_server_tests.git
    cd schul_cloud_resources_server_tests

If you have ``pip`` installed, you can now install the packages:

.. code:: shell

    pip install --user -r requirements.txt pip-tools==1.6.5

Now, as long as you are in the ``schul_cloud_resources_server_tests`` folder, you can run the commands as mentioned below.
Additionally, you can use git to create pull-requests with your edited code.

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

    python -m schul_cloud_resources_server_tests.app

The server should appear at http://localhost:8080/v1.

Tests
~~~~~

You always test against the running server.
**Tests may delete everyting you can reach.**
If you test the running server, make sure to authenticate in a way that does not destroy the data you want to keep.

.. code:: shell

    python -m schul_cloud_resources_server_tests.tests --url=http://localhost:8080/v1/

http://localhost:8080/v1/ is the default url.

Steps for Implementation
~~~~~~~~~~~~~~~~~~~~~~~~

If you want to implement your server you can follow the TDD steps to implement
one test after the other.

.. code:: shell

    python -m schul_cloud_resources_server_tests.tests -m step1
    python -m schul_cloud_resources_server_tests.tests -m step2
    python -m schul_cloud_resources_server_tests.tests -m step3
    ...

- `step1` runs the first test  
- `step2` runs the first and the second test  
- `step3` runs the first, second and third test  
- ...

You can run  a single test with

.. code:: shell

    python -m schul_cloud_resources_server_tests.tests -m step3only

Test Authentication
~~~~~~~~~~~~~~~~~~~

The test server supports api key authentication and basic authentication.
If you test authentication over the internet.
Use https to protect the secrets.
Thus, an example test call to your api could look like this:

.. code:: Python

    python -m schul_cloud_resources_server_tests.tests  \
           --url=https://url.to/your/server               \
           --noauth=false --basic=username:password

If you have an api key, you can test that the server works.

.. code:: Python

    python -m schul_cloud_resources_server_tests.tests   \
           --url=http://url.to/your/server                \
           --noauth=false --apikey=apikey

By default the test server accepts authentication with several credentials

- no authentication
- basic:

  - user ``valid1@schul-cloud.org`` password ``123abc``
  - user ``valid2@schul-cloud.org`` password ``supersecure``
- api key: ``abcdefghijklmn`` for the user ``valid1@schul-cloud.org``.
  The client does not send the user name to the server.

To test these, you can add the ``--basic`` and ``--apikey``
parameters several times to the tests.
The ``--noauth=true`` parameter is default.
If the api only accepts authenticated requests, set ``--noauth=false``.

.. code:: Python

    python -m schul_cloud_resources_server_tests.tests    \
           --basic=valid1@schul-cloud.org:123abc           \
           --basic=valid2@schul-cloud.org:supersecure      \
           --apikey=valid1@schul-cloud.org:abcdefghijklmn  \
           --noauth=true

All tests are run with the different authentication options.
If we have several ways to authenticate, the tests test if the user sees the other users' data.

It is assumed, that adding ``invalid`` to the password,
user name and api key will make it invalid.
Tests use the invalid credentials to test the server behavior in rejected cases.

Example Travis Configuration
----------------------------

If you want to implement a crawler or server, you can use Travis-CI to test
it.
An example travis configuration can be found in the `test-example
<https://github.com/schul-cloud/schul_cloud_resources_server_tests/blob/test-example/.travis.yml>`__ branch.
You can view the `output
<https://travis-ci.org/schul-cloud/schul_cloud_resources_server_tests/branches>`__
The configuration is generic.
It will run under any other language you configure.

Usage in Crawler
----------------

The `url-crawler <https://github.com/schul-cloud/url-crawler#readme>`__ uses the test server to test synchronization.

Use the server in pytest
------------------------

You can use the sever in Python tests.
There are fixtures available that start and stop the server.

.. code:: Python

    from schul_cloud_resources_server_tests.tests.fixtures import *

    def test_pytest(resources_server):
        """pytest using the server"""

The following attributes are available:

- ``resources_server.url`` The url of the server.
- ``resources_server.api`` A ``schul_cloud_resources_api_v1.ResourcesApi`` object connected to the server.
- ``resources_server.get_resources()`` A function to return a list of resources on the server.

For more information, see the module ``schul_cloud_resources_server_tests.tests.fixtures``.
You can add support for more test frameworks.

Docker
------

You can build the this image with the following docker command:

.. code:: shell

    docker build -t schulcloud/schul_cloud_resources_server_tests .

Or you can pull the docker container and run it.

.. code:: shell

    docker run schulcloud/schul_cloud_resources_server_tests

This starts the server at the port 8080 as in the examples above.

Docker-Compose
~~~~~~~~~~~~~~

There is a ``docker-compose.yml`` file, so you can use the ``docker-compose`` command.
The server will be available at http://localhost:80/v1
It uses a memory limit of 60MB.

------------------------------

You can edit this document `on Github
<https://github.com/schul-cloud/schul_cloud_resources_server_tests/blob/master/README.rst#readme>`__
and check it with `this editor <http://rst.ninjs.org/>`__.

.. _API: https://github.com/schul-cloud/resources-api-v1
