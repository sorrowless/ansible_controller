#!/bin/sh

ansible-galaxy install -r get-non-vendor-roles.yml -p ./roles/
ansible-galaxy install -r get-vendor-roles.yml -p ./roles/
