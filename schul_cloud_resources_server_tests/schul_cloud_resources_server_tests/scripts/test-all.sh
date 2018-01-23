#!/bin/bash

pytest --version
pytest schul_cloud_resources_server_tests/tests             \
       --basic=valid1@schul-cloud.org:123abc                \
       --basic=valid2@schul-cloud.org:supersecure           \
       --apikey=valid1@schul-cloud.org:abcdefghijklmn       \
       --noauth=true "$@"
