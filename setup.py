# coding: utf-8

"""
Schul-Cloud Ressources API Server Tests
"""


import sys
import os
from setuptools import setup, find_packages

NAME = "schul_cloud_resources_server_tests"
VERSION = "1.0"
if os.environ.get("TRAVIS_BUILD_NUMBER"):
    # same as in ../generate_python_client.sh
    VERSION += "." + os.environ.get("TRAVIS_BUILD_NUMBER")
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

HERE = os.path.dirname(__file__) or "."

REQUIRES = [line.strip() for line in open(os.path.join(HERE, "requirements.txt")).readlines() if line.strip()]

setup(
    name=NAME,
    version=VERSION,
    description="Schul-Cloud Content API",
    author_email="",
    url="https://github.com/schul-cloud/schul_cloud_ressources_server_tests",
    keywords=["Swagger", "Schul-Cloud Content API", "Server Tests"],
    install_requires=REQUIRES,
    packages=find_packages(),
    include_package_data=True,
    long_description=open(os.path.join(HERE, "README.rst")).read()
)

