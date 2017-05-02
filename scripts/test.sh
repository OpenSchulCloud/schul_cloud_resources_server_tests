#!/bin/bash

pytest --pyargs schul_cloud_ressources_server_tests     \
       --basic=valid1@schul-cloud.org:123abc            \
       --basic=valid2@schul-cloud.org:supersecure       \
       --apikey=valid1@schul-cloud.org:abcdefghijklmn   \
       --noauth=true "$@"
